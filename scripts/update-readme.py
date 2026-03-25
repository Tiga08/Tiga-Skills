#!/usr/bin/env python3
"""
update-readme.py
扫描 skills/ 目录，按插件分组重新生成 README.md。
用法：python3 update-readme.py <repo_root>
"""
import os
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> dict:
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip().strip('"\'')
    return fm


def main(repo_root: str) -> None:
    skills_dir = Path(repo_root) / "skills"
    readme_path = Path(repo_root) / "README.md"

    # 收集所有 skills，按插件分组
    plugins: dict[str, list[tuple[str, str]]] = {}
    if skills_dir.exists():
        for plugin_dir in sorted(skills_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            plugin_name = plugin_dir.name
            skill_list: list[tuple[str, str]] = []
            for skill_dir in sorted(plugin_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    fm = parse_frontmatter(content)
                    skill_name = fm.get("name", skill_dir.name)
                    description = fm.get("description", "")
                    skill_list.append((skill_name, description))
                except Exception:
                    skill_list.append((skill_dir.name, ""))
            if skill_list:
                plugins[plugin_name] = skill_list

    total_plugins = len(plugins)
    total_skills = sum(len(v) for v in plugins.values())

    lines = [
        "# tiga-skills",
        "",
        "> 个人 Claude Code Skills 备份仓库",
        ">",
        "> **注意：本文件由脚本自动生成，请勿手动编辑。**",
        "",
        "## 统计",
        "",
        f"- 插件总数：{total_plugins}",
        f"- Skills 总数：{total_skills}",
        "",
    ]

    if plugins:
        lines += ["## Skills 列表", ""]
        for plugin_name, skill_list in plugins.items():
            lines += [
                f"### {plugin_name}",
                "",
                "| Skill | 描述 |",
                "|-------|------|",
            ]
            for skill_name, desc in skill_list:
                lines.append(f"| {skill_name} | {desc} |")
            lines.append("")
    else:
        lines += [
            "## Skills 列表",
            "",
            "_暂无 skills，请将 skill 目录放入对应插件子目录中。_",
            "",
        ]

    lines += [
        "## 目录结构",
        "",
        "```",
        "skills/",
        "  {plugin-name}/",
        "    {skill-name}/",
        "      SKILL.md",
        "```",
        "",
        "## 安装与使用",
        "",
        "1. 克隆仓库：`git clone <repo-url>`",
        "2. 将对应 skill 目录复制到：",
        "   `~/.claude/plugins/cache/{publisher}/{plugin}/{version}/skills/`",
        "3. 在 `~/.claude/settings.json` 中启用对应插件",
    ]

    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"README.md updated: {total_plugins} plugins, {total_skills} skills")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: update-readme.py <repo_root>")
        sys.exit(1)
    main(sys.argv[1])
