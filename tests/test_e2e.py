"""skills.py 端到端测试。

每个用例都在临时目录里搭一套独立的仓库、HOME、项目和上游 git 仓库，
通过子进程调用真实脚本，不触碰本机配置，也不访问网络。

覆盖的失败方式：
1. 用户级链接没有同时装到 Claude Code 与 Codex 的目录
2. 重复执行 install 产生多余改动
3. install 改动或删除了不归它管理的条目（synced/、别人的链接、普通文件）
4. 从清单移除 skill 或整个项目后，旧链接残留
5. 项目级链接不是相对路径，或缺少 .claude/skills 桥接链接
6. 目标位置已有真实目录或别人的有效链接时被覆盖
7. 失效的旧链接没有被修复
8. check 漏报缺失链接、frontmatter 错误、未登记目录、README 过期、越界引用
9. 首次引入外部 skill 时没有锁定 commit 或丢失上游 LICENSE
10. 预览更新时修改了文件；采纳更新后锁定 commit 未前进
11. 本地改过的外部 skill 被上游版本直接覆盖
12. 一次采纳多个 skill 时中途失败，已替换的副本与锁定 commit 错位
13. requires 中的 skill 未登记或没有覆盖依赖方的安装位置时，check 没有报出
"""

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "tiga-skills" / "scripts" / "skills.py"

README = textwrap.dedent("""\
    # 测试仓库

    <!-- BEGIN SKILL LIST -->
    <!-- END SKILL LIST -->
    """)


def git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd, check=True, capture_output=True,
    )


def write_skill(directory, name, body="正文"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {name} 的描述\n---\n\n{body}\n", encoding="utf-8"
    )


