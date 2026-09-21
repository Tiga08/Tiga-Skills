---
name: tiga-translate
description: "Translate Markdown files or directories into Simplified Chinese after assessing what needs translation and route outputs by document type. Invoke explicitly only."
argument-hint: "<path...>"
disable-model-invocation: true
---

Translate English Markdown files or directories into Simplified Chinese.

**Arguments:** One or more paths. Preserve shell-style quoting so a path containing spaces remains one argument. Each path may be a directory or a single `.md` file, mixed freely. 本次调用参数：`$ARGUMENTS`

**No-argument behavior:** If no path is provided, tell the user that at least one file or directory path is required, then stop. Do not scan the project for files and do not ask any questions.

## Workflow

### Phase 1: Parse Arguments & Resolve Paths

1. Treat every parsed argument as a path — there are no flags to extract. If the host exposes only raw `$ARGUMENTS`, split it with shell-style quote handling rather than on whitespace alone.
2. Resolve each path:
   - Trim leading and trailing whitespace from each path argument.
   - Paths starting with `/` or `~` are absolute (`~` must be expanded to the home directory).
   - All other paths are relative to the current project root directory.
   - If a path is a symbolic link, resolve it to its target. Skip if the target does not exist or if the resolved target is already in the translation list.
3. Determine each path's type:
   - File: must end with `.md`, otherwise report an error and skip it.
   - Directory: use `find "<dir>" -name '*.md' -type f` to recursively collect all `.md` files, and record the directory's own basename (trailing slashes trimmed) for the output rule below.
   - Does not exist: report an error and skip it.
4. Deduplicate collected files by resolved source path. If the same file was both passed directly and discovered through a directory argument, keep the directory-derived entry so it follows the directory-mirroring output rule.
5. Report all invalid or duplicate paths upfront, before any translation work starts.

### Phase 2: Assess Need & Build the Translation Plan

1. **Filter.** Exclude from the collected file list, each with a one-line reason:
   - Files whose names already end with `.zh.md` (already translated).
   - Files whose names end with `-zh.md` (legacy Chinese naming convention).
   - Empty files (0 bytes).
   - Files where prose content is >80% CJK characters ("already in Chinese").
2. **Compute each remaining file's output path**, in this precedence order:
   - **Governance files** (`AGENTS.md`, `CLAUDE.md`), wherever encountered — including nested inside a directory argument being recursed — always go to a sibling `.zh.md` next to the source (e.g., `AGENTS.md` → `AGENTS.zh.md`). This precedes the directory-mirroring rule below.
   - **A single document** — a non-governance `.md` file passed directly as an argument (not reached via directory recursion) — goes flat under `.tiga/translations/`, same filename with `.zh` inserted before the extension (e.g., `README.md` → `.tiga/translations/README.zh.md`).
   - **A directory argument's contents** — every non-governance `.md` file found while recursing a directory mirrors that file's path relative to the directory under `.tiga/translations/<dir-basename>/`, with `.zh` inserted before each file's extension. `<dir-basename>` is the last path segment of the directory argument as given. Example: directory `03-skills/tiga-translate` → `.tiga/translations/tiga-translate/SKILL.zh.md`; directory `.agents/skills/tiga-global-skills` → `.tiga/translations/tiga-global-skills/SKILL.zh.md` and `.tiga/translations/tiga-global-skills/references/operations.zh.md`.
3. Detect output collisions before translation. If distinct sources map to the same target (for example, two directory arguments with the same basename), report every conflicting source and skip that target instead of overwriting it.
4. **Assess translation need for each remaining file** — must happen before any translation starts; its result is the plan Phase 3 executes:
   - Target output file does not exist → needs a **new translation**.
   - Target output file exists → determine the translation's **baseline**:
     - If the translation is git-tracked with no uncommitted modifications, record the commit that last changed it with `git log -1 --format=%H -- <translation>`.
     - If the translation is untracked (e.g. `.tiga/translations/` is git-ignored) or has uncommitted modifications, record its mtime with `stat`.
   - Compare the source with that baseline. For a commit baseline, use `git diff <baseline-commit> -- <source>` so committed, staged, and unstaged changes are all included. For an mtime baseline, compare the source and translation mtimes; commit timestamps are not a safe substitute because committing does not change the source-file mtime. Unchanged → **already up to date**. Changed → needs an **incremental update**; carry the baseline data forward to Phase 3.
