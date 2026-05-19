#!/usr/bin/env bash
# 用途：将本仓库的 Skills 逐个链接到本机 agent 配置目录
# 用法：link-skills.sh [--all|--claude|--codex|--agents|--unlink|--skill <name>|--help]

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
SKILLS_DIRS=(
  "$REPO_ROOT/02-agent-skills/skills"
  "$REPO_ROOT/05-custom-skills/skills"
)

ALL_AGENTS=(claude codex agents)

agent_target_dir() {
  local agent="$1"
  case "$agent" in
    claude) echo "$HOME/.claude/skills" ;;
    codex)  echo "$HOME/.codex/skills" ;;
    agents) echo "$HOME/.agents/skills" ;;
    *)      echo "" ;;
  esac
}

# --- 参数 ---
SELECTED_AGENTS=()
UNLINK=false
FILTER_SKILL=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --all              Link to all agents (default)
  --claude           Link to ~/.claude/skills
  --codex            Link to ~/.codex/skills
  --agents           Link to ~/.agents/skills
  --unlink           Remove symlinks instead of creating them
  --skill <name>     Only process this skill (default: all skills)
  --help             Show this help message

Each skill is linked individually, preserving existing content (e.g.,
~/.codex/skills/.system/) in the target directory.
EOF
}

add_agent() {
  local agent="$1"
  local existing

  for existing in "${SELECTED_AGENTS[@]+"${SELECTED_AGENTS[@]}"}"; do
    if [ "$existing" = "$agent" ]; then
      return 0
    fi
  done

  SELECTED_AGENTS+=("$agent")
}

# --- 解析 SKILL.md frontmatter 的 agents 字段 ---
parse_agents_field() {
  local skill_md="$1"

  python3 -c "
import sys, re

with open(sys.argv[1]) as f:
    content = f.read()

if not content.startswith('---'):
    print('ALL')
    sys.exit(0)

end = content.find('---', 3)
if end == -1:
    print('ALL')
    sys.exit(0)

fm_text = content[3:end]

# agents: []
if re.search(r'^agents:\s*\[\s*\]\s*$', fm_text, re.MULTILINE):
    sys.exit(0)

match = re.search(r'^agents:\s*$', fm_text, re.MULTILINE)
if not match:
    print('ALL')
    sys.exit(0)

pos = match.end()
lines = fm_text[pos:].split('\n')
for line in lines:
    stripped = line.strip()
    if stripped.startswith('- '):
        print(stripped[2:].strip())
    elif stripped == '' or stripped.startswith('#'):
        continue
    else:
        break
" "$skill_md" 2>/dev/null
}

# --- 判断 Skill 是否应链接到某个 agent ---
should_link() {
  local skill_md="$1"
  local agent="$2"
  local agents_output

  agents_output="$(parse_agents_field "$skill_md")"

  if [ -z "$agents_output" ]; then
    return 1
  fi

  if echo "$agents_output" | grep -qx "ALL"; then
    return 0
  fi

  echo "$agents_output" | grep -qx "$agent"
}

# --- 链接单个 Skill 到单个 agent ---
link_skill() {
  local skill_name="$1"
  local agent="$2"
  local source="$3"
  local target_dir
  target_dir="$(agent_target_dir "$agent")"
  local target="$target_dir/$skill_name"

  mkdir -p "$target_dir"

  if [ -L "$target" ]; then
    local current_target
    current_target="$(readlink "$target")"
    local source_real
    source_real="$(cd "$source" && pwd -P)"

    if [ "$(cd "$(dirname "$target")" && cd "$current_target" && pwd -P)" = "$source_real" ] 2>/dev/null; then
      echo -e "${GREEN}  ✓ $agent: already linked${NC}"
      return 0
    fi

    rm "$target"
  elif [ -e "$target" ]; then
    local backup="${target}.backup-$(date +%Y%m%d-%H%M%S)"
    echo -e "${YELLOW}  ⚠ $agent: backing up existing $target -> $backup${NC}"
    mv "$target" "$backup"
  fi

  ln -s "$source" "$target"
  echo -e "${GREEN}  ✓ $agent: linked${NC}"
}

# --- 移除单个 Skill 的 symlink ---
unlink_skill() {
  local skill_name="$1"
  local agent="$2"
  local target_dir
  target_dir="$(agent_target_dir "$agent")"
  local target="$target_dir/$skill_name"

  if [ -L "$target" ]; then
    rm "$target"
    echo -e "${GREEN}  ✓ $agent: unlinked${NC}"
  elif [ -e "$target" ]; then
    echo -e "${YELLOW}  ⚠ $agent: $target exists but is not a symlink, skipping${NC}"
  else
    echo -e "${CYAN}  · $agent: no link found${NC}"
  fi
}

# --- 处理单个 Skill ---
process_skill() {
  local skill_dir="$1"
  local skill_name
  skill_name="$(basename "$skill_dir")"
  local skill_md="$skill_dir/SKILL.md"

  if [ ! -f "$skill_md" ]; then
    echo -e "${YELLOW}Skip $skill_name: no SKILL.md${NC}"
    return
  fi

  echo -e "${CYAN}$skill_name${NC}"

  local agent
  for agent in "${SELECTED_AGENTS[@]}"; do
    if $UNLINK; then
      unlink_skill "$skill_name" "$agent"
    else
      if should_link "$skill_md" "$agent"; then
        link_skill "$skill_name" "$agent" "$skill_dir"
      else
        echo -e "  · $agent: skipped (not in agents list)"
      fi
    fi
  done
}

# --- 解析命令行参数 ---
while [ "$#" -gt 0 ]; do
  case "$1" in
    --all)
      for a in "${ALL_AGENTS[@]}"; do add_agent "$a"; done
      ;;
    --claude)  add_agent claude ;;
    --codex)   add_agent codex ;;
    --agents)  add_agent agents ;;
    --unlink)  UNLINK=true ;;
    --skill)   shift; FILTER_SKILL="$1" ;;
    --help|-h) usage; exit 0 ;;
    *) echo -e "${RED}Error: unknown option: $1${NC}" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

# 默认链接所有 agent
if [ "${#SELECTED_AGENTS[@]}" -eq 0 ]; then
  for a in "${ALL_AGENTS[@]}"; do add_agent "$a"; done
fi

# --- 检查 skills 目录 ---
for skills_dir in "${SKILLS_DIRS[@]}"; do
  if [ ! -d "$skills_dir" ]; then
    echo -e "${YELLOW}Warning: skills directory not found: $skills_dir${NC}"
  fi
done

# --- 主循环 ---
if [ -n "$FILTER_SKILL" ]; then
  found=false
  for skills_dir in "${SKILLS_DIRS[@]}"; do
    if [ -d "$skills_dir/$FILTER_SKILL" ]; then
      process_skill "$skills_dir/$FILTER_SKILL"
      found=true
      break
    fi
  done
  if ! $found; then
    echo -e "${RED}Error: skill not found: $FILTER_SKILL${NC}" >&2
    exit 1
  fi
else
  for skills_dir in "${SKILLS_DIRS[@]}"; do
    [ -d "$skills_dir" ] || continue
    for skill_dir in "$skills_dir"/*/; do
      [ -d "$skill_dir" ] || continue
      process_skill "$skill_dir"
    done
  done
fi

echo -e "${GREEN}Done.${NC}"
