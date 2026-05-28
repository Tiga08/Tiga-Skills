#!/usr/bin/env bash
# 用途：同步自定义 Skills 到能力索引
# 用法：sync-index.sh [--dry-run|--help]

set -euo pipefail

# --- 颜色 ---
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- 路径 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CUSTOM_SKILLS_DIR="$REPO_ROOT/05-custom-skills/skills"
SKILL_INDEX="$REPO_ROOT/00-skill-index/README.md"

DRY_RUN=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run|--help]

Scan 05-custom-skills/skills/ and update the "自定义 Skills" section
in 00-skill-index/README.md.

Options:
  --dry-run   Print the table rows without modifying the file
  --help      Show this help message
EOF
}

extract_description() {
  local skill_md="$1"
  python3 -c "
import sys, re
with open(sys.argv[1]) as f:
    text = f.read()
desc = ''
m = re.search(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
if m:
    dm = re.search(r'^description:\s*(.+)', m.group(1), re.MULTILINE)
    if dm:
        val = dm.group(1).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('\"', \"'\"):
            val = val[1:-1]
        desc = val
print(desc)
" "$skill_md"
}

# --- 解析参数 ---
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# --- 构建表格行（按名称排序） ---
TABLE_ROWS=""
if [ -d "$CUSTOM_SKILLS_DIR" ]; then
  UNSORTED_ROWS=""
  for skill_dir in "$CUSTOM_SKILLS_DIR"/*/; do
    [ -d "$skill_dir" ] || continue
    skill_md="$skill_dir/SKILL.md"
    [ -f "$skill_md" ] || continue

    skill_name="$(basename "$skill_dir")"
    description="$(extract_description "$skill_md")"
    if [ -z "$description" ]; then
      description="(no description)"
    fi
    description="$(echo "$description" | sed 's/|/\\|/g')"
    UNSORTED_ROWS="${UNSORTED_ROWS}| ${skill_name} | ${description} |
"
  done
  TABLE_ROWS="$(printf '%s' "$UNSORTED_ROWS" | sort)"
  if [ -n "$TABLE_ROWS" ]; then
    TABLE_ROWS="${TABLE_ROWS}
"
  fi
fi

if [ -z "$TABLE_ROWS" ]; then
  TABLE_ROWS="| — | 暂无 |
"
fi

# --- dry-run 模式 ---
if [ "$DRY_RUN" = true ]; then
  echo "Will write the following rows to '自定义 Skills' section:"
  echo ""
  printf "%s" "$TABLE_ROWS"
  exit 0
fi

# --- 替换章节内容 ---
if [ ! -f "$SKILL_INDEX" ]; then
  echo "Error: $SKILL_INDEX not found" >&2
  exit 1
fi

python3 -c "
import sys

index_file = sys.argv[1]
new_rows = sys.argv[2]

with open(index_file) as f:
    lines = f.readlines()

section_heading = '## 自定义 Skills'
in_section = False
found_separator = False
result = []
skipping = False

for line in lines:
    stripped = line.rstrip('\n')

    if stripped == section_heading:
        in_section = True
        result.append(line)
        continue

    if in_section and not found_separator:
        result.append(line)
        if stripped.startswith('|--'):
            found_separator = True
            skipping = True
            for row in new_rows.strip('\n').split('\n'):
                result.append(row + '\n')
        continue

    if skipping:
        if stripped.startswith('## ') or stripped == '':
            skipping = False
            if stripped == '':
                result.append(line)
                continue
            result.append('\n')
            result.append(line)
            continue
        continue

    result.append(line)

with open(index_file, 'w') as f:
    f.writelines(result)
" "$SKILL_INDEX" "$TABLE_ROWS"

echo -e "${GREEN}Updated${NC} ${SKILL_INDEX#$REPO_ROOT/}"
