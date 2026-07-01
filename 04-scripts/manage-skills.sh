#!/usr/bin/env bash
# 技能管理脚本 — 管理 02-agent-skills/ 中的软链接并更新 README.md
# 02-agent-skills/ 为扁平结构：技能软链接直接位于该目录下，来源分类通过解析符号链接目标推断，仅用于展示分组

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$PROJECT_ROOT/02-agent-skills"
CUSTOM_DIR="$PROJECT_ROOT/03-custom-skills"
README="$PROJECT_ROOT/README.md"

# ── 辅助函数 ──

die() { echo "错误: $1" >&2; exit 1; }

# 从 SKILL.md frontmatter 提取字段值
extract_field() {
  local file="$1" field="$2"
  sed -n '/^---$/,/^---$/p' "$file" | sed -n "s/^${field}: *//p" | head -1
}

# 从 descriptions-zh.conf 查找外部技能的中文描述覆盖
lookup_description_zh() {
  local name="$1"
  local conf="$SCRIPT_DIR/descriptions-zh.conf"
  [ -f "$conf" ] || return
  sed -n "s/^${name}=//p" "$conf" | head -1
}

# 根据分类子目录名返回来源说明文本
category_description() {
  local category="$1"
  case "$category" in
    superpowers)    echo "来源于 [AG-Tools/superpowers](https://github.com/Tiga08/AG-Tools)" ;;
    custom-skills)  echo '来源于 `03-custom-skills/`，通过 `add-custom` 命令注册' ;;
    *)              echo '来源于外部路径，通过 `add` 命令注册' ;;
  esac
}

# 判断技能来源类别（用于展示分组，不再对应物理子目录）
classify_source() {
  local target="$1"
  if [[ "$target" == *"/AG-Tools/"* ]]; then
    echo "$target" | sed -n 's|.*/AG-Tools/\([^/]*\)/.*|\1|p'
  elif [[ "$target" == *"03-custom-skills/"* ]]; then
    echo "custom-skills"
  else
    echo "external"
  fi
}

