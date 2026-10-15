#!/usr/bin/env bash
# 技能管理脚本 — 管理 03-skills/ 中的技能注册并更新 README.md
# 03-skills/ 为统一技能目录：自定义技能为真实目录，外部技能为符号链接；来源分类通过条目类型和链接目标推断，仅用于展示分组

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$PROJECT_ROOT/03-skills"
README="$PROJECT_ROOT/README.md"
DESCRIPTIONS_ZH_CONF="$PROJECT_ROOT/descriptions-zh.conf"
AGTOOLS_ROOT="$HOME/Projects/AG-Tools"
SKILLS_REFS_FILE="$AGTOOLS_ROOT/SKILLS-REFS.md"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
CODEX_SKILLS_LINK="$HOME/.codex/skills/tiga-skills"

# ── 辅助函数 ──

die() { echo "错误: $1" >&2; exit 1; }

validate_skill_name() {
  local name="$1"
  # 以 . 开头的条目会被 03-skills/* 遍历忽略；synced 与 Claude Code 在 ~/.claude/skills 下的同步目录同名
  [[ -n "$name" && "$name" != .* && "$name" != "synced" && "$name" != */* && \
    "$name" != *$'\t'* && "$name" != *$'\n'* ]] || die "无效的技能名称: $name"
}

require_no_args() { [ "$#" -eq 0 ] || die "命令不接受额外参数: $*"; }

resolve_directory() (
  cd "$1" 2>/dev/null && cd "$2" 2>/dev/null && pwd
)

# 判断 $1 是否为可解析到目录 $2 的软链接
link_resolves_to() {
  [ -L "$1" ] && [ "$(resolve_directory "$(dirname "$1")" "$(readlink "$1")")" = "$2" ]
}

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
# add 按整行去重后插入并保持表体按上游技能列排序；remove 按引用方列精确删除，无对应行时直接返回
sync_agtools_refs() {
  local action="$1" upstream="$2" consumer="$3"
  local row="| ${upstream} | ${consumer} | link |"

  if [ ! -f "$SKILLS_REFS_FILE" ]; then
    echo "⚠ 未找到 ${SKILLS_REFS_FILE}，跳过下游引用清单维护" >&2
    return
  fi
  if [ "$action" = "add" ] && grep -qxF "$row" "$SKILLS_REFS_FILE"; then
    echo "✓ 下游引用清单已存在该行，无需追加"
    return
  fi
  if [ "$action" = "remove" ] && ! grep -qF "| ${consumer} |" "$SKILLS_REFS_FILE"; then
    return
  fi

  local template rowsfile
  template="$(mktemp)"
  rowsfile="$(mktemp)"

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
    rm -f "$template" "$rowsfile"
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

  # 将排序后的表体回填到占位位置（写入原文件，保留其权限与软链接）
  awk -v rowsfile="$rowsfile" '
    $0 == "@@ROWS@@" {
      while ((getline line < rowsfile) > 0) print line
      close(rowsfile)
      next
    }
    { print }
  ' "$template" > "$SKILLS_REFS_FILE"
  rm -f "$template" "$rowsfile"

  if [ "$action" = "add" ]; then
    echo "✓ 下游引用清单已追加: $row"
  else
    echo "✓ 下游引用清单已删除引用方 ${consumer} 的行"
  fi
}

# 从 descriptions-zh.conf 读取 README 字段
lookup_readme_field() {
  local key="$1.$2="
  awk -v key="$key" 'index($0, key) == 1 { print substr($0, length(key) + 1); exit }' "$DESCRIPTIONS_ZH_CONF"
}

# 获取并校验 README 所需的中文说明
readme_description() {
  local name="$1" desc
  desc="$(lookup_readme_field "$name" "description")"
  [ -n "$desc" ] || die "descriptions-zh.conf 缺少 ${name}.description"
  printf '%s' "$desc"
}

# 获取 README 参数列内容：优先 SKILL.md 的 argument-hint，其次 descriptions-zh.conf 的 arguments 兜底
# 已转义 Markdown 表格分隔符，调用方直接输出即可
skill_arguments() {
  local name="$1" file="$2" args=""
  [ -f "$file" ] && args="$(frontmatter_field "$file" "argument-hint")"
  [ -n "$args" ] || args="$(lookup_readme_field "$name" "arguments")"
  [ -n "$args" ] || args="—"
  escape_markdown_cell "$args"
}

# 删除技能时同步清理 README 元数据
remove_readme_metadata() {
  local name="$1" tmpfile
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

# 官方允许的 frontmatter 顶层字段：Claude Code 扩展字段 + Agent Skills 开放标准字段
# 规范演进时在此处增补；未列出的键一律按拼写偏差报违规
ALLOWED_FRONTMATTER_KEYS="name description when_to_use argument-hint arguments \
disable-model-invocation user-invocable allowed-tools disallowed-tools model effort \
context agent background hooks paths shell license compatibility metadata"

# 列出 frontmatter 中的顶层键（缩进行与列表项不计入）
frontmatter_keys() {
  awk '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && match($0, /^[A-Za-z_][A-Za-z0-9_-]*:/) { print substr($0, 1, RLENGTH - 1) }
  ' "$1"
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

  local key
  while IFS= read -r key; do
    [ -n "$key" ] || continue
    [[ " $ALLOWED_FRONTMATTER_KEYS " == *" $key "* ]] || violations+=("未知 frontmatter 字段: $key")
  done < <(frontmatter_keys "$file")

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

# 根据分类名返回 README 中的来源说明文本
category_description() {
  case "$1" in
    项目级技能)     echo '位于 `.agents/skills/`，供操作本仓库使用' ;;
    superpowers)    echo "来源于 [AG-Tools/superpowers](https://github.com/Tiga08/AG-Tools)" ;;
    custom-skills)  echo '来源于 `03-skills/` 中的自定义技能目录' ;;
    *)              echo '来源于外部路径，通过 `add` 命令注册' ;;
  esac
}

# 输出 rows 文件中实际存在的分类：项目级技能 → custom-skills → superpowers → 其余字母序
skill_categories() {
  cut -f1 "$1" | sort -u | awk '
    $0 == "项目级技能" || $0 == "custom-skills" || $0 == "superpowers" { fixed[$0] = 1; next }
    { rest[++n] = $0 }
    END {
      split("项目级技能 custom-skills superpowers", order, " ")
      for (i = 1; i <= 3; i++) if (order[i] in fixed) print order[i]
      for (i = 1; i <= n; i++) print rest[i]
    }'
}

# 判断技能来源类别（用于展示分组）
# 真实目录一律归为 custom-skills；符号链接解析为绝对路径后，位于 AG-Tools 下的取其子仓库名
# 本仓库位于 AG-Tools 内，add 写入的相对目标（如 ../../superpowers/...）不含 AG-Tools 字样，因此不能只匹配链接文本
classify_source() {
  local entry="$1" resolved
  if [ ! -L "$entry" ]; then
    echo "custom-skills"
    return
  fi
  resolved="$(resolve_directory "$(dirname "$entry")" "$(readlink "$entry")")" || resolved=""
  if [[ "$resolved" == "$AGTOOLS_ROOT/"*/* ]]; then
    resolved="${resolved#"$AGTOOLS_ROOT"/}"
    echo "${resolved%%/*}"
  else
    echo "external"
  fi
}

