---
name: md-to-zh
description: Translate English Markdown files or directories into Simplified Chinese, preserving structure line by line; existing translations update incrementally from changed lines only, and unchanged files are skipped at zero cost. Governance files (AGENTS.md / CLAUDE.md) get sibling .zh.md files; other files go to .tiga/translations/. Use when creating or refreshing Chinese versions of any Markdown document.
description_zh: 将英文 Markdown 文件或目录翻译为简体中文，逐行保留文档结构；已有译文仅按变动行增量更新，未变更的文件零成本跳过。治理文件（AGENTS.md / CLAUDE.md）在源文件旁生成 .zh.md，其余文件输出到 .tiga/translations/。适用于为任何 Markdown 文档新建或刷新中文版本。
---

Translate English Markdown files into Simplified Chinese.

**Arguments:** One or more paths separated by spaces. Each path may be a directory or a single `.md` file, mixed freely. Flags `--force` and `--output <dir>` may appear anywhere in the argument list.

- `--force`: Force full re-translation of every file, overwriting existing translations and bypassing the incremental-update logic.
- `--output <dir>`: Specify the output directory for translated files. Default: `.tiga/translations` (relative to project root). Does not affect governance files — see the output rules in Phase 2.

**No-argument behavior:** If no path is provided, tell the user that at least one file or directory path is required, then stop. Do not scan the project for files and do not ask any questions.

## Workflow

### Phase 1: Parse Arguments & Resolve Paths

1. Extract flags (`--force`, `--output <dir>`); treat all remaining arguments as paths.
2. Resolve each path:
   - Trim leading and trailing whitespace from each path argument.
   - Paths starting with `/` or `~` are absolute (`~` must be expanded to the home directory).
   - All other paths are relative to the current project root directory.
   - If a path is a symbolic link, resolve it to its target. Skip if the target does not exist or if the resolved target is already in the translation list.
3. Determine each path's type:
   - File: must end with `.md`, otherwise report an error and skip it.
   - Directory: use `find <dir> -name '*.md' -type f` to recursively collect all `.md` files.
   - Does not exist: report an error and skip it.
4. Report all invalid paths upfront, before any translation work starts.

### Phase 2: Filter & Build Translation Plan

1. **Filter.** Exclude from the collected file list:
   - Files whose names already end with `.zh.md` (already translated).
   - Files whose names end with `-zh.md` (legacy Chinese naming convention).
   - Empty files (0 bytes): skip with a note.
   - Files where prose content is >80% CJK characters: skip as "already in Chinese".
2. **Compute each file's output path** per these output rules:
   - **Governance files** (`AGENTS.md`, `CLAUDE.md`): write the translation as `.zh.md` next to the source file (e.g., `AGENTS.md` → `AGENTS.zh.md` in the same directory). This rule takes precedence over `--output`: even when `--output` is given, governance files still go next to their source; `--output` only affects non-governance files.
   - **All other files**: write to the output directory (`--output` value or default `.tiga/translations/`).
     - Naming convention: `{immediate-parent-dir}-{filename}.md`. Use the immediate parent directory name as a prefix, joined by `-`, keeping the `.md` extension.
     - Example: `03-custom-skills/gen-governance/SKILL.md` → `.tiga/translations/gen-governance-SKILL.md`.
     - If the source file is directly in the project root (no parent directory), use the filename as-is (e.g., `README.md` → `.tiga/translations/README.md`).
3. Ensure the output directory exists (create it if needed).
4. Show the user a summary: total count N, and each source → output mapping (display relative paths, grouped by directory).

### Phase 3: Translate Files

Process files one by one. Before each file, print `[k/N] Translating <relative-path> → <output-path> ...`.

Dispatch for each source file:

- Target translation does not exist → full translation, following the Translation rules below.
- `--force` is set → skip the incremental check and unconditionally re-translate the full file, overwriting the target.
- Target translation exists → run the incremental update flow below.

**Incremental update flow:**

1. **Determine the translation's baseline time.** If the translation file is git-tracked and has no uncommitted modifications, use `git log -1 --format=%ai -- <translation>`. If it is untracked (e.g., the default output directory `.tiga/translations/` is git-ignored) or has uncommitted modifications, use the file's mtime (`stat`).
2. **Decide whether the source changed.** Combine `git status` (uncommitted modifications) and `git log` (commits after the baseline time) to determine whether the source file changed after the baseline time. If it did not change → print "already up to date" and skip; no translation tokens are spent.
3. **Line-count consistency check.** Compare the total line counts of the source document and the translation. The translation rules preserve Markdown structure line by line, so the mapping "source line N ↔ translation line N" is considered reliable only when the counts match.
4. **Locate changed lines.** Take the last commit that touched the source file before the baseline time as the base, then run `git diff <base> -- <source>` to obtain the changed hunks (this automatically includes uncommitted modifications).
5. **Translate incrementally.** Translate only the lines inside the changed hunks, consulting the hunk context lines to keep terminology and style consistent, and use Edit to replace the corresponding lines in the translation at the same line numbers. For added or removed lines, insert into or delete from the translation following the hunk's line offsets.

**Fallback conditions** — if any of these holds, re-translate the full file and overwrite the target, stating the fallback reason in the output:

- Source and translation line counts differ.
- The source file is not git-tracked.
- The base commit cannot be determined, or the diff result is unusable.

After processing each file, print its resulting status, one of:

- New translation
- Incremental update (N lines)
- Already up to date (skipped)
- Full re-translation (with the fallback reason, or `--force`)

**Failure handling:** If a single file fails for any reason (read error, write error, etc.), record the failure reason and continue with the next file — never abort the whole batch.

### Phase 4: Summary

Print a final summary counting files by status: new translation / incremental update / already up to date / full re-translation / failed (with recorded reasons), with the output directory path.

## Translation rules

- Preserve all Markdown formatting exactly: headings, tables, code blocks, bold, italics, links, etc.
- Do NOT translate: file paths, directory names, command names, code identifiers, skill names, URLs.
- Do NOT translate content inside: `[[wiki-links]]`, `{{template-vars}}`, `:::admonition` markers, `{% liquid-tags %}`.
- YAML frontmatter handling: translate user-facing string values (e.g., `description`, `when_to_use`). Preserve keys, booleans, numbers, tool names, file paths, and machine-readable identifiers (e.g., `name: write` stays as-is).
- Translate all English prose, table headers, descriptions, and inline comments into natural, fluent Simplified Chinese.
- Technical terms may retain their English form or include a Chinese annotation in parentheses on first use.
- The output file must be complete and standalone: no preamble, no explanation, just the translated content.