# 遍历 $SKILLS_DIR 下所有一级符号链接，输出 "分类\t名称\t描述" 到指定文件
collect_skill_rows() {
  local outfile="$1"
  : > "$outfile"

  local link
  for link in "$SKILLS_DIR"/*; do
    [ -L "$link" ] || continue
    local name target category resolved desc
    name="$(basename "$link")"
    target="$(readlink "$link")"
    category="$(classify_source "$target")"

    resolved="$(cd "$SKILLS_DIR" && cd "$target" 2>/dev/null && pwd)" || resolved=""
    desc=""
    if [ -n "$resolved" ] && [ -f "$resolved/SKILL.md" ]; then
      desc="$(extract_field "$resolved/SKILL.md" "description_zh")"
      [ -z "$desc" ] && desc="$(lookup_description_zh "$name")"
      [ -z "$desc" ] && desc="$(extract_field "$resolved/SKILL.md" "description")"
    fi

    printf '%s\t%s\t%s\n' "$category" "$name" "$desc" >> "$outfile"
  done
}

# ── setup ──

cmd_setup() {
  local target="$SKILLS_DIR"

  # ── Claude: ~/.claude/skills 整个目录作为软链接 ──
  local claude_link="$HOME/.claude/skills"

  if [ -L "$claude_link" ]; then
    local existing
    existing="$(readlink "$claude_link")"
    if [ "$existing" = "$target" ]; then
      echo "✓ $claude_link 已指向正确目标"
    else
      echo "⚠ $claude_link 当前指向 $existing"
      echo "  期望目标: $target"
      read -r -p "  是否更新？[y/N] " answer
      if [[ "$answer" =~ ^[Yy]$ ]]; then
        rm "$claude_link"
        ln -s "$target" "$claude_link"
        echo "✓ 已更新 $claude_link -> $target"
      else
        echo "  跳过"
      fi
    fi
  elif [ -d "$claude_link" ]; then
    echo "⚠ $claude_link 是一个真实目录"
    echo "  需要替换为指向 $target 的软链接"
    read -r -p "  是否删除该目录并创建软链接？[y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
      rm -rf "$claude_link"
      ln -s "$target" "$claude_link"
      echo "✓ 已替换 $claude_link -> $target"
    else
      echo "  跳过"
    fi
  elif [ -e "$claude_link" ]; then
    die "$claude_link 已存在且不是软链接或目录，请手动处理"
  else
    mkdir -p "$HOME/.claude"
    ln -s "$target" "$claude_link"
    echo "✓ 已创建 $claude_link -> $target"
  fi

  # ── Codex: ~/.codex/skills/tiga-skills 子链接（保持原有逻辑） ──
  local codex_dir="$HOME/.codex/skills"
  local codex_link="$codex_dir/tiga-skills"
  mkdir -p "$codex_dir"

  if [ -L "$codex_link" ]; then
    local existing
    existing="$(readlink "$codex_link")"
    if [ "$existing" = "$target" ]; then
      echo "✓ $codex_link 已指向正确目标"
    else
      echo "⚠ $codex_link 当前指向 $existing"
      echo "  期望目标: $target"
      read -r -p "  是否更新？[y/N] " answer
      if [[ "$answer" =~ ^[Yy]$ ]]; then
        rm "$codex_link"
        ln -s "$target" "$codex_link"
        echo "✓ 已更新 $codex_link -> $target"
      else
        echo "  跳过"
      fi
    fi
  elif [ -e "$codex_link" ]; then
    die "$codex_link 已存在且不是软链接，请手动处理"
  else
    ln -s "$target" "$codex_link"
    echo "✓ 已创建 $codex_link -> $target"
  fi
}

# ── add ──

cmd_add() {
  local source_path="" name=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --name) name="$2"; shift 2 ;;
      *) source_path="$1"; shift ;;
    esac
  done

  [ -z "$source_path" ] && die "用法: $0 add <source-path> [--name <name>]"

  # 展开 ~ 并转为绝对路径
  source_path="${source_path/#\~/$HOME}"
  source_path="$(cd "$source_path" 2>/dev/null && pwd)" || die "路径不存在: $source_path"

  [ -f "$source_path/SKILL.md" ] || die "未找到 SKILL.md: $source_path/SKILL.md"

  [ -z "$name" ] && name="$(basename "$source_path")"

  local link="$SKILLS_DIR/$name"
  [ -e "$link" ] && die "技能 '$name' 已存在于 02-agent-skills/"

  local category
  category="$(classify_source "$source_path")"

  ln -s "$source_path" "$link"
  echo "✓ 已添加 ${name} -> ${source_path}（分类: ${category}）"
  cmd_update_readme
}

# ── add-custom ──

cmd_add_custom() {
  local name="$1"
  [ -z "$name" ] && die "用法: $0 add-custom <name>"
  [ -d "$CUSTOM_DIR/$name" ] || die "自定义技能不存在: 03-custom-skills/$name"

  local link="$SKILLS_DIR/$name"
  [ -e "$link" ] && die "技能 '$name' 已存在于 02-agent-skills/"

  ln -s "../03-custom-skills/$name" "$link"
  echo "✓ 已添加 ${name} -> ../03-custom-skills/${name}（分类: custom-skills）"
  cmd_update_readme
}

# ── remove ──

cmd_remove() {
  local name="$1"
  [ -z "$name" ] && die "用法: $0 remove <name>"

  local found
  found="$(find "$SKILLS_DIR" -mindepth 1 -maxdepth 1 -name "$name" -type l 2>/dev/null | head -1)"

  [ -z "$found" ] && die "未找到技能 '$name'"
  [ -L "$found" ] || die "'$found' 不是软链接，拒绝删除"

  rm "$found"
  echo "✓ 已移除 $name"
  cmd_update_readme
}

# ── list ──

cmd_list() {
  echo "已注册技能:"
  echo "─────────────────────────────────────────────────────"

  local rowsfile
  rowsfile="$(mktemp)"
  collect_skill_rows "$rowsfile"

  local total=0
  local ordered_categories="custom-skills superpowers"
  local category

  print_category_list() {
    local category="$1"
    local count
    count="$(awk -F'\t' -v c="$category" '$1==c' "$rowsfile" | wc -l | tr -d ' ')"
    [ "$count" -eq 0 ] && return

    echo ""
    echo "[$category] ($count 个)"
    printf "  %-35s %s\n" "名称" "描述"
    echo "  ───────────────────────────────────────────────────"

    while IFS=$'\t' read -r cat name desc; do
      [ "$cat" = "$category" ] || continue
      printf "  %-35s %s\n" "$name" "$desc"
      total=$((total + 1))
    done < "$rowsfile"
  }

  for category in $ordered_categories; do
    print_category_list "$category"
  done

  for category in $(cut -f1 "$rowsfile" | sort -u); do
    [[ " $ordered_categories " == *" $category "* ]] && continue
    print_category_list "$category"
  done

  rm -f "$rowsfile"

  if [ "$total" -eq 0 ]; then
    echo "(无)"
  fi
  echo ""
  echo "共 $total 个技能"
}

# ── update-readme ──

cmd_update_readme() {
  [ -f "$README" ] || die "README.md 不存在"

  local tmpfile tablefile rowsfile
  tmpfile="$(mktemp)"
  tablefile="$(mktemp)"
  rowsfile="$(mktemp)"
  collect_skill_rows "$rowsfile"

  # 输出单个分类的表格
  generate_category_table() {
    local category="$1"
    local count
    count="$(awk -F'\t' -v c="$category" '$1==c' "$rowsfile" | wc -l | tr -d ' ')"
    [ "$count" -eq 0 ] && return

    echo "### $category"
    echo ""
    echo "$(category_description "$category")"
    echo ""
    echo "| 名称 | 描述 |"
    echo "| ---- | ---- |"

    while IFS=$'\t' read -r cat name desc; do
      [ "$cat" = "$category" ] || continue
      echo "| $name | $desc |"
    done < "$rowsfile"

    echo ""
  }

  # 生成分组表格：项目级技能 → custom-skills → superpowers → 其余字母序
  {
    # 1. 项目级技能
    local project_skills_dir="$PROJECT_ROOT/.agents/skills"
    local has_project_skills=0
    for skill_dir in "$project_skills_dir"/*/; do
      [ -f "$skill_dir/SKILL.md" ] && { has_project_skills=1; break; }
    done

    if [ "$has_project_skills" -eq 1 ]; then
      echo "### 项目级技能"
      echo ""
      echo "位于 \`.agents/skills/\`，供操作本仓库使用"
      echo ""
      echo "| 名称 | 描述 |"
      echo "| ---- | ---- |"

      for skill_dir in "$project_skills_dir"/*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        local name
        name="$(basename "$skill_dir")"
        local desc=""
        desc="$(extract_field "$skill_dir/SKILL.md" "description_zh")"
        [ -z "$desc" ] && desc="$(lookup_description_zh "$name")"
        [ -z "$desc" ] && desc="$(extract_field "$skill_dir/SKILL.md" "description")"
        echo "| $name | $desc |"
      done

      echo ""
    fi

    # 2. 指定顺序的分类
    local ordered_categories="custom-skills superpowers"
    local category
    for category in $ordered_categories; do
      generate_category_table "$category"
    done

    # 3. 其余分类按字母序
    for category in $(cut -f1 "$rowsfile" | sort -u); do
      [[ " $ordered_categories " == *" $category "* ]] && continue
      generate_category_table "$category"
    done
  } > "$tablefile"

  # 替换标记区域
  awk -v tfile="$tablefile" '
    /<!-- BEGIN SKILL LIST -->/ {
      print
      print ""
      while ((getline line < tfile) > 0) print line
      close(tfile)
      skip=1
      next
    }
    /<!-- END SKILL LIST -->/ { skip=0 }
    skip { next }
    { print }
  ' "$README" > "$tmpfile"

  mv "$tmpfile" "$README"
  rm -f "$tablefile" "$rowsfile"
  echo "✓ README.md 技能清单已更新"
}

# ── 主入口 ──

cmd="${1:-}"
shift || true

case "$cmd" in
  setup)        cmd_setup ;;
  add)          cmd_add "$@" ;;
  add-custom)   cmd_add_custom "${1:-}" ;;
  remove)       cmd_remove "${1:-}" ;;
  list)         cmd_list ;;
  update-readme) cmd_update_readme ;;
  *)
    echo "用法: $0 <command> [args]"
    echo ""
    echo "命令:"
    echo "  setup                          创建用户级软链接 (~/.claude/skills → 目录链接, ~/.codex/skills/tiga-skills → 子链接)"
    echo "  add <path> [--name <name>]     从外部路径添加技能到 02-agent-skills/"
    echo "  add-custom <name>              从 03-custom-skills/ 添加技能到 02-agent-skills/"
    echo "  remove <name>                  按名称移除技能软链接"
    echo "  list                           按来源分组列出已注册技能"
    echo "  update-readme                  更新 README.md 技能清单（按来源分组）"
    exit 1
    ;;
esac
