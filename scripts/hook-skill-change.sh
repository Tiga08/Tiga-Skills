#!/bin/bash
# hook-skill-change.sh
# 由 Claude Code PostToolUse hook 调用，判断是否为 skill 相关操作，若是则更新 README.md

REPO_ROOT="/Users/bruce/Projects/Skills"

EVENT=$(cat)

FILE_PATH=$(echo "$EVENT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

CMD=$(echo "$EVENT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [[ "$FILE_PATH" == */skills/* ]] || [[ "$CMD" == *skills/* ]]; then
  bash "$REPO_ROOT/scripts/update-readme.sh"
fi
