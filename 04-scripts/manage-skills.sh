#!/usr/bin/env bash
# 用途：管理外部 Skill 的导入、移除、查询和更新
# 用法：manage-skills.sh <import|remove|list|status|update> [参数]

set -euo pipefail

# --- 颜色 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- 路径 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/02-agent-skills/skills"
REGISTRY="$REPO_ROOT/02-agent-skills/skill-registry.json"
SKILL_INDEX="$REPO_ROOT/00-skill-index/README.md"

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [options]

Commands:
  import <source-path>     Import a skill from an external path
  remove <skill-name>      Remove an imported skill
  list                     List all imported skills
  status                   Check for upstream changes
  update <skill-name>      Update an imported skill from source

Examples:
  $(basename "$0") import /path/to/khazix-skills/skills/my-skill
  $(basename "$0") remove my-skill
  $(basename "$0") list
  $(basename "$0") status
  $(basename "$0") update my-skill
EOF
}

ensure_registry() {
  if [ ! -f "$REGISTRY" ]; then
    printf '{\n  "version": 2,\n  "skills": []\n}\n' > "$REGISTRY"
  fi
}

compute_hash() {
  local dir="$1"
  find "$dir" -type f | sort | xargs shasum 2>/dev/null | shasum | cut -c1-8
}

find_in_registry() {
  local name="$1"
  python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
entries = [s for s in data['skills'] if s['name'] == sys.argv[2]]
if entries:
    print(json.dumps(entries[0]))
else:
    sys.exit(1)
" "$REGISTRY" "$name"
}

