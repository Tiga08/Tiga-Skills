#!/usr/bin/env python3
"""Tiga-Skills 管理脚本。

以仓库根目录的 skills.toml 为唯一权威来源：
  install                    按清单创建、修复、清理链接，并刷新 README 技能清单
  check                      只读检查清单、skill 目录、链接与 README，有问题时退出码为 1
  update [name...]           预览外部 skill 的上游变化
  update [name...] --apply   采纳上游最新版本并更新 skills.lock.json

只依赖 Python 3.11 标准库与 git。
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"
MANIFEST = ROOT / "skills.toml"
LOCK = ROOT / "skills.lock.json"
STATE = ROOT / ".tiga" / "installed.json"
CACHE = ROOT / ".tiga" / "cache"
README = ROOT / "README.md"
BEGIN, END = "<!-- BEGIN SKILL LIST -->", "<!-- END SKILL LIST -->"
# Claude Code 与 Codex 的用户级 skill 目录
USER_DIRS = (".claude/skills", ".agents/skills")
# 项目里 .claude/skills 指向的位置，Codex 直接读取 .agents/skills
BRIDGE = "../.agents/skills"
LICENSE_RE = re.compile(r"^(licen[cs]e|copying)(\.\w+)?$", re.I)
ESCAPE_RE = re.compile(r"\]\((\.\./[^)\s]*)\)")
# 比较本地副本与上游版本时忽略的系统与运行时产物
IGNORED = {".DS_Store", "__pycache__"}


# ---------- 基础 ----------

def git(cwd, *args, binary=False):
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=not binary)
    if result.returncode:
        stderr = result.stderr if not binary else result.stderr.decode(errors="replace")
        raise SystemExit(f"git {' '.join(args)} 失败：\n{stderr.strip()}")
    return result.stdout if binary else result.stdout.strip()


def load_manifest():
    with MANIFEST.open("rb") as f:
        return tomllib.load(f).get("skills", {})


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def report(problems, ok=None):
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    if ok:
        print(ok)


# ---------- 链接 ----------

def project_root(target):
    # 解析真实路径，保证相对链接按磁盘上的实际层级计算
    return Path(target.removeprefix("project:")).expanduser().resolve()


def project_dirs(manifest):
    return {
        project_root(t)
        for spec in manifest.values()
        for t in spec.get("targets", [])
        if t.startswith("project:")
    }


def desired_links(manifest):
    """返回 {链接路径: 链接内容}。用户级写绝对路径，项目级写相对路径。"""
    links = {}
    for name, spec in manifest.items():
        source = SKILLS / name
        for target in spec.get("targets", []):
            if target == "user":
                for d in USER_DIRS:
                    links[Path.home() / d / name] = str(source)
            elif target.startswith("project:"):
                link = project_root(target) / ".agents" / "skills" / name
                links[link] = os.path.relpath(source, link.parent)
            else:
                raise SystemExit(f"skills.toml 中 {name} 的目标无法识别：{target}")
    return links


def is_managed(link):
    """只有指向本仓库 skills/ 的链接才归脚本管理，其余条目一律不动。"""
    if not link.is_symlink():
        return False
    target = Path(os.path.normpath(os.path.join(link.parent, os.readlink(link))))
    return target.is_relative_to(SKILLS)


def candidate_links(manifest):
    """可能需要清理的受管理链接：上次安装记录的，加上用户级与各项目目录里现有的。"""
    paths = {Path(p) for p in load_json(STATE, [])}
    dirs = [Path.home() / d for d in USER_DIRS] + [p / ".agents" / "skills" for p in project_dirs(manifest)]
    for d in dirs:
        if d.is_dir():
            paths.update(d.iterdir())
    return {p for p in paths if is_managed(p)}


def install(_args):
    manifest = load_manifest()
    desired = desired_links(manifest)
    changes, errors = [], []
    for link in sorted(candidate_links(manifest) - desired.keys()):
        link.unlink()
        changes.append(f"删除 {link}")
    for link, target in sorted(desired.items()):
        if link.is_symlink() and os.readlink(link) == target:
            continue
        if link.is_symlink() and (is_managed(link) or not link.exists()):
            # 指向本仓库但内容不对，或已经失效的链接，可以安全替换
            link.unlink()
        elif os.path.lexists(link):
            kind = f"指向 {os.readlink(link)} 的链接" if link.is_symlink() else "真实文件或目录"
            errors.append(f"{link} 已是{kind}，未改动")
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        changes.append(f"链接 {link} -> {target}")
    for project in sorted(project_dirs(manifest)):
        bridge = project / ".claude" / "skills"
        if not os.path.lexists(bridge):
            bridge.parent.mkdir(parents=True, exist_ok=True)
            bridge.symlink_to(BRIDGE)
            changes.append(f"链接 {bridge} -> {BRIDGE}")
    installed = [str(link) for link, target in desired.items() if link.is_symlink() and os.readlink(link) == target]
    save_json(STATE, sorted(installed))
    readme = render_readme(manifest)
    if README.read_text(encoding="utf-8") != readme:
        README.write_text(readme, encoding="utf-8")
        changes.append("刷新 README.md 技能清单")
    print("\n".join(changes) or "无变化")
    report(errors)


# ---------- README ----------

def render_readme(manifest):
    lock = load_json(LOCK, {})
    rows = ["| 名称 | 来源 | 安装位置 | 描述 |", "| --- | --- | --- | --- |"]
    for name in sorted(manifest):
        spec = manifest[name]
        upstream = spec.get("upstream")
        if upstream:
            repo = "/".join(upstream["repo"].removesuffix(".git").rstrip("/").split("/")[-2:])
            source = f"`{repo}` @ `{lock.get(name, '未引入')[:7]}`"
        else:
            source = "自写"
        where = "、".join("用户级" if t == "user" else f"项目 `{t.removeprefix('project:')}`" for t in spec.get("targets", []))
        rows.append(f"| {name} | {source} | {where} | {spec.get('zh', '')} |")
    text = README.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(f"README.md 缺少 {BEGIN} / {END} 标记")
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    return text[:start] + "\n" + "\n".join(rows) + "\n" + text[end:]


# ---------- check ----------

def check_skill(name, spec, lock):
    directory = SKILLS / name
    skill_md = directory / "SKILL.md"
    if not skill_md.is_file():
        return [f"skills/{name} 缺少 SKILL.md"]
    problems = []
    match = re.match(r"---\n(.*?)\n---\n", skill_md.read_text(encoding="utf-8"), re.S)
    fields = dict(re.findall(r"^([\w-]+):[ \t]*(.*)$", match.group(1), re.M)) if match else {}
    actual = fields.get("name", "").strip("\"'")
    if actual != name:
        problems.append(f"skills/{name}/SKILL.md 的 name 是 {actual!r}，应为 {name!r}")
    if not fields.get("description"):
        problems.append(f"skills/{name}/SKILL.md 缺少 description")
    if not spec.get("zh"):
        problems.append(f"skills.toml 中的 {name} 缺少 zh 描述")
    if "upstream" in spec and name not in lock:
        problems.append(f"外部 skill {name} 尚未引入（运行 update {name} --apply）")
    root = directory.resolve()
    for path in sorted(directory.rglob("*")):
        rel = path.relative_to(SKILLS)
        if path.is_symlink():
            if not path.resolve().is_relative_to(root):
                problems.append(f"skills/{rel} 链接到 skill 目录之外")
        elif path.suffix == ".md" and path.is_file():
            for ref in ESCAPE_RE.findall(path.read_text(encoding="utf-8")):
                if not (path.parent / ref).resolve().is_relative_to(root):
                    problems.append(f"skills/{rel} 引用了 skill 目录之外的 {ref}")
    return problems


def check(_args):
    manifest = load_manifest()
    lock = load_json(LOCK, {})
    problems = []
    dirs = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    problems += [f"skills/{n} 未在 skills.toml 登记" for n in sorted(dirs - manifest.keys())]
    problems += [f"skills.toml 中的 {n} 没有对应目录" for n in sorted(manifest.keys() - dirs)]
    for name in sorted(manifest.keys() & dirs):
        problems += check_skill(name, manifest[name], lock)
    external = {n for n, s in manifest.items() if "upstream" in s}
    problems += [f"skills.lock.json 中的 {n} 不是外部 skill" for n in sorted(lock.keys() - external)]
    desired = desired_links(manifest)
    for link, target in sorted(desired.items()):
        if not os.path.lexists(link):
            problems.append(f"缺失链接 {link}")
        elif not link.is_symlink() or os.readlink(link) != target:
            problems.append(f"链接不符 {link}（应指向 {target}）")
        elif not link.exists():
            problems.append(f"链接失效 {link}")
    problems += [f"多余链接 {l}（运行 install 清理）" for l in sorted(candidate_links(manifest) - desired.keys())]
    for project in sorted(project_dirs(manifest)):
        bridge = project / ".claude" / "skills"
        if not (bridge.is_symlink() and os.readlink(bridge) == BRIDGE):
            problems.append(f"{bridge} 不是指向 {BRIDGE} 的链接，Claude Code 读不到该项目的 skill")
    if README.read_text(encoding="utf-8") != render_readme(manifest):
        problems.append("README.md 技能清单已过期（运行 install 刷新）")
    report(problems, ok="全部正常")


# ---------- update ----------

def fetch(repo):
    """把上游仓库拉到 .tiga/cache/：只取提交与目录结构，文件内容按需下载。"""
    cache = CACHE / re.sub(r"[^\w.-]+", "-", repo.removesuffix(".git")).strip("-")
    if cache.exists():
        git(cache, "fetch", "--quiet", "origin")
    else:
        CACHE.mkdir(parents=True, exist_ok=True)
        git(CACHE, "clone", "--quiet", "--filter=blob:none", "--no-checkout", repo, str(cache))
    return cache


def materialize(cache, commit, path, dest):
    """导出上游某个 commit 的 skill 目录；目录内没有许可证时补上仓库根目录的许可证。"""
    data = git(cache, "archive", "--format=tar", commit, "--", path, binary=True)
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(tmp, filter="data")
        if not (Path(tmp) / path).is_dir():
            raise SystemExit(f"上游 {commit[:12]} 中没有目录 {path}")
        shutil.copytree(Path(tmp) / path, dest, symlinks=True)
    if not any(LICENSE_RE.match(p.name) for p in dest.iterdir()):
        names = git(cache, "ls-tree", "--name-only", commit).splitlines()
        license_name = next((n for n in names if LICENSE_RE.match(n)), None)
        if license_name:
            (dest / license_name).write_bytes(git(cache, "show", f"{commit}:{license_name}", binary=True))
        else:
            print(f"警告：上游 {path} 没有许可证文件", file=sys.stderr)
    return dest


def snapshot(directory):
    """目录内容的可比较快照：相对路径 -> 文件内容或链接目标。"""
    return {
        str(p.relative_to(directory)): os.readlink(p) if p.is_symlink() else p.read_bytes()
        for p in directory.rglob("*")
        if (p.is_symlink() or p.is_file()) and not IGNORED & set(p.relative_to(directory).parts)
    }


def vendor(cache, commit, path, dest):
    with tempfile.TemporaryDirectory() as tmp:
        fresh = materialize(cache, commit, path, Path(tmp) / dest.name)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(fresh, dest, symlinks=True)


def update(args):
    manifest = load_manifest()
    external = {n: s["upstream"] for n, s in manifest.items() if "upstream" in s}
    names = args.names or sorted(external)
    unknown = [n for n in names if n not in external]
    if unknown:
        raise SystemExit(f"不是外部 skill：{', '.join(unknown)}")
    lock = load_json(LOCK, {})
    problems = []
    for name in names:
        repo, path = external[name]["repo"], external[name]["path"]
        cache = fetch(repo)
        latest = git(cache, "rev-parse", "origin/HEAD")
        locked = lock.get(name)
        dest = SKILLS / name
        if not locked:
            print(f"== {name}：尚未引入，上游最新 {latest[:12]}")
            if args.apply:
                vendor(cache, latest, path, dest)
                lock[name] = latest
                print(f"已引入 {name} @ {latest[:12]}")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            pristine = materialize(cache, locked, path, Path(tmp) / name)
            modified = not dest.exists() or snapshot(dest) != snapshot(pristine)
        status = "本地有修改" if modified else "本地未改动"
        if locked == latest:
            print(f"== {name}：已是最新 {latest[:12]}（{status}）")
            continue
        print(f"== {name}：{locked[:12]} -> {latest[:12]}（{status}）")
        print(git(cache, "diff", locked, latest, "--", path) or "（上游有新提交，但该 skill 目录没有变化）")
        if not args.apply:
            continue
        if modified:
            problems.append(f"{name} 本地有修改，未采纳；请按 tiga-skills 的合并流程处理")
            continue
        vendor(cache, latest, path, dest)
        lock[name] = latest
        print(f"已采纳 {name} @ {latest[:12]}")
    if args.apply:
        save_json(LOCK, lock)
    report(problems)


def main():
    parser = argparse.ArgumentParser(description="Tiga-Skills 管理脚本")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install", help="按清单创建、修复、清理链接并刷新 README")
    sub.add_parser("check", help="只读检查清单、skill 目录、链接与 README")
    p = sub.add_parser("update", help="预览或采纳外部 skill 的上游更新")
    p.add_argument("names", nargs="*", help="只处理这些 skill，默认全部外部 skill")
    p.add_argument("--apply", action="store_true", help="采纳上游最新版本")
    args = parser.parse_args()
    {"install": install, "check": check, "update": update}[args.command](args)


if __name__ == "__main__":
    main()
