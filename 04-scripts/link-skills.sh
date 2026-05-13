#!/usr/bin/env bash
# 用途：将本仓库的 02-agent-skills 软链接到 ~/.claude/skills 和 ~/.codex/skills
# 用法：link-skills.sh

set -euo pipefail

# --- 颜色 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# --- 推导仓库根目录 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/02-agent-skills"

if [ ! -d "$SKILLS_SRC" ]; then
  echo -e "${RED}Error: source skills directory does not exist: $SKILLS_SRC${NC}"
  exit 1
fi

# --- 备份已有路径 ---
backup_if_exists() {
  local target="$1"

  if [ -L "$target" ]; then
    echo -e "${YELLOW}Remove existing symlink: $target${NC}"
    rm "$target"
  elif [ -e "$target" ]; then
    local backup="${target}.backup.$(date +%Y%m%d-%H%M%S)"
    echo -e "${YELLOW}Backup existing path: $target -> $backup${NC}"
    mv "$target" "$backup"
  fi
}

# --- 创建目标父目录 ---
mkdir -p ~/.claude ~/.codex

# --- 创建软链接 ---
TARGETS=(~/.claude/skills ~/.codex/skills)

for target in "${TARGETS[@]}"; do
  backup_if_exists "$target"
  ln -s "$SKILLS_SRC" "$target"
  echo -e "${GREEN}Linked: $target -> $SKILLS_SRC${NC}"
done

echo -e "${GREEN}Done.${NC}"