update_skill_index() {
  local skill_name="$1"
  local skill_md="$SKILLS_DIR/$skill_name/SKILL.md"

  if [ ! -f "$SKILL_INDEX" ] || [ ! -f "$skill_md" ]; then
    return 0
  fi

  if grep -q "| $skill_name |" "$SKILL_INDEX" 2>/dev/null; then
    return 0
  fi

  local description
  description="$(python3 -c "
import sys, re

with open(sys.argv[1]) as f:
    text = f.read()

desc = ''
m = re.search(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
if m:
    fm = m.group(1)
    # Match description: possibly followed by quoted or unquoted value
    dm = re.search(r'^description:\s*(.+)', fm, re.MULTILINE)
    if dm:
        val = dm.group(1).strip()
        # Strip matching quotes (single or double)
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('\"', \"'\"):
            val = val[1:-1]
        desc = val

# Truncate: first sentence, max 80 chars
if '. ' in desc:
    desc = desc[:desc.index('. ') + 1]
if len(desc) > 80:
    desc = desc[:77] + '…'

# Escape pipe for Markdown tables
desc = desc.replace('|', r'\|')

print(desc)
" "$skill_md")"

  if [ -z "$description" ]; then
    description="(no description)"
  fi

  local index_line="| $skill_name | $description | \`02-agent-skills/skills/$skill_name/\` |"

  python3 -c "
import sys
index_file = sys.argv[1]
new_line = sys.argv[2]
with open(index_file) as f:
    lines = f.readlines()
insert_pos = None
in_agent_skills = False
for i, line in enumerate(lines):
    if line.strip() == '## Agent Skills':
        in_agent_skills = True
    elif in_agent_skills and line.startswith('## '):
        insert_pos = i
        break
    elif in_agent_skills and line.startswith('|') and not line.startswith('| 名称') and not line.startswith('|--'):
        insert_pos = i + 1
if insert_pos is None:
    insert_pos = len(lines)
lines.insert(insert_pos, new_line + '\n')
with open(index_file, 'w') as f:
    f.writelines(lines)
" "$SKILL_INDEX" "$index_line"

  echo -e "${CYAN}Updated skill index: $skill_name${NC}"
}

remove_from_skill_index() {
  local skill_name="$1"

  if [ ! -f "$SKILL_INDEX" ]; then
    return 0
  fi

  if ! grep -q "| $skill_name |" "$SKILL_INDEX" 2>/dev/null; then
    return 0
  fi

  python3 -c "
import sys
with open(sys.argv[1]) as f:
    lines = f.readlines()
with open(sys.argv[1], 'w') as f:
    for line in lines:
        if not line.strip().startswith('| ' + sys.argv[2] + ' |'):
            f.write(line)
" "$SKILL_INDEX" "$skill_name"

  echo -e "${CYAN}Removed from skill index: $skill_name${NC}"
}

# --- import ---
cmd_import() {
  local source_path="${1:-}"

  if [ -z "$source_path" ]; then
    echo -e "${RED}Error: source path is required${NC}" >&2
    echo "Usage: $(basename "$0") import <source-path>" >&2
    exit 1
  fi

  source_path="$(cd "$source_path" && pwd)" 2>/dev/null || {
    echo -e "${RED}Error: source path does not exist: $source_path${NC}" >&2
    exit 1
  }

  if [ ! -f "$source_path/SKILL.md" ]; then
    echo -e "${RED}Error: SKILL.md not found in $source_path${NC}" >&2
    exit 1
  fi

  local skill_name
  skill_name="$(basename "$source_path")"
  local target_dir="$SKILLS_DIR/$skill_name"

  ensure_registry
  mkdir -p "$SKILLS_DIR"

  if [ -d "$target_dir" ]; then
    if find_in_registry "$skill_name" >/dev/null 2>&1; then
      local current_hash
      current_hash="$(compute_hash "$source_path")"
      local local_hash
      local_hash="$(compute_hash "$target_dir")"

      if [ "$current_hash" = "$local_hash" ]; then
        echo -e "${GREEN}Already up-to-date: $skill_name${NC}"
        return 0
      fi

      echo -e "${YELLOW}Skill already imported. Use 'update' to refresh.${NC}"
      return 1
    else
      echo -e "${RED}Error: $skill_name already exists but is not an imported skill.${NC}" >&2
      exit 1
    fi
  fi

  cp -R "$source_path" "$target_dir"

  local source_hash
  source_hash="$(compute_hash "$source_path")"
  local now
  now="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"

  python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
if data.get('version', 1) == 1:
    data['version'] = 2
    for s in data.get('skills', []):
        s.pop('agent', None)
data['skills'].append({
    'name': sys.argv[2],
    'source': sys.argv[3],
    'importedAt': sys.argv[4],
    'updatedAt': sys.argv[4],
    'sourceHash': sys.argv[5]
})
with open(sys.argv[1], 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" "$REGISTRY" "$skill_name" "$source_path" "$now" "$source_hash"

  update_skill_index "$skill_name"

  echo -e "${GREEN}Imported: $skill_name -> $target_dir${NC}"
}

# --- remove ---
cmd_remove() {
  local skill_name="${1:-}"

  if [ -z "$skill_name" ]; then
    echo -e "${RED}Error: skill name is required${NC}" >&2
    echo "Usage: $(basename "$0") remove <skill-name>" >&2
    exit 1
  fi

  ensure_registry

  if ! find_in_registry "$skill_name" >/dev/null 2>&1; then
    echo -e "${RED}Error: $skill_name is not an imported skill${NC}" >&2
    exit 1
  fi

  local target_dir="$SKILLS_DIR/$skill_name"

  if [ -d "$target_dir" ]; then
    rm -rf "$target_dir"
  fi

  python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
data['skills'] = [s for s in data['skills'] if s['name'] != sys.argv[2]]
with open(sys.argv[1], 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" "$REGISTRY" "$skill_name"

  remove_from_skill_index "$skill_name"

  echo -e "${GREEN}Removed: $skill_name${NC}"
}

# --- list ---
cmd_list() {
  ensure_registry

  python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
skills = data['skills']
if not skills:
    print('No imported skills.')
else:
    for s in skills:
        print(f\"  {s['name']:30s} {s['source']}\")
" "$REGISTRY"
}

# --- status ---
cmd_status() {
  ensure_registry

  python3 -c "
import json, subprocess, os, sys

with open(sys.argv[1]) as f:
    data = json.load(f)

skills = data['skills']
if not skills:
    print('No imported skills.')
    sys.exit(0)

for s in skills:
    source = s['source']
    name = s['name']
    old_hash = s.get('sourceHash', '')

    if not os.path.isdir(source):
        print(f'  \033[0;33m{name:30s} source missing: {source}\033[0m')
        continue

    result = subprocess.run(
        ['bash', '-c', f\"find '{source}' -type f | sort | xargs shasum 2>/dev/null | shasum\"],
        capture_output=True, text=True
    )
    new_hash = result.stdout.strip()[:8] if result.returncode == 0 else '?'

    if new_hash == old_hash:
        print(f'  \033[0;32m{name:30s} up-to-date\033[0m')
    else:
        print(f'  \033[0;33m{name:30s} changed (local: {old_hash}, source: {new_hash})\033[0m')
" "$REGISTRY"
}

# --- update ---
cmd_update() {
  local skill_name="${1:-}"

  if [ -z "$skill_name" ]; then
    echo -e "${RED}Error: skill name is required${NC}" >&2
    echo "Usage: $(basename "$0") update <skill-name>" >&2
    exit 1
  fi

  ensure_registry

  local record
  record="$(find_in_registry "$skill_name")" || {
    echo -e "${RED}Error: $skill_name is not an imported skill${NC}" >&2
    exit 1
  }

  local source_path
  source_path="$(echo "$record" | python3 -c "import json,sys; print(json.load(sys.stdin)['source'])")"

  if [ ! -d "$source_path" ]; then
    echo -e "${RED}Error: source path no longer exists: $source_path${NC}" >&2
    exit 1
  fi

  if [ ! -f "$source_path/SKILL.md" ]; then
    echo -e "${RED}Error: SKILL.md not found in $source_path${NC}" >&2
    exit 1
  fi

  local target_dir="$SKILLS_DIR/$skill_name"

  local source_hash
  source_hash="$(compute_hash "$source_path")"
  local local_hash
  local_hash="$(compute_hash "$target_dir" 2>/dev/null || echo "none")"

  if [ "$source_hash" = "$local_hash" ]; then
    echo -e "${GREEN}Already up-to-date: $skill_name${NC}"
    return 0
  fi

  rm -rf "$target_dir"
  cp -R "$source_path" "$target_dir"

  local now
  now="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"

  python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for s in data['skills']:
    if s['name'] == sys.argv[2]:
        s['updatedAt'] = sys.argv[3]
        s['sourceHash'] = sys.argv[4]
        break
with open(sys.argv[1], 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" "$REGISTRY" "$skill_name" "$now" "$source_hash"

  update_skill_index "$skill_name"

  echo -e "${GREEN}Updated: $skill_name${NC}"
}

# --- 主入口 ---
if [ "$#" -eq 0 ]; then
  usage
  exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
  import) cmd_import "$@" ;;
  remove) cmd_remove "$@" ;;
  list)   cmd_list "$@" ;;
  status) cmd_status "$@" ;;
  update) cmd_update "$@" ;;
  --help|-h) usage ;;
  *)
    echo -e "${RED}Error: unknown command: $COMMAND${NC}" >&2
    usage >&2
    exit 1
    ;;
esac
