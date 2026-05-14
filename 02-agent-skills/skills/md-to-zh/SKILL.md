---
name: md-to-zh
description: Translate English Markdown files into Simplified Chinese (.zh.md)
---

Translate English Markdown files into Simplified Chinese, writing the output alongside the source.

**Arguments:** One or more paths separated by spaces. Each path may be a directory or a single `.md` file, mixed freely. Flags `--dry-run` and `--force` may appear anywhere in the argument list.

- `--dry-run`: List all files that would be translated without writing anything.
- `--force`: Overwrite all existing `.zh.md` files without conflict prompts.

**No-argument behavior:** If no arguments and no flags are provided, scan the project root for `.md` files. If any are found, use `AskUserQuestion` to offer translating them (list the files found). If none are found, tell the user and stop.

**Path resolution:**
- Trim leading and trailing whitespace from each path argument.
- Paths starting with `/` or `~` are absolute (`~` must be expanded to the home directory).
- All other paths are relative to the current project root directory.
- If a path is a symbolic link, resolve it to its target. Skip if the target does not exist or if the resolved target is already in the translation list.
- For each path, determine its type:
  - File: must end with `.md`, otherwise report an error and skip it.
  - Directory: use `find <dir> -name '*.md' -type f` to recursively collect all `.md` files. Each output file is written next to its source, not at the root of the passed-in directory.
  - Does not exist: report an error and skip it.

**Filtering:** Before translating, exclude:
- Files whose names already end with `.zh.md` (already translated).
- Files whose names end with `-zh.md` (legacy Chinese naming convention).
- Empty files (0 bytes): skip with a note.
- Files where prose content is >80% CJK characters: skip as "already in Chinese".

**Output naming:** `foo.md` in the same directory becomes `foo.zh.md`.

**Conflict handling:**
- If `--force` is set, overwrite all existing `.zh.md` files without prompting.
- If `--dry-run` is set, just list what would happen (including conflicts) without writing.
- Otherwise, if `foo.zh.md` already exists, use `AskUserQuestion` to ask the user:
  - Overwrite this file
  - Skip this file
  - Overwrite all remaining conflicts
  - Skip all remaining conflicts

Apply the chosen action accordingly.

**Translation rules:**
- Preserve all Markdown formatting exactly: headings, tables, code blocks, bold, italics, links, etc.
- Do NOT translate: file paths, directory names, command names, code identifiers, skill names, URLs.
- Do NOT translate content inside: `[[wiki-links]]`, `{{template-vars}}`, `:::admonition` markers, `{% liquid-tags %}`.
- YAML frontmatter handling: translate user-facing string values (e.g., `description`, `when_to_use`). Preserve keys, booleans, numbers, tool names, file paths, and machine-readable identifiers (e.g., `name: write` stays as-is).
- Translate all English prose, table headers, descriptions, and inline comments into natural, fluent Simplified Chinese.
- Technical terms may retain their English form or include a Chinese annotation in parentheses on first use.
- The output file must be complete and standalone: no preamble, no explanation, just the translated content.

**Progress indication:** Before each file, print `[N/Total] Translating <relative-path> ...`. After writing, print confirmation.

**Execution flow:**
1. Parse arguments: extract flags (`--dry-run`, `--force`) and paths. Trim whitespace from paths.
2. Resolve symbolic links. Validate all paths (files and directories, mixed). Report any invalid paths upfront.
3. Build the full list of files to translate (use `find` for directories). Apply all filters.
4. Show the user a summary: total count and file paths (display relative paths where possible, grouped by directory).
5. If `--dry-run`, print the file list with conflict annotations and stop here.
6. Translate each file one by one with progress indication, writing `foo.zh.md` next to the source. Handle conflicts per the conflict-handling rules.
7. When done, print a final summary: succeeded / skipped / failed.
