#!/usr/bin/env bash
# 技能管理脚本 — 管理 02-agent-skills/ 中的软链接并更新 README.md
# 02-agent-skills/ 按来源分组为子目录（superpowers/、custom-skills/ 等）

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

# 判断技能来源类别，返回子目录名
classify_source() {
  local target="$1"
  if [[ "$target" == *"/AG-Tools/"* ]]; then
    echo "$target" | sed -n 's|.*/AG-Tools/\([^/]*\)/.*|\1|p'
  elif [[ "$target" == *"03-custom-skills/"* ]] || [[ "$target" == "../../03-custom-skills/"* ]]; then
    echo "custom-skills"
  else
    echo "external"
  fi
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

  # 根据来源确定子目录
  local category
  category="$(classify_source "$source_path")"
  mkdir -p "$SKILLS_DIR/$category"

  local link="$SKILLS_DIR/$category/$name"
  [ -e "$link" ] && die "技能 '$name' 已存在于 02-agent-skills/$category/"

  ln -s "$source_path" "$link"
  echo "✓ 已添加 $name -> $source_path（分类: $category）"
  cmd_update_readme
}

# ── add-custom ──

cmd_add_custom() {
  local name="$1"
  [ -z "$name" ] && die "用法: $0 add-custom <name>"
  [ -d "$CUSTOM_DIR/$name" ] || die "自定义技能不存在: 03-custom-skills/$name"

  mkdir -p "$SKILLS_DIR/custom-skills"

  local link="$SKILLS_DIR/custom-skills/$name"
  [ -e "$link" ] && die "技能 '$name' 已存在于 02-agent-skills/custom-skills/"

  ln -s "../../03-custom-skills/$name" "$link"
  echo "✓ 已添加 $name -> ../../03-custom-skills/$name（分类: custom-skills）"
  cmd_update_readme
}

# ── remove ──

cmd_remove() {
  local name="$1"
  [ -z "$name" ] && die "用法: $0 remove <name>"

  # 在子目录中搜索匹配的软链接
  local found
  found="$(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -name "$name" -type l 2>/dev/null | head -1)"

  [ -z "$found" ] && die "未找到技能 '$name'（已在所有子目录中搜索）"
  [ -L "$found" ] || die "'$found' 不是软链接，拒绝删除"

  rm "$found"
  echo "✓ 已移除 $name（位于 $(dirname "$found" | xargs basename)/）"
  cmd_update_readme
}

# ── list ──

cmd_list() {
  echo "已注册技能:"
  echo "─────────────────────────────────────────────────────"

  local total=0

  for category_dir in "$SKILLS_DIR"/*/; do
    [ -d "$category_dir" ] || continue
    local category
    category="$(basename "$category_dir")"

    local count=0
    for link in "$category_dir"*/; do
      [ -L "${link%/}" ] || continue
      count=$((count + 1))
    done

    [ "$count" -eq 0 ] && continue

    echo ""
    echo "[$category] ($count 个)"
    printf "  %-35s %s\n" "名称" "描述"
    echo "  ───────────────────────────────────────────────────"

    for link in "$category_dir"*/; do
      [ -L "${link%/}" ] || continue
      local name
      name="$(basename "${link%/}")"

      local desc=""
      local resolved
      resolved="$(cd "$SKILLS_DIR/$category" && cd "$(readlink "${link%/}")" 2>/dev/null && pwd)" || resolved=""
      if [ -n "$resolved" ] && [ -f "$resolved/SKILL.md" ]; then
        desc="$(extract_field "$resolved/SKILL.md" "description_zh")"
        [ -z "$desc" ] && desc="$(lookup_description_zh "$name")"
        [ -z "$desc" ] && desc="$(extract_field "$resolved/SKILL.md" "description")"
      fi

      printf "  %-35s %s\n" "$name" "$desc"
      total=$((total + 1))
    done
  done

  if [ "$total" -eq 0 ]; then
    echo "(无)"
  fi
  echo ""
  echo "共 $total 个技能"
}

# ── update-readme ──

cmd_update_readme() {
  [ -f "$README" ] || die "README.md 不存在"

  local tmpfile
  tmpfile="$(mktemp)"
  local tablefile
  tablefile="$(mktemp)"

  # 输出单个分类目录的表格
  generate_category_table() {
    local category="$1"
    local category_dir="$SKILLS_DIR/$category"
    [ -d "$category_dir" ] || return

    local has_links=0
    for link in "$category_dir"/*/; do
      [ -L "${link%/}" ] && { has_links=1; break; }
    done
    [ "$has_links" -eq 0 ] && return

    echo "### $category"
    echo ""
    echo "$(category_description "$category")"
    echo ""
    echo "| 名称 | 描述 |"
    echo "| ---- | ---- |"

    for link in "$category_dir"/*/; do
      [ -L "${link%/}" ] || continue
      local name
      name="$(basename "${link%/}")"

      local desc=""
      local resolved
      resolved="$(cd "$category_dir" && cd "$(readlink "${link%/}")" 2>/dev/null && pwd)" || resolved=""
      if [ -n "$resolved" ] && [ -f "$resolved/SKILL.md" ]; then
        desc="$(extract_field "$resolved/SKILL.md" "description_zh")"
        [ -z "$desc" ] && desc="$(lookup_description_zh "$name")"
        [ -z "$desc" ] && desc="$(extract_field "$resolved/SKILL.md" "description")"
      fi

      echo "| $name | $desc |"
    done

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
    for category in $ordered_categories; do
      generate_category_table "$category"
    done

    # 3. 其余分类按字母序
    for category_dir in "$SKILLS_DIR"/*/; do
      [ -d "$category_dir" ] || continue
      local category
      category="$(basename "$category_dir")"
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
  rm -f "$tablefile"
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
    echo "  add <path> [--name <name>]     从外部路径添加技能（自动按来源分组到子目录）"
    echo "  add-custom <name>              从 03-custom-skills/ 添加技能到 custom-skills/ 子目录"
    echo "  remove <name>                  按名称搜索并移除技能软链接"
    echo "  list                           按来源分组列出已注册技能"
    echo "  update-readme                  更新 README.md 技能清单（按来源分组）"
    exit 1
    ;;
esac
