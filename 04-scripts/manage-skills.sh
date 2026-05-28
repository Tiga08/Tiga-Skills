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
  import [--description "说明"] <source-path>
                           Import a skill from an external path
  remove <skill-name>      Remove an imported skill
  list                     List all imported skills
  status                   Check for upstream changes
  update [--description "说明"] <skill-name>
                           Update an imported skill from source

Examples:
  $(basename "$0") import /path/to/khazix-skills/skills/my-skill
  $(basename "$0") import --description "将 Markdown 转为 HTML" /path/to/skills/md-to-html
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

extract_english_description() {
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

update_skill_index() {
  local skill_name="$1"
  local description="$2"

  if [ ! -f "$SKILL_INDEX" ]; then
    return 0
  fi

  if [ -z "$description" ]; then
    description="(no description)"
  fi

  python3 -c "
import json, sys, re

index_file = sys.argv[1]
skill_name = sys.argv[2]
description = sys.argv[3].replace('|', r'\|')
registry_file = sys.argv[4]

# --- 从 registry 解析上游仓库链接 ---
upstream_col = ''
try:
    with open(registry_file) as f:
        reg = json.load(f)
    for s in reg.get('skills', []):
        if s['name'] == skill_name:
            repo_id = s.get('repoId', '')
            if repo_id:
                url = reg.get('repos', {}).get(repo_id, {}).get('upstreamUrl', '')
                # git@github.com:Org/Repo.git -> [Org/Repo](https://github.com/Org/Repo)
                m = re.match(r'git@github\.com:(.+?)(?:\.git)?$', url)
                if m:
                    slug = m.group(1)
                    upstream_col = f'[{slug}](https://github.com/{slug})'
            break
except Exception:
    pass

new_entry = (skill_name, description, upstream_col)

# --- 读取索引文件 ---
with open(index_file) as f:
    lines = f.readlines()

# --- 找到 Agent Skills 区域，收集现有行 ---
section_start = None
header_end = None
section_end = None
existing = {}  # name -> (description, upstream)

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == '## Agent Skills':
        section_start = i
    elif section_start is not None and header_end is None:
        if stripped.startswith('|--'):
            header_end = i + 1
    elif header_end is not None and section_end is None:
        if stripped.startswith('## ') or stripped == '':
            section_end = i
            break
        if stripped.startswith('|'):
            parts = [p.strip() for p in stripped.split('|')]
            # parts: ['', name, desc, upstream?, '']
            if len(parts) >= 4:
                ename = parts[1]
                edesc = parts[2]
                eupstream = parts[3] if len(parts) >= 5 else ''
                existing[ename] = (edesc, eupstream)

if section_start is None or header_end is None:
    sys.exit(0)

if section_end is None:
    section_end = len(lines)

# --- 加入/更新条目 ---
existing[new_entry[0]] = (new_entry[1], new_entry[2])

# --- 按名称排序，生成 3 列表格 ---
sorted_names = sorted(existing.keys())
new_rows = []
for name in sorted_names:
    desc, upstream = existing[name]
    new_rows.append(f'| {name} | {desc} | {upstream} |\n')

# --- 重写 Agent Skills 区域 ---
header = [
    '| 名称 | 说明 | 上游仓库 |\n',
    '|------|------|----------|\n',
]
result = lines[:section_start + 1]  # 包含 ## Agent Skills
result.append('\n')
result.extend(header)
result.extend(new_rows)
result.extend(lines[section_end:])

with open(index_file, 'w') as f:
    f.writelines(result)
" "$SKILL_INDEX" "$skill_name" "$description" "$REGISTRY"

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
  local user_description=""
  local source_path=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --description)
        user_description="${2:-}"
        shift 2
        ;;
      *)
        source_path="$1"
        shift
        ;;
    esac
  done

  if [ -z "$source_path" ]; then
    echo -e "${RED}Error: source path is required${NC}" >&2
    echo "Usage: $(basename "$0") import [--description \"说明\"] <source-path>" >&2
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

  local en_desc
  en_desc="$(extract_english_description "$source_path/SKILL.md")"

  local description="$user_description"
  if [ -z "$description" ]; then
    if [ -t 0 ]; then
      echo -e "${CYAN}English description: ${en_desc:-（无）}${NC}"
      printf "请输入中文说明（回车跳过使用英文）: "
      read -r description
    fi
  fi
  if [ -z "$description" ]; then
    description="$en_desc"
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
entry = {
    'name': sys.argv[2],
    'source': sys.argv[3],
    'importedAt': sys.argv[4],
    'updatedAt': sys.argv[4],
    'sourceHash': sys.argv[5],
    'description': sys.argv[6]
}
source = sys.argv[3]
for rid, rinfo in data.get('repos', {}).items():
    if source.startswith(rinfo.get('localPath', '') + '/'):
        entry['repoId'] = rid
        break
data['skills'].append(entry)
with open(sys.argv[1], 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" "$REGISTRY" "$skill_name" "$source_path" "$now" "$source_hash" "$description"

  update_skill_index "$skill_name" "$description"

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
  local user_description=""
  local skill_name=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --description)
        user_description="${2:-}"
        shift 2
        ;;
      *)
        skill_name="$1"
        shift
        ;;
    esac
  done

  if [ -z "$skill_name" ]; then
    echo -e "${RED}Error: skill name is required${NC}" >&2
    echo "Usage: $(basename "$0") update [--description \"说明\"] <skill-name>" >&2
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

  local description="$user_description"
  if [ -z "$description" ]; then
    description="$(echo "$record" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('description',''))")"
  fi
  if [ -z "$description" ]; then
    description="$(extract_english_description "$source_path/SKILL.md")"
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
        s['description'] = sys.argv[5]
        break
with open(sys.argv[1], 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" "$REGISTRY" "$skill_name" "$now" "$source_hash" "$description"

  update_skill_index "$skill_name" "$description"

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
