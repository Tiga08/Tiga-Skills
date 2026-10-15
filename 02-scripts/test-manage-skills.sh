#!/usr/bin/env bash
# manage-skills.sh 端到端测试
# 在临时 HOME 中搭建最小仓库副本，验证 setup / add / remove / check / update-readme 的行为
# 用法: ./02-scripts/test-manage-skills.sh   （不触碰真实 HOME 与本仓库的 03-skills/）

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_SCRIPT="$SCRIPT_DIR/manage-skills.sh"

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

pass=0
fail=0

# 断言失败时附上最近一次 run 的输出，便于定位
assert() {
  local label="$1"
  shift
  if "$@"; then
    echo "  ✓ $label"
    pass=$((pass + 1))
  else
    echo "  ✗ $label"
    sed 's/^/      | /' "$TMP_ROOT/out.log" 2>/dev/null
    fail=$((fail + 1))
  fi
}

is_link_to() { [ -L "$1" ] && [ "$(readlink "$1")" = "$2" ]; }
is_real_dir() { [ -d "$1" ] && [ ! -L "$1" ]; }
absent() { [ ! -e "$1" ] && [ ! -L "$1" ]; }
entry_count_is() { [ "$(ls -A "$SKILLS" | wc -l | tr -d ' ')" = "$1" ]; }
lacks() { ! grep -qF -- "$1" "$2"; }

run() { "$REPO/02-scripts/manage-skills.sh" "$@" > "$TMP_ROOT/out.log" 2>&1 < /dev/null; }
run_fails() { ! run "$@"; }
output_has() { grep -qF -- "$1" "$TMP_ROOT/out.log"; }

# 搭建全新的临时 HOME 与仓库副本，设置 HOME / AGTOOLS / REPO / SKILLS / EXT / CLAUDE_DIR / CODEX_LINK
new_fixture() {
  export HOME="$TMP_ROOT/$1/home"
  AGTOOLS="$HOME/Projects/AG-Tools"
  REPO="$AGTOOLS/tiga-skills"
  SKILLS="$REPO/03-skills"
  EXT="$AGTOOLS/ext/skills/demo-ext"
  CLAUDE_DIR="$HOME/.claude/skills"
  CODEX_LINK="$HOME/.codex/skills/tiga-skills"

  mkdir -p "$REPO/02-scripts" "$SKILLS/demo-custom" "$REPO/.agents/skills/demo-project" "$EXT"
  cp "$SOURCE_SCRIPT" "$REPO/02-scripts/manage-skills.sh"

  local skill
  for skill in "$SKILLS/demo-custom" "$REPO/.agents/skills/demo-project" "$EXT"; do
    printf -- '---\nname: %s\ndescription: 测试技能\n---\n' "$(basename "$skill")" > "$skill/SKILL.md"
  done

  printf '# 测试\n\n<!-- BEGIN SKILL LIST -->\n<!-- END SKILL LIST -->\n' > "$REPO/README.md"
  printf '%s\n' "demo-custom.description=自定义测试" "demo-project.description=项目测试" \
    "demo-ext.description=外部测试" > "$REPO/descriptions-zh.conf"

  printf '# 下游引用\n\n| 上游技能 | 引用方 | 方式 |\n| -------- | ------ | ---- |\n' > "$AGTOOLS/SKILLS-REFS.md"
  ln -s ../SKILLS-REFS.md "$REPO/SKILLS-REFS.md"
  mkdir -p "$REPO/.claude" "$REPO/.codex"
  ln -s ../.agents/skills "$REPO/.claude/skills"
  ln -s ../.agents/skills "$REPO/.codex/skills"
}

echo "场景 1：全新 HOME 执行 setup，重复执行保持幂等"
new_fixture fresh
assert "setup 成功退出" run setup
assert "~/.claude/skills 是真实目录" is_real_dir "$CLAUDE_DIR"
assert "demo-custom 链接指向 03-skills/demo-custom" is_link_to "$CLAUDE_DIR/demo-custom" "$SKILLS/demo-custom"
assert "~/.codex/skills/tiga-skills 指向 03-skills" is_link_to "$CODEX_LINK" "$SKILLS"
assert "check 成功退出" run check
assert "check 输出用户级链接检查" output_has "检查用户级链接"
assert "再次 setup 成功退出" run setup
assert "再次 setup 后链接不变" is_link_to "$CLAUDE_DIR/demo-custom" "$SKILLS/demo-custom"

echo "场景 2：~/.claude/skills 是软链接（旧布局）时不做任何链接"
new_fixture legacy
mkdir -p "$HOME/.claude"
ln -s "$SKILLS" "$CLAUDE_DIR"
assert "setup 退出时提示删除软链接" run setup
assert "setup 输出旧布局提示" output_has "软链接"
assert "旧布局软链接原样保留" is_link_to "$CLAUDE_DIR" "$SKILLS"
assert "add 成功退出" run add "$EXT"
assert "03-skills/ 只新增 demo-ext" entry_count_is 2
assert "check 在旧布局下失败" run_fails check

echo "场景 3：保留 Claude Code 自有内容与无关链接"
new_fixture coexist
mkdir -p "$CLAUDE_DIR/synced/bucket/docx" "$HOME/elsewhere/other-skill"
ln -s "$HOME/elsewhere/other-skill" "$CLAUDE_DIR/other-skill"
assert "setup 成功退出" run setup
assert "synced/ 内容未被改动" is_real_dir "$CLAUDE_DIR/synced/bucket/docx"
assert "无关软链接保持不变" is_link_to "$CLAUDE_DIR/other-skill" "$HOME/elsewhere/other-skill"
assert "check 成功退出" run check