5. Ensure every output directory used by the plan exists (create as needed).
6. **Report the plan before translating anything**: total candidate count, how many need a new translation, how many need an incremental update, how many are already up to date, and the skipped-with-reason list from steps 1 and 3. Group source → output mappings by directory using relative paths.

### Phase 3: Translate

Process only the files the Phase 2 plan marked as needing a new or incremental translation, one by one, in the order reported. Before each file, print `[k/N] Translating <relative-path> → <output-path> ...` (N = the needs-translation count).

Dispatch per the Phase 2 classification:

- **New translation** → translate the full file, following the Translation rules below.
- **Incremental update** → run the incremental update flow below, reusing the baseline data computed in Phase 2 step 4.

**Incremental update flow:**

1. **Reconstruct the baseline source.** For a clean, tracked translation, use its recorded baseline commit. For an mtime baseline with uncommitted source changes, use `HEAD` as the candidate base only when the translation mtime is later than the source mtime cached by `git ls-files --debug -- <source>`; otherwise the base cannot be established safely, so use the full re-translation fallback. Read the source snapshot at the selected commit with `git show <base>:<repo-relative-source>`.
2. **Line-count consistency check.** Compare the total line counts of the baseline source snapshot and the existing translation. The mapping "baseline source line N ↔ translation line N" is reliable only when the counts match; comparing the current source would incorrectly reject valid added or removed lines.
3. **Locate changed lines.** Run `git diff <base> -- <source>` to obtain the changed hunks; this includes committed, staged, and unstaged changes after the baseline.
4. **Translate incrementally.** Translate only the lines inside the changed hunks, consulting hunk context to keep terminology and style consistent, and edit the corresponding translation lines. For added or removed lines, insert into or delete from the translation following the hunk offsets. Stay consistent with renderings already used elsewhere in the existing translation.

**Fallback conditions** — if any holds, re-translate the full file and overwrite the target, stating the fallback reason (there is no override flag anymore; these conditions are the only trigger for a full re-translation of an existing target):

- The baseline source snapshot and translation line counts differ.
- The source file is not git-tracked.
- The base commit cannot be determined, or the diff result is unusable.

After each file, print its status: New translation / Incremental update (N lines) / Full re-translation (with reason).

**Failure handling:** a single file's failure is recorded and the batch continues.

### Phase 4: Summary

Print a final summary counting files by status: new translation / incremental update / already up to date / full re-translation / failed (with reasons), with the output paths used.

## Translation rules

- Preserve all Markdown formatting exactly: headings, tables, code blocks, bold, italics, links, etc.
- Do NOT translate: file paths, directory names, command names, code identifiers, skill names, URLs.
- Do NOT translate content inside: `[[wiki-links]]`, `{{template-vars}}`, `:::admonition` markers, `{% liquid-tags %}`.
- YAML frontmatter handling: translate user-facing string values (e.g., `description`, `when_to_use`). Preserve keys, booleans, numbers, tool names, file paths, and machine-readable identifiers.
- Translate all English prose, table headers, descriptions, and inline comments into natural, fluent Simplified Chinese.
- **Rewrite within the line, not word-for-word**: each translated line should read as if a native Chinese writer composed it from scratch.
- **Accuracy first**: facts, data, and logic must match the source exactly.
- **Avoid translationese (欧化中文)**: no overused connectives (因此/然而/此外), no passive-voice abuse (被/由/受到), no noun pile-ups.
- **Never break the line mapping**: never split or merge lines — incremental updates depend on the "source line N ↔ translation line N" mapping.
- **Terminology consistency**: translate a repeated term the same way every time it appears; for an incremental update, match the rendering already used in the existing translation.
- The output file must be complete and standalone: no preamble, no explanation, just the translated content.
