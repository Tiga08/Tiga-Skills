#!/bin/bash
# update-readme.sh
# 扫描 skills/ 目录，从每个 SKILL.md 的 frontmatter 提取 name 和 description，
# 按插件分组重新生成 README.md

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$REPO_ROOT/scripts/update-readme.py" "$REPO_ROOT"
