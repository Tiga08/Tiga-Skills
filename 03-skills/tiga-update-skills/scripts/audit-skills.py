#!/usr/bin/env python3
"""对本地 Agent Skills 执行无第三方依赖的结构审查。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
CORE_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
CLAUDE_FIELDS = {
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "background",
    "hooks",
    "paths",
    "shell",
}
TOP_LEVEL_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$")
VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: Path
    message: str


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("当前目录不在 Git 仓库中")
    return Path(result.stdout.strip()).resolve()


def scalar_value(raw: str, following_lines: list[str]) -> str:
    value = raw.strip()
    if value in {"|", "|-", "|+", ">", ">-", ">+"}:
        parts = [line.strip() for line in following_lines if line.strip()]
        separator = "\n" if value.startswith("|") else " "
        return separator.join(parts)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("缺少以 --- 开始的 YAML frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("YAML frontmatter 缺少结束标记 ---") from error

    frontmatter_lines = lines[1:closing]
    fields: dict[str, str] = {}
    keys: list[str] = []
    index = 0
    while index < len(frontmatter_lines):
        line = frontmatter_lines[index]
        match = TOP_LEVEL_KEY.match(line)
        if not match:
            index += 1
            continue
        key, raw_value = match.groups()
        keys.append(key)
        following: list[str] = []
        cursor = index + 1
        while cursor < len(frontmatter_lines):
            candidate = frontmatter_lines[cursor]
            if TOP_LEVEL_KEY.match(candidate):
                break
            if candidate.startswith((" ", "\t")):
                following.append(candidate)
            cursor += 1
        fields[key] = scalar_value(raw_value or "", following)
        index = cursor
    return fields, keys, text


def quoted_yaml_string(raw: str) -> str | None:
    value = raw.strip()
    if len(value) < 2 or value[0] != value[-1] or value[0] not in {'"', "'"}:
        return None
    return value[1:-1]


def audit_openai_yaml(path: Path, skill_name: str) -> list[Finding]:
    if not path.is_file():
        return [
            Finding(
                "INFO",
                "CODEX-METADATA",
                path,
                "未提供可选的 agents/openai.yaml",
            )
        ]

    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        match = re.match(
            r"^\s{2}(display_name|short_description|default_prompt):\s*(.+)$",
            line,
        )
        if match:
            values[match.group(1)] = match.group(2)

    findings: list[Finding] = []
    for key in ("display_name", "short_description", "default_prompt"):
        if key not in values:
            findings.append(
                Finding("WARNING", "CODEX-METADATA", path, f"缺少 interface.{key}")
            )
            continue
        parsed = quoted_yaml_string(values[key])
        if parsed is None:
            findings.append(
                Finding(
                    "ERROR",
                    "CODEX-METADATA",
                    path,
                    f"interface.{key} 必须是带引号的字符串",
                )
            )
            continue
        if key == "short_description" and not 25 <= len(parsed) <= 64:
            findings.append(
                Finding(
                    "WARNING",
                    "CODEX-METADATA",
                    path,
                    "interface.short_description 应为 25–64 个字符",
                )
            )
        if key == "default_prompt" and f"${skill_name}" not in parsed:
            findings.append(
                Finding(
                    "ERROR",
                    "CODEX-METADATA",
                    path,
                    f"interface.default_prompt 必须显式包含 ${skill_name}",
                )
            )

    policy_lines = [
        line
        for line in lines
        if re.match(r"^\s{2}allow_implicit_invocation:\s*", line)
    ]
    if policy_lines:
        value = policy_lines[-1].split(":", 1)[1].strip()
        if value not in {"true", "false"}:
            findings.append(
                Finding(
                    "ERROR",
                    "CODEX-POLICY",
                    path,
                    "policy.allow_implicit_invocation 必须是 true 或 false",
                )
            )
    return findings


def audit_skill(display_path: Path, repo_root: Path) -> list[Finding]:
    skill_file = display_path / "SKILL.md"
    findings: list[Finding] = []
    try:
        resolved = display_path.resolve(strict=True)
    except FileNotFoundError:
        return [
            Finding("ERROR", "MISSING", display_path, "Skill 路径或符号链接目标不存在")
        ]

    if display_path.is_symlink():
        findings.append(
            Finding("INFO", "SYMLINK", display_path, f"解析到 {resolved}")
        )
        if repo_root not in (resolved, *resolved.parents):
            findings.append(
                Finding(
                    "WARNING",
                    "EXTERNAL",
                    display_path,
                    "符号链接目标位于当前仓库之外，只应审查，不应默认更新",
                )
            )

    if not skill_file.is_file():
        return findings + [
            Finding("ERROR", "MISSING", skill_file, "缺少 SKILL.md")
        ]

    try:
        fields, keys, text = parse_frontmatter(skill_file)
    except (OSError, UnicodeError, ValueError) as error:
        return findings + [
            Finding("ERROR", "FRONTMATTER", skill_file, str(error))
        ]

    for required in ("name", "description"):
        if not fields.get(required, "").strip():
            findings.append(
                Finding(
                    "ERROR",
                    "CORE",
                    skill_file,
                    f"缺少非空的 {required} 字段",
                )
            )

    for key, count in Counter(keys).items():
        if count > 1:
            findings.append(
                Finding(
                    "ERROR",
                    "FRONTMATTER",
                    skill_file,
                    f"frontmatter 顶层字段重复：{key}",
                )
            )

    name = fields.get("name", "").strip()
    if name:
        if not VALID_NAME.fullmatch(name) or len(name) > 64:
            findings.append(
                Finding(
                    "ERROR",
                    "CORE",
                    skill_file,
                    "name 必须为不超过 64 字符的 kebab-case，且不能含连续连字符",
                )
            )
        if name != display_path.name:
            findings.append(
                Finding(
                    "ERROR",
                    "CORE",
                    skill_file,
                    f"name={name!r} 与目录名 {display_path.name!r} 不一致",
                )
            )

    description = fields.get("description", "").strip()
    if len(description) > 1024:
        findings.append(
            Finding(
                "ERROR",
                "CORE",
                skill_file,
                "description 超过 Agent Skills 的 1024 字符上限",
            )
        )

    compatibility = fields.get("compatibility", "").strip()
    if len(compatibility) > 500:
        findings.append(
            Finding(
                "ERROR",
                "CORE",
                skill_file,
                "compatibility 超过 Agent Skills 的 500 字符上限",
            )
        )

    for key in dict.fromkeys(keys):
        if key in CORE_FIELDS:
            continue
        if key in CLAUDE_FIELDS:
            findings.append(
                Finding(
                    "INFO",
                    "CLAUDE-EXTENSION",
                    skill_file,
                    f"{key} 是 Claude Code 扩展，应与可移植核心分层判断",
                )
            )
        else:
            findings.append(
                Finding(
                    "ERROR",
                    "UNKNOWN",
                    skill_file,
                    f"未识别的 frontmatter 顶层字段：{key}",
                )
            )

    if len(text.splitlines()) > 500:
        findings.append(
            Finding(
                "WARNING",
                "BLOAT",
                skill_file,
                "SKILL.md 超过 500 行，应评估是否拆分到 references/",
            )
        )

    findings.extend(audit_openai_yaml(display_path / "agents" / "openai.yaml", name))
    return findings


def resolve_targets(repo_root: Path, target: str | None) -> list[Path]:
    skills_root = repo_root / ".agents" / "skills"
    if target is None:
        if not skills_root.is_dir():
            raise ValueError(f"默认 Skill 目录不存在：{skills_root}")
        return sorted(
            (
                path
                for path in skills_root.iterdir()
                if path.is_symlink()
                or (path.is_dir() and (path / "SKILL.md").is_file())
            ),
            key=lambda path: path.name,
        )

    candidate = Path(target).expanduser()
    if candidate.is_absolute() or "/" in target or target.startswith("."):
        path = candidate if candidate.is_absolute() else repo_root / candidate
    else:
        path = skills_root / target
        if not path.exists() and target == SKILL_ROOT.name:
            path = SKILL_ROOT
    if path.name == "SKILL.md":
        path = path.parent
    if not path.exists():
        raise ValueError(f"找不到 Skill：{target}")
    return [path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="审查 `.agents/skills` 中的全部 Skill 或一个指定 Skill。",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Skill 名称、目录路径或 SKILL.md 路径",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = repository_root()
        targets = resolve_targets(repo_root, args.target)
    except (RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    total_errors = 0
    total_warnings = 0
    total_infos = 0
    for target in targets:
        findings = audit_skill(target, repo_root)
        print(f"== {target} ==")
        if not findings:
            print("PASS")
        for finding in findings:
            print(
                f"[{finding.level}][{finding.code}] "
                f"{finding.path}: {finding.message}"
            )
            total_errors += finding.level == "ERROR"
            total_warnings += finding.level == "WARNING"
            total_infos += finding.level == "INFO"

    print(
        "SUMMARY "
        f"skills={len(targets)} errors={total_errors} "
        f"warnings={total_warnings} infos={total_infos}"
    )
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