class SkillsE2E(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.repo = self.tmp / "repo"
        script_dir = self.repo / "skills" / "tiga-skills" / "scripts"
        script_dir.mkdir(parents=True)
        shutil.copy(SCRIPT, script_dir / "skills.py")
        write_skill(self.repo / "skills" / "tiga-skills", "tiga-skills")
        write_skill(self.repo / "skills" / "alpha", "alpha")
        (self.repo / "README.md").write_text(README, encoding="utf-8")
        self.project = self.home / "Projects" / "demo"
        self.project.mkdir(parents=True)

    # ---------- 辅助 ----------

    def manifest(self, text):
        (self.repo / "skills.toml").write_text(textwrap.dedent(text), encoding="utf-8")

    def cli(self, *args, ok=True):
        result = subprocess.run(
            ["python3", str(self.repo / "skills" / "tiga-skills" / "scripts" / "skills.py"), *args],
            env={**os.environ, "HOME": str(self.home)}, capture_output=True, text=True,
        )
        output = result.stdout + result.stderr
        if ok:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        return output

    def make_upstream(self):
        """创建一个上游仓库：skills/beta 加根目录 LICENSE。"""
        up = self.tmp / "upstream"
        write_skill(up / "skills" / "beta", "beta", body="第一版")
        (up / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        git(up, "init", "-q", "-b", "main")
        git(up, "add", ".")
        git(up, "commit", "-q", "-m", "v1")
        return up

    def upstream_commit(self, up, body):
        write_skill(up / "skills" / "beta", "beta", body=body)
        git(up, "commit", "-q", "-am", body)

    def head(self, up):
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=up, capture_output=True, text=True).stdout.strip()

    def beta_manifest(self, up):
        self.manifest(f"""\
            [skills.tiga-skills]
            zh = "管理"
            targets = ["user"]

            [skills.alpha]
            zh = "阿尔法"
            targets = ["user"]

            [skills.beta]
            zh = "贝塔"
            targets = ["user"]
            upstream = {{ repo = "file://{up}", path = "skills/beta" }}
            """)

    def basic_manifest(self, alpha_targets='["user"]'):
        self.manifest(f"""\
            [skills.tiga-skills]
            zh = "管理"
            targets = ["user"]

            [skills.alpha]
            zh = "阿尔法"
            targets = {alpha_targets}
            """)

    # ---------- install ----------

    def test_install_links_user_skills_for_both_agents(self):
        self.basic_manifest()
        self.cli("install")
        for agent_dir in (".claude/skills", ".agents/skills"):
            for name in ("tiga-skills", "alpha"):
                link = self.home / agent_dir / name
                self.assertTrue(link.is_symlink(), link)
                self.assertEqual(link.resolve(), (self.repo / "skills" / name).resolve())
        readme = (self.repo / "README.md").read_text(encoding="utf-8")
        self.assertIn("| alpha | 自写 | 用户级 | 阿尔法 |", readme)

    def test_install_is_idempotent(self):
        self.basic_manifest()
        self.cli("install")
        self.assertIn("无变化", self.cli("install"))

    def test_install_leaves_foreign_entries(self):
        claude = self.home / ".claude" / "skills"
        (claude / "synced" / "x").mkdir(parents=True)
        other = self.tmp / "other-skill"
        write_skill(other, "other")
        (claude / "other").symlink_to(other)
        (claude / "notes.txt").write_text("keep", encoding="utf-8")
        self.basic_manifest()
        self.cli("install")
        self.assertTrue((claude / "synced" / "x").is_dir())
        self.assertEqual((claude / "other").resolve(), other.resolve())
        self.assertEqual((claude / "notes.txt").read_text(encoding="utf-8"), "keep")

    def test_install_removes_links_dropped_from_manifest(self):
        self.basic_manifest(alpha_targets=f'["user", "project:{self.project}"]')
        self.cli("install")
        project_link = self.project / ".agents" / "skills" / "alpha"
        self.assertTrue(project_link.is_symlink())
        # 整个 alpha 条目连同项目目标一起删掉，仍应清理项目里的链接
        shutil.rmtree(self.repo / "skills" / "alpha")
        self.manifest("""\
            [skills.tiga-skills]
            zh = "管理"
            targets = ["user"]
            """)
        self.cli("install")
        self.assertFalse(os.path.lexists(self.home / ".claude" / "skills" / "alpha"))
        self.assertFalse(os.path.lexists(self.home / ".agents" / "skills" / "alpha"))
        self.assertFalse(os.path.lexists(project_link))
        self.assertTrue((self.home / ".claude" / "skills" / "tiga-skills").is_symlink())

    def test_install_project_target(self):
        self.basic_manifest(alpha_targets=f'["project:~/Projects/demo"]')
        self.cli("install")
        link = self.project / ".agents" / "skills" / "alpha"
        self.assertFalse(os.path.isabs(os.readlink(link)), os.readlink(link))
        self.assertEqual(link.resolve(), (self.repo / "skills" / "alpha").resolve())
        bridge = self.project / ".claude" / "skills"
        self.assertEqual(os.readlink(bridge), "../.agents/skills")
        self.assertFalse(os.path.lexists(self.project / ".codex"))
        self.assertFalse(os.path.lexists(self.home / ".claude" / "skills" / "alpha"))

    def test_install_refuses_to_overwrite_real_dir_or_foreign_link(self):
        real = self.home / ".claude" / "skills" / "alpha"
        write_skill(real, "alpha", body="手写的")
        other = self.tmp / "other-alpha"
        write_skill(other, "alpha")
        codex = self.home / ".agents" / "skills"
        codex.mkdir(parents=True)
        (codex / "alpha").symlink_to(other)
        self.basic_manifest()
        output = self.cli("install", ok=False)
        self.assertIn("未改动", output)
        self.assertIn("手写的", (real / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((codex / "alpha").resolve(), other.resolve())
        # 其余条目照常安装
        self.assertTrue((self.home / ".claude" / "skills" / "tiga-skills").is_symlink())

    def test_install_repairs_broken_link(self):
        claude = self.home / ".claude" / "skills"
        claude.mkdir(parents=True)
        (claude / "alpha").symlink_to(self.tmp / "old-location" / "alpha")
        self.basic_manifest()
        self.cli("install")
        self.assertEqual((claude / "alpha").resolve(), (self.repo / "skills" / "alpha").resolve())

    # ---------- check ----------

    def test_check_reports_clean_state(self):
        self.basic_manifest()
        self.cli("install")
        self.assertIn("全部正常", self.cli("check"))

    def test_check_reports_problems(self):
        self.basic_manifest()
        self.cli("install")
        (self.home / ".agents" / "skills" / "alpha").unlink()
        write_skill(self.repo / "skills" / "tiga-skills", "wrong-name")
        write_skill(self.repo / "skills" / "orphan", "orphan")
        write_skill(self.repo / "skills" / "alpha", "alpha", body="见 [共享说明](../../docs/x.md)")
        readme = self.repo / "README.md"
        readme.write_text(README, encoding="utf-8")
        output = self.cli("check", ok=False)
        for expected in ("缺失", "wrong-name", "orphan", "README", "../../docs/x.md"):
            self.assertIn(expected, output)

    def test_check_reports_unmet_requires(self):
        write_skill(self.repo / "skills" / "dep", "dep")
        self.manifest(f"""\
            [skills.tiga-skills]
            zh = "管理"
            targets = ["user"]

            [skills.alpha]
            zh = "阿尔法"
            targets = ["user"]
            requires = ["dep", "missing"]

            [skills.dep]
            zh = "依赖"
            targets = ["project:{self.home / 'Projects' / 'other'}"]
            """)
        self.cli("install")
        output = self.cli("check", ok=False)
        self.assertIn("alpha 依赖的 missing 不在", output)
        self.assertIn("alpha 依赖的 dep 没有装到 user", output)

    def test_check_accepts_requires_covered_by_user_or_same_project(self):
        write_skill(self.repo / "skills" / "dep", "dep")
        self.manifest(f"""\
            [skills.tiga-skills]
            zh = "管理"
            targets = ["user"]

            [skills.alpha]
            zh = "阿尔法"
            targets = ["project:~/Projects/demo"]
            requires = ["dep", "tiga-skills"]

            [skills.dep]
            zh = "依赖"
            targets = ["project:{self.project}"]
            """)
        self.cli("install")
        self.assertIn("全部正常", self.cli("check"))

    # ---------- update ----------

    def test_update_vendors_new_upstream_skill(self):
        up = self.make_upstream()
        self.beta_manifest(up)
        preview = self.cli("update", "beta")
        self.assertIn("尚未引入", preview)
        self.assertFalse((self.repo / "skills" / "beta").exists())
        self.cli("update", "beta", "--apply")
        beta = self.repo / "skills" / "beta"
        self.assertIn("第一版", (beta / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((beta / "LICENSE").read_text(encoding="utf-8"), "MIT License\n")
        lock = json.loads((self.repo / "skills.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["beta"], self.head(up))
        self.cli("install")
        self.assertIn("全部正常", self.cli("check"))

    def test_update_applies_upstream_change_when_unmodified(self):
        up = self.make_upstream()
        self.beta_manifest(up)
        self.cli("update", "beta", "--apply")
        self.upstream_commit(up, "第二版")
        preview = self.cli("update", "beta")
        self.assertIn("+第二版", preview)
        skill_md = self.repo / "skills" / "beta" / "SKILL.md"
        self.assertIn("第一版", skill_md.read_text(encoding="utf-8"))
        self.cli("update", "beta", "--apply")
        self.assertIn("第二版", skill_md.read_text(encoding="utf-8"))
        lock = json.loads((self.repo / "skills.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["beta"], self.head(up))
        self.assertIn("已是最新", self.cli("update", "beta"))

    def test_update_refuses_when_locally_modified(self):
        up = self.make_upstream()
        self.beta_manifest(up)
        self.cli("update", "beta", "--apply")
        locked = json.loads((self.repo / "skills.lock.json").read_text(encoding="utf-8"))["beta"]
        write_skill(self.repo / "skills" / "beta", "beta", body="本地改过")
        self.upstream_commit(up, "第二版")
        self.assertIn("本地有修改", self.cli("update", "beta"))
        self.cli("update", "beta", "--apply", ok=False)
        skill_md = self.repo / "skills" / "beta" / "SKILL.md"
        self.assertIn("本地改过", skill_md.read_text(encoding="utf-8"))
        lock = json.loads((self.repo / "skills.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["beta"], locked)

    def test_update_keeps_lock_in_sync_when_later_skill_fails(self):
        up = self.make_upstream()
        self.beta_manifest(up)
        # gamma 排在 beta 之后，上游没有它的目录，采纳时必然失败
        with (self.repo / "skills.toml").open("a", encoding="utf-8") as f:
            f.write(f'\n[skills.gamma]\nzh = "伽马"\ntargets = ["user"]\n'
                    f'upstream = {{ repo = "file://{up}", path = "skills/gamma" }}\n')
        self.cli("update", "--apply", ok=False)
        self.assertIn("第一版", (self.repo / "skills" / "beta" / "SKILL.md").read_text(encoding="utf-8"))
        lock = json.loads((self.repo / "skills.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["beta"], self.head(up))
        self.assertIn("本地未改动", self.cli("update", "beta"))


if __name__ == "__main__":
    unittest.main()
