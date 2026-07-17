#!/usr/bin/env bash
# 技能管理脚本 — 管理 02-agent-skills/ 中的软链接并更新 README.md
# 02-agent-skills/ 为扁平结构：技能软链接直接位于该目录下，来源分类通过解析符号链接目标推断，仅用于展示分组

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$PROJECT_ROOT/02-agent-skills"
CUSTOM_DIR="$PROJECT_ROOT/03-custom-skills"
README="$PROJECT_ROOT/README.md"
DESCRIPTIONS_ZH_CONF="$PROJECT_ROOT/descriptions-zh.conf"
AGTOOLS_ROOT="$HOME/Projects/AG-Tools"
SKILLS_REFS_FILE="$AGTOOLS_ROOT/SKILLS-REFS.md"

# ── 辅助函数 ──

die() { echo "错误: $1" >&2; exit 1; }

validate_skill_name() {
  local name="$1"
  [[ -n "$name" && "$name" != "." && "$name" != ".." && "$name" != */* && \
    "$name" != *$'\t'* && "$name" != *$'\n'* ]] || die "无效的技能名称: $name"
}

require_no_args() { [ "$#" -eq 0 ] || die "命令不接受额外参数: $*"; }

resolve_directory() (
  cd "$1" 2>/dev/null && cd "$2" 2>/dev/null && pwd
)

# 将 $HOME 下的绝对路径转换为相对于 $SKILLS_DIR 的相对路径
# 目的：软链接不写死用户名，仓库布局一致时可跨机器移植
to_portable_target() {
  local target="$1"
  if [[ "$target" != "$HOME/"* ]]; then
    echo "⚠ 目标不在 \$HOME 下，保留绝对路径（跨机器不可移植）: $target" >&2
    echo "$target"
    return
  fi

  # 从 $SKILLS_DIR 逐级向上找公共前缀，每上一级补一个 ..
  local common="$SKILLS_DIR" up=""
  while [[ "$target" != "$common" && "$target" != "$common/"* ]]; do
    [ "$common" != "/" ] || break
    common="$(dirname "$common")"
    up="../$up"
  done

  if [ "$common" = "/" ]; then
    echo "${up}${target#/}"
  else
    echo "${up}${target#"$common"/}"
  fi
}

# 同步维护 AG-Tools SKILLS-REFS.md 下游引用清单
# 用法: sync_agtools_refs <add|remove> <上游相对路径> <引用方条目路径>
# add 按整行去重后插入并保持表体按上游技能列排序；remove 按引用方列精确删除
# AG-Tools 缺失时跳过并提示；add 时文件缺失则按模板自动创建，remove 时缺失仅提示
sync_agtools_refs() {
  local action="$1" upstream="$2" consumer="$3"
  local row="| ${upstream} | ${consumer} | link |"

  if [ ! -d "$AGTOOLS_ROOT" ]; then
    echo "⚠ 未找到 $AGTOOLS_ROOT，跳过下游引用清单维护" >&2
    return
  fi
  if [ ! -f "$SKILLS_REFS_FILE" ]; then
    if [ "$action" = "remove" ]; then
      echo "⚠ 未找到 $SKILLS_REFS_FILE，跳过下游引用清单维护" >&2
      return
    fi
    cat > "$SKILLS_REFS_FILE" <<'EOF'
# 下游引用

> 记录 AG-Tools 技能被下游仓库引用的情况，回答"哪些 skill 被哪些仓库引用"。
> **维护契约**：本清单由下游消费方维护——各项目 `.agents/skills/` 条目的增删由 tiga-local-skills 负责，Tiga-Skills `02-agent-skills/` 注册表的增删由其 `manage-skills.sh` 负责。
> 行格式：上游技能为相对 AG-Tools 根目录的路径；引用方为相对 `~/Projects` 的条目路径（含条目名，覆盖 `--name` 重命名）；方式为 `link` 或 `copy`。表体按"上游技能"列排序。

| 上游技能 | 引用方 | 方式 |
| -------- | ------ | ---- |
EOF
    echo "✓ 已按模板创建 $SKILLS_REFS_FILE"
  fi

  if [ "$action" = "add" ] && grep -qxF "$row" "$SKILLS_REFS_FILE"; then
    echo "✓ 下游引用清单已存在该行，无需追加"
    return
  fi
  if [ "$action" = "remove" ] && ! grep -qF "| ${consumer} |" "$SKILLS_REFS_FILE"; then
    echo "⚠ 下游引用清单中未找到引用方 ${consumer} 的行，跳过删除" >&2
    return
  fi

  local template rowsfile outfile
  template="$(mktemp)"
  rowsfile="$(mktemp)"
  outfile="$(mktemp)"

  # 拆分：文件中第一个表格（表头行 + 分隔行之后的连续 | 行）的数据行写入 rowsfile，原位置留 @@ROWS@@ 占位
  awk -v rowsfile="$rowsfile" '
    !done && /^\|/ {
      if (!sep_seen) {
        print
        if ($0 ~ /^\| *-/) { sep_seen = 1; print "@@ROWS@@" }
        next
      }
      print $0 >> rowsfile
      next
    }
    sep_seen { done = 1 }
    { print }
  ' "$SKILLS_REFS_FILE" > "$template"

  if ! grep -qx '@@ROWS@@' "$template"; then
    echo "⚠ 未能定位下游引用表体（表头或分隔行缺失），跳过维护" >&2
    rm -f "$template" "$rowsfile" "$outfile"
    return
  fi

  if [ "$action" = "add" ]; then
    printf '%s\n' "$row" >> "$rowsfile"
  else
    grep -vF "| ${consumer} |" "$rowsfile" > "$rowsfile.filtered" || true
    mv "$rowsfile.filtered" "$rowsfile"
  fi

  # 表体按上游技能列排序（C locale + 大小写折叠，保证跨环境 diff 稳定）
  LC_ALL=C sort -f "$rowsfile" -o "$rowsfile"

  # 将排序后的表体回填到占位位置
  awk -v rowsfile="$rowsfile" '
    $0 == "@@ROWS@@" {
      while ((getline line < rowsfile) > 0) print line
      close(rowsfile)
      next
    }
    { print }
  ' "$template" > "$outfile"

  cat "$outfile" > "$SKILLS_REFS_FILE"
  rm -f "$template" "$rowsfile" "$outfile"

  if [ "$action" = "add" ]; then
    echo "✓ 下游引用清单已追加: $row"
  else
    echo "✓ 下游引用清单已删除引用方 ${consumer} 的行"
  fi
}

# 从 descriptions-zh.conf 读取 README 字段
lookup_readme_field() {
  local name="$1" field="$2" key
  [ -f "$DESCRIPTIONS_ZH_CONF" ] || return
  key="${name}.${field}="
  awk -v key="$key" 'index($0, key) == 1 { print substr($0, length(key) + 1); exit }' "$DESCRIPTIONS_ZH_CONF"
}

# 获取并校验 README 所需的中文说明
readme_description() {
  local name="$1" desc
  desc="$(lookup_readme_field "$name" "description")"
  [ -n "$desc" ] || die "descriptions-zh.conf 缺少 ${name}.description"
  printf '%s' "$desc"
}

# 删除技能时同步清理 README 元数据
remove_readme_metadata() {
  local name="$1" tmpfile
  [ -f "$DESCRIPTIONS_ZH_CONF" ] || return
  tmpfile="$(mktemp)"
  awk -v prefix="${name}." 'index($0, prefix) != 1 { print }' "$DESCRIPTIONS_ZH_CONF" > "$tmpfile"
  cat "$tmpfile" > "$DESCRIPTIONS_ZH_CONF"
  rm -f "$tmpfile"
  echo "✓ 已移除 README 元数据: $name"
}

# 从 SKILL.md frontmatter（前两个 --- 之间）提取单行字段值，去除成对的包裹引号
# 现有技能的 name / description 均为单行值，不处理多行 YAML
frontmatter_field() {
  local file="$1" field="$2" value
  value="$(awk -v key="$field" '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && index($0, key ":") == 1 {
      value = substr($0, length(key) + 2)
      sub(/^[ \t]+/, "", value)
      print value
      exit
    }
  ' "$file")"
  if [ "${#value}" -ge 2 ]; then
    case "$value" in
      \"*\" | \'*\') value="${value:1:${#value}-2}" ;;
    esac
  fi
  printf '%s' "$value"
}

# 按官方 Agent Skills 规范校验并输出单个技能的 frontmatter 检查结果
# 参数: SKILL.md 路径、期望名称（注册链接名，即 agent 实际看到的目录名）、显示标签
check_skill_frontmatter() {
  local file="$1" expected_name="$2" label="$3" name desc violations=()
  name="$(frontmatter_field "$file" "name")"
  desc="$(frontmatter_field "$file" "description")"

  [ -n "$name" ] || violations+=("缺少 name 字段")
  if [ -n "$name" ]; then
    [[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || violations+=("name 格式不合规（需全小写，无首尾或连续连字符）: $name")
    [ "${#name}" -le 64 ] || violations+=("name 超过 64 字符（当前 ${#name}）")
    [ "$name" = "$expected_name" ] || violations+=("name 与注册名不一致: $name != $expected_name")
  fi
  [ -n "$desc" ] || violations+=("缺少 description 字段或值为空")
  [ "${#desc}" -le 1024 ] || violations+=("description 超过 1024 字符（当前 ${#desc}）")

  if [ "${#violations[@]}" -eq 0 ]; then
    echo "  ✓ ${label}"
    return 0
  fi

  echo "  ✗ ${label}（frontmatter 不合规）"
  printf '      - %s\n' "${violations[@]}"
  return 1
}

# 转义 Markdown 表格单元格中的分隔符
escape_markdown_cell() {
  local value="$1"
  value="${value//|/\\|}"
  printf '%s' "$value"
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

skill_categories() {
  printf '%s\n' custom-skills superpowers
  cut -f1 "$1" | sort -u | awk '$0 != "custom-skills" && $0 != "superpowers"'
}

# 判断技能来源类别（用于展示分组，不再对应物理子目录）
classify_source() {
  local target="$1"
  if [[ "$target" =~ /AG-Tools/([^/]+)/ ]]; then
    echo "${BASH_REMATCH[1]}"
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

    resolved="$(resolve_directory "$SKILLS_DIR" "$target")" || resolved=""
    if [ -z "$resolved" ]; then
      echo "⚠ 软链接目标无法解析: $name -> $target" >&2
    elif [ ! -f "$resolved/SKILL.md" ]; then
      echo "⚠ 缺少 SKILL.md: $name -> $target" >&2
    fi

    desc="$(readme_description "$name")"
    printf '%s\t%s\t%s\n' "$category" "$name" "$desc" >> "$outfile"
  done
}

# 创建或修复单个用户级软链接；仅 Claude 的目录链接允许交互替换真实目录
ensure_user_link() {
  local link="$1" target="$2" replace_directory="${3:-false}"
  local existing answer action

  mkdir -p "$(dirname "$link")"

  if [ -L "$link" ]; then
    existing="$(readlink "$link")"
    if [ "$existing" = "$target" ]; then
      echo "✓ $link 已指向正确目标"
      return
    fi
    echo "⚠ $link 当前指向 $existing"
    echo "  期望目标: $target"
    action="更新"
  elif [ -e "$link" ]; then
    if [ "$replace_directory" != "true" ] || [ ! -d "$link" ]; then
      die "$link 已存在且不是软链接，请手动处理"
    fi
    echo "⚠ $link 是一个真实目录"
    echo "  需要替换为指向 $target 的软链接"
    action="替换"
  else
    ln -s "$target" "$link"
    echo "✓ 已创建 $link -> $target"
    return
  fi

  read -r -p "  是否${action}？[y/N] " answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "  跳过"
    return
  fi
  rm -rf "$link"
  ln -s "$target" "$link"
  echo "✓ 已${action} $link -> $target"
}

# ── setup ──

cmd_setup() {
  require_no_args "$@"
  ensure_user_link "$HOME/.claude/skills" "$SKILLS_DIR" true
  ensure_user_link "$HOME/.codex/skills/tiga-skills" "$SKILLS_DIR"
}

# ── add ──

cmd_add() {
  local source_path="" name=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --name)
        [ "$#" -ge 2 ] || die "--name 缺少参数"
        [ -z "$name" ] || die "--name 只能指定一次"
        name="$2"
        shift 2
        ;;
      --*) die "未知选项: $1" ;;
      *)
        [ -z "$source_path" ] || die "只能指定一个 source-path"
        source_path="$1"
        shift
        ;;
    esac
  done

  [ -z "$source_path" ] && die "用法: $0 add <source-path> [--name <name>]"

  # 展开 ~ 并转为绝对路径
  source_path="${source_path/#\~/$HOME}"
  source_path="$(cd "$source_path" 2>/dev/null && pwd)" || die "路径不存在: $source_path"

  [ -f "$source_path/SKILL.md" ] || die "未找到 SKILL.md: $source_path/SKILL.md"

  [ -z "$name" ] && name="$(basename "$source_path")"
  validate_skill_name "$name"

  local link="$SKILLS_DIR/$name"
  [[ -e "$link" || -L "$link" ]] && die "技能 '$name' 已存在于 02-agent-skills/"
  readme_description "$name" > /dev/null

  local category
  category="$(classify_source "$source_path")"

  # 转换为可移植的相对路径后再创建软链接
  local link_target
  link_target="$(to_portable_target "$source_path")"

  ln -s "$link_target" "$link"
  echo "✓ 已添加 ${name} -> ${link_target}（分类: ${category}）"

  # 来源位于 AG-Tools 时，同步登记下游引用
  if [[ "$source_path" == "$AGTOOLS_ROOT/"* ]]; then
    sync_agtools_refs add "${source_path#"$AGTOOLS_ROOT"/}" "${PROJECT_ROOT#"$HOME/Projects/"}/02-agent-skills/$name"
  fi
  cmd_update_readme
}

# ── add-custom ──

cmd_add_custom() {
  [ "$#" -eq 1 ] || die "用法: $0 add-custom <name>"
  local name="$1"
  validate_skill_name "$name"
  [ -d "$CUSTOM_DIR/$name" ] || die "自定义技能不存在: 03-custom-skills/$name"
  [ -f "$CUSTOM_DIR/$name/SKILL.md" ] || die "未找到 SKILL.md: 03-custom-skills/$name/SKILL.md"

  local link="$SKILLS_DIR/$name"
  [[ -e "$link" || -L "$link" ]] && die "技能 '$name' 已存在于 02-agent-skills/"
  readme_description "$name" > /dev/null

  ln -s "../03-custom-skills/$name" "$link"
  echo "✓ 已添加 ${name} -> ../03-custom-skills/${name}（分类: custom-skills）"
  cmd_update_readme
}

# ── remove ──

cmd_remove() {
  [ "$#" -eq 1 ] || die "用法: $0 remove <name>"
  local name="$1" link
  validate_skill_name "$name"
  link="$SKILLS_DIR/$name"
  [ -L "$link" ] || die "未找到技能 '$name'"

  # 删除前先解析链接目标，用于判断是否需同步清理下游引用
  local target resolved
  target="$(readlink "$link")"
  resolved="$(resolve_directory "$SKILLS_DIR" "$target")" || resolved=""

  rm "$link"
  remove_readme_metadata "$name"
  echo "✓ 已移除 $name"

  if [ -n "$resolved" ] && [[ "$resolved" == "$AGTOOLS_ROOT/"* ]]; then
    sync_agtools_refs remove "${resolved#"$AGTOOLS_ROOT"/}" "${PROJECT_ROOT#"$HOME/Projects/"}/02-agent-skills/$name"
  elif [ -z "$resolved" ] && [[ "$target" == *AG-Tools* ]]; then
    echo "⚠ 链接目标无法解析: $target，SKILLS-REFS.md 下游引用清单中的对应行可能需手动清理" >&2
  fi
  cmd_update_readme
}

# ── list ──

cmd_list() {
  require_no_args "$@"
  echo "已注册技能:"
  echo "─────────────────────────────────────────────────────"

  local rowsfile
  rowsfile="$(mktemp)"
  collect_skill_rows "$rowsfile"

  local total=0
  local category

  print_category_list() {
    local category="$1"
    local count
    count="$(awk -F'\t' -v c="$category" '$1 == c { count++ } END { print count + 0 }' "$rowsfile")"
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

  while IFS= read -r category; do
    print_category_list "$category"
  done < <(skill_categories "$rowsfile")

  rm -f "$rowsfile"

  if [ "$total" -eq 0 ]; then
    echo "(无)"
  fi
  echo ""
  echo "共 $total 个技能"
}

# ── check ──

cmd_check() {
  require_no_args "$@"
  local ok=0 bad=0

  echo "检查 02-agent-skills/ 技能软链接:"
  local link
  for link in "$SKILLS_DIR"/*; do
    [ -L "$link" ] || continue
    local name target resolved
    name="$(basename "$link")"
    target="$(readlink "$link")"
    resolved="$(resolve_directory "$SKILLS_DIR" "$target")" || resolved=""

    if [ -z "$resolved" ]; then
      echo "  ✗ ${name} -> ${target}（目标无法解析）"
      bad=$((bad + 1))
    elif [ ! -f "$resolved/SKILL.md" ]; then
      echo "  ✗ ${name} -> ${target}（缺少 SKILL.md）"
      bad=$((bad + 1))
    elif [[ "$resolved" != "$PROJECT_ROOT/"* ]]; then
      # 外部上游源不可修改，跳过 frontmatter 校验
      echo "  ✓ ${name} -> ${target}（外部源，跳过 frontmatter 校验）"
      ok=$((ok + 1))
    else
      # 仓库内的源追加官方规范 frontmatter 校验
      if check_skill_frontmatter "$resolved/SKILL.md" "$name" "${name} -> ${target}"; then
        ok=$((ok + 1))
      else
        bad=$((bad + 1))
      fi
    fi
  done

  echo ""
  echo "检查项目级技能 (.agents/skills/):"
  local skill_dir
  for skill_dir in "$PROJECT_ROOT/.agents/skills"/*/; do
    [ -d "$skill_dir" ] || continue
    local sname
    sname="$(basename "$skill_dir")"
    if [ ! -f "${skill_dir}SKILL.md" ]; then
      echo "  ✗ ${sname}（缺少 SKILL.md）"
      bad=$((bad + 1))
      continue
    fi
    if check_skill_frontmatter "${skill_dir}SKILL.md" "$sname" "$sname"; then
      ok=$((ok + 1))
    else
      bad=$((bad + 1))
    fi
  done

  echo ""
  echo "检查项目级链接:"
  local expected="$PROJECT_ROOT/.agents/skills"
  local plink
  for plink in "$PROJECT_ROOT/.claude/skills" "$PROJECT_ROOT/.codex/skills"; do
    local label="${plink#"$PROJECT_ROOT"/}"
    if [ ! -L "$plink" ]; then
      echo "  ✗ ${label}（不是软链接）"
      bad=$((bad + 1))
      continue
    fi
    local ptarget presolved
    ptarget="$(readlink "$plink")"
    presolved="$(resolve_directory "$(dirname "$plink")" "$ptarget")" || presolved=""
    if [ "$presolved" = "$expected" ]; then
      echo "  ✓ ${label} -> ${ptarget}"
      ok=$((ok + 1))
    else
      echo "  ✗ ${label} -> ${ptarget}（应指向 .agents/skills）"
      bad=$((bad + 1))
    fi
  done

  # 根目录 SKILLS-REFS.md 应为软链接且可解析到 AG-Tools 下游引用清单
  local srefs="$PROJECT_ROOT/SKILLS-REFS.md"
  if [ ! -L "$srefs" ]; then
    echo "  ✗ SKILLS-REFS.md（缺失或不是软链接）"
    bad=$((bad + 1))
  elif [ "$srefs" -ef "$SKILLS_REFS_FILE" ]; then
    echo "  ✓ SKILLS-REFS.md -> $(readlink "$srefs")"
    ok=$((ok + 1))
  elif [ -f "$srefs" ]; then
    echo "  ✗ SKILLS-REFS.md -> $(readlink "$srefs")（应指向 ${SKILLS_REFS_FILE}）"
    bad=$((bad + 1))
  else
    echo "  ✗ SKILLS-REFS.md -> $(readlink "$srefs")（目标无法解析为文件）"
    bad=$((bad + 1))
  fi

  echo ""
  echo "共检查 $((ok + bad)) 项：$ok 正常，$bad 失效"
  if [ "$bad" -gt 0 ]; then
    exit 1
  fi
}

# ── update-readme ──

cmd_update_readme() {
  require_no_args "$@"
  [ -f "$README" ] || die "README.md 不存在"
  awk '
    /<!-- BEGIN SKILL LIST -->/ { begin_count++; begin_line=NR }
    /<!-- END SKILL LIST -->/ { end_count++; end_line=NR }
    END { exit !(begin_count == 1 && end_count == 1 && begin_line < end_line) }
  ' "$README" || die "README.md 必须包含一组顺序正确的技能清单标记"

  local tmpfile tablefile rowsfile
  tmpfile="$(mktemp)"
  tablefile="$(mktemp)"
  rowsfile="$(mktemp)"
  collect_skill_rows "$rowsfile"

  # 输出单个分类的表格
  generate_category_table() {
    local category="$1"
    local count
    count="$(awk -F'\t' -v c="$category" '$1 == c { count++ } END { print count + 0 }' "$rowsfile")"
    [ "$count" -eq 0 ] && return

    echo "### $category"
    echo ""
    echo "$(category_description "$category")"
    echo ""
    echo "| 名称 | 描述 |"
    echo "| ---- | ---- |"

    while IFS=$'\t' read -r cat name desc; do
      [ "$cat" = "$category" ] || continue
      printf '| %s | %s |\n' \
        "$(escape_markdown_cell "$name")" \
        "$(escape_markdown_cell "$desc")"
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
        local name desc
        name="$(basename "$skill_dir")"
        desc="$(readme_description "$name")"
        printf '| %s | %s |\n' \
          "$(escape_markdown_cell "$name")" \
          "$(escape_markdown_cell "$desc")"
      done

      echo ""
    fi

    # 2. 指定顺序的分类，再追加其余字母序分类
    local category
    while IFS= read -r category; do
      generate_category_table "$category"
    done < <(skill_categories "$rowsfile")
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

  # 仅在内容变化时覆写，并保留 README 原有文件权限
  if cmp -s "$tmpfile" "$README"; then
    echo "✓ README.md 技能清单无需更新"
  else
    cat "$tmpfile" > "$README"
    echo "✓ README.md 技能清单已更新"
  fi
  rm -f "$tmpfile" "$tablefile" "$rowsfile"
}

print_usage() {
  cat <<EOF
用法: $0 <command> [args]

命令:
  setup                          创建用户级软链接 (~/.claude/skills → 目录链接, ~/.codex/skills/tiga-skills → 子链接)
  add <path> [--name <name>]     从外部路径添加技能到 02-agent-skills/
  add-custom <name>              从 03-custom-skills/ 添加技能到 02-agent-skills/
  remove <name>                  按名称移除技能软链接
  list                           按来源分组列出已注册技能
  check                          检查技能软链接与项目级链接的健康状态
  update-readme                  更新 README.md 技能清单（按来源分组）
EOF
}

# ── 主入口 ──

cmd="${1:-}"
shift || true

case "$cmd" in
  setup)        cmd_setup "$@" ;;
  add)          cmd_add "$@" ;;
  add-custom)   cmd_add_custom "$@" ;;
  remove)       cmd_remove "$@" ;;
  list)         cmd_list "$@" ;;
  check)        cmd_check "$@" ;;
  update-readme) cmd_update_readme "$@" ;;
  *)
    print_usage
    exit 1
    ;;
esac
