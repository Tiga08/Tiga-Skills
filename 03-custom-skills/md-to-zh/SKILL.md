---
name: md-to-zh
description: Translate English Markdown files into Simplified Chinese
---

Translate English Markdown files into Simplified Chinese.

**Arguments:** One or more paths separated by spaces. Each path may be a directory or a single `.md` file, mixed freely. Flags `--force` and `--output <dir>` may appear anywhere in the argument list.

- `--force`: Overwrite all existing translation files without conflict prompts.
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
- Files already present in the output directory with the same target name: treated as conflict (see below).

**Conflict handling:**
- If `--force` is set, overwrite all existing translation files without prompting.
- Otherwise, if the target output file already exists, use `AskUserQuestion` to ask the user:
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

**Progress indication:** Before each file, print `[N/Total] Translating <relative-path> → <output-path> ...`. After writing, print confirmation.

**Execution flow:**
1. Parse arguments: extract flags (`--force`, `--output`) and paths. Trim whitespace from paths.
2. Resolve symbolic links. Validate all paths (files and directories, mixed). Report any invalid paths upfront.
3. Build the full list of source files to translate (use `find` for directories). Apply all filters.
4. Compute each file's output path per the output rules. Ensure the output directory exists (create if needed).
5. Show the user a summary: total count, each source → output mapping (display relative paths, grouped by directory).
6. Translate each file one by one with progress indication. Handle conflicts per the conflict-handling rules. Write each translation to its computed output path.
7. Print a final summary: succeeded / skipped / failed, with the output directory path.