# 向 rows 文件追加一行 "分类\t名称\t参数\t描述"（各列已转义 Markdown 表格分隔符）
append_skill_row() {
  local outfile="$1" category="$2" name="$3" skill_md="$4" desc args
  desc="$(readme_description "$name")"
  args="$(skill_arguments "$name" "$skill_md")"
  printf '%s\t%s\t%s\t%s\n' "$category" "$(escape_markdown_cell "$name")" "$args" \
    "$(escape_markdown_cell "$desc")" >> "$outfile"
}

# 遍历 $SKILLS_DIR 下所有一级条目（真实目录或符号链接），写入 rows 文件；链接健康由 check 负责
collect_skill_rows() {
  local outfile="$1" entry
  : > "$outfile"
  for entry in "$SKILLS_DIR"/*; do
    [ -L "$entry" ] || [ -d "$entry" ] || continue
    append_skill_row "$outfile" "$(classify_source "$entry")" "$(basename "$entry")" "$entry/SKILL.md"
  done
}

# ~/.claude/skills 保持为真实目录：Claude Code 会在其中写入 synced/ 等自有内容，且只扫描这一层技能目录
# 因此不整体链接到 03-skills/，而是为每个条目建立同名软链接 ~/.claude/skills/<name> -> 03-skills/<name>

# 列出 ~/.claude/skills 中指向 03-skills/ 但目标条目已不存在的链接
stale_claude_links() {
  local link target
  for link in "$CLAUDE_SKILLS_DIR"/*; do
    [ -L "$link" ] || continue
    target="$(readlink "$link")"
    [[ "$target" == "$SKILLS_DIR/"* ]] || continue
    [ -e "$target" ] || [ -L "$target" ] || echo "$link"
  done
}

# 让 ~/.claude/skills/<name> 与 03-skills/ 条目一一对应：补齐缺失链接、修正悬空的同名链接、清理失效链接
# 同名真实目录或指向别处的有效链接视为冲突，只提示不覆盖
sync_claude_skill_links() {
  if [ -L "$CLAUDE_SKILLS_DIR" ]; then
    echo "⚠ $CLAUDE_SKILLS_DIR 是软链接（旧布局），跳过技能链接同步；请删除该软链接后重新运行 $0 setup" >&2
    return
  fi
  mkdir -p "$CLAUDE_SKILLS_DIR"

  local entry link
  for entry in "$SKILLS_DIR"/*; do
    [ -L "$entry" ] || [ -d "$entry" ] || continue
    link="$CLAUDE_SKILLS_DIR/$(basename "$entry")"

    if [ -L "$link" ] && [ "$(readlink "$link")" = "$entry" ]; then
      continue
    elif [ -L "$link" ] && [ ! -e "$link" ]; then
      rm "$link"
    elif [ -e "$link" ] || [ -L "$link" ]; then
      echo "⚠ 冲突: $link 已存在且未指向 ${entry}，跳过" >&2
      continue
    fi
    ln -s "$entry" "$link"
    echo "✓ 已链接 $link -> $entry"
  done

  while IFS= read -r link; do
    rm "$link"
    echo "✓ 已清理失效链接 $link"
  done < <(stale_claude_links)
  echo "✓ $CLAUDE_SKILLS_DIR 技能链接已同步"
}

# ── setup ──

cmd_setup() {
  require_no_args "$@"
  sync_claude_skill_links

  # Codex 递归扫描 ~/.codex/skills，整目录链接即可；已存在且指向别处时不覆盖
  if link_resolves_to "$CODEX_SKILLS_LINK" "$SKILLS_DIR"; then
    echo "✓ $CODEX_SKILLS_LINK 已指向正确目标"
  elif [ -e "$CODEX_SKILLS_LINK" ] || [ -L "$CODEX_SKILLS_LINK" ]; then
    echo "⚠ $CODEX_SKILLS_LINK 已存在且未指向 ${SKILLS_DIR}，跳过；如需更新请先删除" >&2
  else
    mkdir -p "$(dirname "$CODEX_SKILLS_LINK")"
    ln -s "$SKILLS_DIR" "$CODEX_SKILLS_LINK"
    echo "✓ 已创建 $CODEX_SKILLS_LINK -> $SKILLS_DIR"
  fi
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
  [[ -e "$link" || -L "$link" ]] && die "技能 '$name' 已存在于 03-skills/"
  readme_description "$name" > /dev/null

  # 转换为可移植的相对路径后再创建软链接
  local link_target
  link_target="$(to_portable_target "$source_path")"
  ln -s "$link_target" "$link"
  echo "✓ 已添加 ${name} -> ${link_target}"

  # 来源位于 AG-Tools 时，同步登记下游引用
  if [[ "$source_path" == "$AGTOOLS_ROOT/"* ]]; then
    sync_agtools_refs add "${source_path#"$AGTOOLS_ROOT"/}" "${PROJECT_ROOT#"$HOME/Projects/"}/03-skills/$name"
  fi
  sync_claude_skill_links
  cmd_update_readme
}

# ── remove ──

cmd_remove() {
  [ "$#" -eq 1 ] || die "用法: $0 remove <name>"
  local name="$1" link
  validate_skill_name "$name"
  link="$SKILLS_DIR/$name"

  if [ -d "$link" ] && [ ! -L "$link" ]; then
    die "'$name' 是自定义技能（真实目录），不支持通过脚本删除；请手动处理"
  fi
  [ -L "$link" ] || die "未找到技能 '$name'"

  rm "$link"
  remove_readme_metadata "$name"
  echo "✓ 已移除 $name"

  # 下游引用按引用方列删除，无需解析链接目标（目标可能已失效）；非 AG-Tools 来源没有对应行
  sync_agtools_refs remove "" "${PROJECT_ROOT#"$HOME/Projects/"}/03-skills/$name"
  sync_claude_skill_links
  cmd_update_readme
}

# ── list ──

cmd_list() {
  require_no_args "$@"
  local rowsfile category
  rowsfile="$(mktemp)"
  collect_skill_rows "$rowsfile"

  while IFS= read -r category; do
    echo "[$category]"
    awk -F'\t' -v c="$category" '$1 == c { printf "  %-35s %s\n", $2, $4 }' "$rowsfile"
    echo ""
  done < <(skill_categories "$rowsfile")

  echo "共 $(wc -l < "$rowsfile" | tr -d ' ') 个技能"
  rm -f "$rowsfile"
}

# ── check ──

cmd_check() {
  require_no_args "$@"
  local ok=0 bad=0
  item_ok() { echo "  ✓ $1"; ok=$((ok + 1)); }
  item_bad() { echo "  ✗ $1"; bad=$((bad + 1)); }

  echo "检查 03-skills/ 技能目录:"
  local entry name label skill_root
  for entry in "$SKILLS_DIR"/*; do
    [ -L "$entry" ] || [ -d "$entry" ] || continue
    name="$(basename "$entry")"
    label="$name"
    skill_root="$entry"
    if [ -L "$entry" ]; then
      label="${name} -> $(readlink "$entry")"
      skill_root="$(resolve_directory "$SKILLS_DIR" "$(readlink "$entry")")" || skill_root=""
    fi

    if [ -z "$skill_root" ]; then
      item_bad "${label}（目标无法解析）"
    elif [ ! -f "$skill_root/SKILL.md" ]; then
      item_bad "${label}（缺少 SKILL.md）"
    elif [[ "$skill_root" != "$PROJECT_ROOT/"* ]]; then
      item_ok "${label}（外部源，跳过 frontmatter 校验）"
    else
      check_skill_frontmatter "$skill_root/SKILL.md" "$name" "$label" && ok=$((ok + 1)) || bad=$((bad + 1))
    fi
  done

  echo ""
  echo "检查项目级技能 (.agents/skills/):"
  local skill_dir
  for skill_dir in "$PROJECT_ROOT/.agents/skills"/*/; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"
    if [ -f "${skill_dir}SKILL.md" ]; then
      check_skill_frontmatter "${skill_dir}SKILL.md" "$name" "$name" && ok=$((ok + 1)) || bad=$((bad + 1))
    else
      item_bad "${name}（缺少 SKILL.md）"
    fi
  done

  echo ""
  echo "检查项目级链接:"
  local plink
  for plink in "$PROJECT_ROOT/.claude/skills" "$PROJECT_ROOT/.codex/skills"; do
    label="${plink#"$PROJECT_ROOT"/}"
    if link_resolves_to "$plink" "$PROJECT_ROOT/.agents/skills"; then
      item_ok "${label} -> $(readlink "$plink")"
    else
      item_bad "${label}（应为指向 .agents/skills 的软链接）"
    fi
  done

  # 根目录 SKILLS-REFS.md 应为软链接且可解析到 AG-Tools 下游引用清单
  local srefs="$PROJECT_ROOT/SKILLS-REFS.md"
  if [ -L "$srefs" ] && [ "$srefs" -ef "$SKILLS_REFS_FILE" ]; then
    item_ok "SKILLS-REFS.md -> $(readlink "$srefs")"
  else
    item_bad "SKILLS-REFS.md（应为指向 ${SKILLS_REFS_FILE} 的软链接）"
  fi

  echo ""
  echo "检查用户级链接:"
  if [ -L "$CLAUDE_SKILLS_DIR" ] || [ ! -d "$CLAUDE_SKILLS_DIR" ]; then
    item_bad "~/.claude/skills（应为真实目录；若是软链接请删除后运行 setup）"
  else
    local link
    for entry in "$SKILLS_DIR"/*; do
      [ -L "$entry" ] || [ -d "$entry" ] || continue
      name="$(basename "$entry")"
      link="$CLAUDE_SKILLS_DIR/$name"
      if [ -L "$link" ] && [ "$(readlink "$link")" = "$entry" ]; then
        item_ok "~/.claude/skills/${name}"
      else
        item_bad "~/.claude/skills/${name}（缺失或未指向 03-skills/${name}，请运行 setup）"
      fi
    done
    while IFS= read -r link; do
      item_bad "~/.claude/skills/$(basename "$link") -> $(readlink "$link")（目标已不存在，请运行 setup 清理）"
    done < <(stale_claude_links)
  fi

  if link_resolves_to "$CODEX_SKILLS_LINK" "$SKILLS_DIR"; then
    item_ok "~/.codex/skills/tiga-skills -> $(readlink "$CODEX_SKILLS_LINK")"
  else
    item_bad "~/.codex/skills/tiga-skills（缺失或未指向 03-skills/，请运行 setup）"
  fi

  echo ""
  echo "共检查 $((ok + bad)) 项：$ok 正常，$bad 失效"
  [ "$bad" -eq 0 ] || exit 1
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

  local tmpfile tablefile rowsfile skill_dir category
  tmpfile="$(mktemp)"
  tablefile="$(mktemp)"
  rowsfile="$(mktemp)"
  collect_skill_rows "$rowsfile"
  for skill_dir in "$PROJECT_ROOT/.agents/skills"/*/; do
    [ -f "${skill_dir}SKILL.md" ] || continue
    append_skill_row "$rowsfile" "项目级技能" "$(basename "$skill_dir")" "${skill_dir}SKILL.md"
  done

  # 每个分类输出一张表格
  while IFS= read -r category; do
    echo "### $category"
    echo ""
    category_description "$category"
    echo ""
    echo "| 名称 | 参数 | 描述 |"
    echo "| ---- | ---- | ---- |"
    awk -F'\t' -v c="$category" '$1 == c { print "| " $2 " | " $3 " | " $4 " |" }' "$rowsfile"
    echo ""
  done < <(skill_categories "$rowsfile") > "$tablefile"

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
  setup                          配置用户级链接 (~/.claude/skills/<name> → 逐个技能链接, ~/.codex/skills/tiga-skills → 目录链接)
  add <path> [--name <name>]     从外部路径添加技能符号链接到 03-skills/
  remove <name>                  按名称移除技能符号链接（仅限外部技能）
  list                           按来源分组列出已注册技能
  check                          检查技能目录、项目级链接与用户级链接的健康状态
  update-readme                  更新 README.md 技能清单（按来源分组）
EOF
}

# ── 主入口 ──

cmd="${1:-}"
shift || true

case "$cmd" in
  setup)        cmd_setup "$@" ;;
  add)          cmd_add "$@" ;;
  remove)       cmd_remove "$@" ;;
  list)         cmd_list "$@" ;;
  check)        cmd_check "$@" ;;
  update-readme) cmd_update_readme "$@" ;;
  *)
    print_usage
    exit 1
    ;;
esac
