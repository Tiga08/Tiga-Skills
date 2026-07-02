---
name: md-to-zh
description: Translate English Markdown files into Simplified Chinese, with incremental updates of existing translations based on changed lines
description_zh: 将英文 Markdown 文件翻译为简体中文，支持对已有译文按变动行增量更新
---

Translate English Markdown files into Simplified Chinese.

**Arguments:** One or more paths separated by spaces. Each path may be a directory or a single `.md` file, mixed freely. Flags `--force` and `--output <dir>` may appear anywhere in the argument list.

- `--force`: Force full re-translation of every file, overwriting existing translations and bypassing the incremental-update logic.
- `--output <dir>`: Specify the output directory for translated files. Default: `agent-plan/translations` (relative to project root).

**No-argument behavior:** If no arguments and no flags are provided, scan the project root for `.md` files. If any are found, use `AskUserQuestion` to offer translating them (list the files found). If none are found, tell the user and stop.

**Output rules:**

- **Governance files** (`AGENTS.md`, `CLAUDE.md`): write the translation as `.zh.md` next to the source file (e.g., `AGENTS.md` → `AGENTS.zh.md` in the same directory).
- **All other files**: write to the output directory (`--output` value or default `agent-plan/translations/`). Create the directory if it does not exist.
  - Naming convention: `{immediate-parent-dir}-{filename}.md`. Use the immediate parent directory name as a prefix, joined by `-`, keeping the `.md` extension.
  - Example: `03-custom-skills/gen-governance/SKILL.md` → `agent-plan/translations/gen-governance-SKILL.md`.
  - If the source file is directly in the project root (no parent directory), use the filename as-is (e.g., `README.md` → `agent-plan/translations/README.md`).

**Path resolution:**
- Trim leading and trailing whitespace from each path argument.
- Paths starting with `/` or `~` are absolute (`~` must be expanded to the home directory).
- All other paths are relative to the current project root directory.
- If a path is a symbolic link, resolve it to its target. Skip if the target does not exist or if the resolved target is already in the translation list.
- For each path, determine its type:
  - File: must end with `.md`, otherwise report an error and skip it.
  - Directory: use `find <dir> -name '*.md' -type f` to recursively collect all `.md` files.
  - Does not exist: report an error and skip it.

**Filtering:** Before translating, exclude:
- Files whose names already end with `.zh.md` (already translated).
- Files whose names end with `-zh.md` (legacy Chinese naming convention).
- Empty files (0 bytes): skip with a note.
- Files where prose content is >80% CJK characters: skip as "already in Chinese".

**Incremental update:**

Dispatch for each source file:
- Target translation does not exist → full translation (existing behavior, unchanged).
- `--force` is set → skip the incremental check and unconditionally re-translate the full file, overwriting the target.
- Target translation exists → run the incremental update flow below.

Incremental update flow:

1. **Determine the translation's baseline time.** If the translation file is git-tracked and has no uncommitted modifications, use `git log -1 --format=%ai -- <translation>`. If it is untracked (e.g., the default output directory `agent-plan/translations/` is git-ignored) or has uncommitted modifications, use the file's mtime (`stat`).
2. **Decide whether the source changed.** Combine `git status` (uncommitted modifications) and `git log` (commits after the baseline time) to determine whether the source file changed after the baseline time. If it did not change → print "already up to date" and skip; no translation tokens are spent.
3. **Line-count consistency check.** Compare the total line counts of the source document and the translation. The translation rules preserve Markdown structure line by line, so the mapping "source line N ↔ translation line N" is considered reliable only when the counts match.
4. **Locate changed lines.** Take the last commit that touched the source file before the baseline time as the base, then run `git diff <base> -- <source>` to obtain the changed hunks (this automatically includes uncommitted modifications).
5. **Translate incrementally.** Translate only the lines inside the changed hunks, consulting the hunk context lines to keep terminology and style consistent, and use Edit to replace the corresponding lines in the translation at the same line numbers. For added or removed lines, insert into or delete from the translation following the hunk's line offsets.

Fallback conditions — if any of these holds, re-translate the full file and overwrite the target, stating the fallback reason in the output:
- Source and translation line counts differ.
- The source file is not git-tracked.
- The base commit cannot be determined, or the diff result is unusable.

**Translation rules:**
- Preserve all Markdown formatting exactly: headings, tables, code blocks, bold, italics, links, etc.
- Do NOT translate: file paths, directory names, command names, code identifiers, skill names, URLs.
- Do NOT translate content inside: `[[wiki-links]]`, `{{template-vars}}`, `:::admonition` markers, `{% liquid-tags %}`.
- YAML frontmatter handling: translate user-facing string values (e.g., `description`, `when_to_use`). Preserve keys, booleans, numbers, tool names, file paths, and machine-readable identifiers (e.g., `name: write` stays as-is).
- Translate all English prose, table headers, descriptions, and inline comments into natural, fluent Simplified Chinese.
- Technical terms may retain their English form or include a Chinese annotation in parentheses on first use.
- The output file must be complete and standalone: no preamble, no explanation, just the translated content.

**Progress indication:** Before each file, print `[N/Total] Translating <relative-path> → <output-path> ...`. After processing, print the file's resulting status, one of:
- New translation
- Incremental update (N lines)
- Already up to date (skipped)
- Full re-translation (with the fallback reason, or `--force`)

**Execution flow:**
1. Parse arguments: extract flags (`--force`, `--output`) and paths. Trim whitespace from paths.
2. Resolve symbolic links. Validate all paths (files and directories, mixed). Report any invalid paths upfront.
3. Build the full list of source files to translate (use `find` for directories). Apply all filters.
4. Compute each file's output path per the output rules. Ensure the output directory exists (create if needed).
5. Show the user a summary: total count, each source → output mapping (display relative paths, grouped by directory).
6. Process each file one by one with progress indication, following the dispatch logic in "Incremental update": full translation for new targets, incremental update / up-to-date skip / fallback full re-translation for existing targets, unconditional full re-translation with `--force`. Write results to the computed output paths.
7. Print a final summary counting files by status: new translation / incremental update / already up to date / full re-translation / failed, with the output directory path.