echo "场景 4：add / remove 同步 ~/.claude/skills、README 与下游引用"
new_fixture add-remove
run setup
assert "add 成功退出" run add "$EXT"
assert "README 将 demo-ext 归入 ext 分组" grep -qx '### ext' "$REPO/README.md"
assert "下游引用清单已登记 demo-ext" grep -qF "| ext/skills/demo-ext | AG-Tools/tiga-skills/03-skills/demo-ext | link |" "$AGTOOLS/SKILLS-REFS.md"
assert "demo-ext 链接已建立" is_link_to "$CLAUDE_DIR/demo-ext" "$SKILLS/demo-ext"
assert "add 后 check 成功退出" run check
assert "remove 成功退出" run remove demo-ext
assert "README 已移除 demo-ext" lacks "demo-ext" "$REPO/README.md"
assert "下游引用清单已删除 demo-ext" lacks "03-skills/demo-ext" "$AGTOOLS/SKILLS-REFS.md"
assert "demo-ext 链接已清理" absent "$CLAUDE_DIR/demo-ext"
assert "remove 后 check 成功退出" run check

echo "场景 5：README 分组顺序为 项目级技能 → custom-skills → 其余"
assert "README 分组顺序正确" bash -c '[ "$(grep "^### " "$0" | tr "\n" ,)" = "### 项目级技能,### custom-skills," ]' "$REPO/README.md"

echo "场景 6：setup 清理指向 03-skills/ 的失效链接，修正悬空同名链接"
new_fixture prune
mkdir -p "$CLAUDE_DIR"
ln -s "$SKILLS/gone-skill" "$CLAUDE_DIR/gone-skill"
ln -s "$HOME/old-location/03-skills/demo-custom" "$CLAUDE_DIR/demo-custom"
assert "check 报告问题并失败" run_fails check
assert "setup 成功退出" run setup
assert "失效链接已删除" absent "$CLAUDE_DIR/gone-skill"
assert "悬空同名链接已改指向当前仓库" is_link_to "$CLAUDE_DIR/demo-custom" "$SKILLS/demo-custom"

echo "场景 7：同名真实目录冲突时不覆盖"
new_fixture conflict
mkdir -p "$CLAUDE_DIR/demo-custom"
echo keep > "$CLAUDE_DIR/demo-custom/marker"
assert "setup 成功退出" run setup
assert "setup 输出冲突提示" output_has "冲突"
assert "同名真实目录未被覆盖" [ -f "$CLAUDE_DIR/demo-custom/marker" ]
assert "check 报告冲突并失败" run_fails check

echo "场景 8：check 发现缺失的技能链接"
new_fixture missing
run setup
rm "$CLAUDE_DIR/demo-custom"
assert "check 失败退出" run_fails check
assert "check 输出缺失项" output_has "~/.claude/skills/demo-custom"

echo "场景 9：remove 时 SKILLS-REFS.md 缺失仍完整执行"
new_fixture refs-missing
run setup
run add "$EXT"
rm "$AGTOOLS/SKILLS-REFS.md"
assert "remove 成功退出" run remove demo-ext
assert "remove 提示未找到下游引用清单" output_has "跳过下游引用清单维护"
assert "README 已移除 demo-ext" lacks "demo-ext" "$REPO/README.md"
assert "demo-ext 链接已清理" absent "$CLAUDE_DIR/demo-ext"

echo "场景 10：remove 来源已失效的 AG-Tools 技能"
new_fixture broken-source
run setup
run add "$EXT"
rm -rf "$EXT"
assert "remove 成功退出" run remove demo-ext
assert "03-skills/demo-ext 已删除" absent "$SKILLS/demo-ext"
assert "下游引用清单中的残留行已清理" lacks "03-skills/demo-ext" "$AGTOOLS/SKILLS-REFS.md"
assert "demo-ext 链接已清理" absent "$CLAUDE_DIR/demo-ext"

echo "场景 11：拒绝会被遍历跳过或与 Claude Code 冲突的技能名"
new_fixture reserved-name
printf '%s\n' "synced.description=保留名" ".hidden.description=隐藏名" >> "$REPO/descriptions-zh.conf"
assert "add --name synced 被拒绝" run_fails add "$EXT" --name synced
assert "add --name .hidden 被拒绝" run_fails add "$EXT" --name .hidden
assert "03-skills/ 未新增条目" entry_count_is 1

echo "场景 12：Codex 链接指向别处时不覆盖"
new_fixture codex-conflict
mkdir -p "$HOME/.codex/skills" "$HOME/elsewhere"
ln -s "$HOME/elsewhere" "$CODEX_LINK"
assert "setup 成功退出" run setup
assert "setup 输出跳过" output_has "跳过"
assert "Codex 链接保持不变" is_link_to "$CODEX_LINK" "$HOME/elsewhere"
assert "Claude 技能链接仍已建立" is_link_to "$CLAUDE_DIR/demo-custom" "$SKILLS/demo-custom"
assert "check 报告 Codex 链接错误并失败" run_fails check

echo ""
echo "结果：$pass 通过，$fail 失败"
[ "$fail" -eq 0 ]
