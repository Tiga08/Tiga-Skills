---
name: check-docs
description: Audit governance docs (README.md, CLAUDE.md, AGENTS.md, docs/) against actual repository state, reporting phantom paths, undocumented content, stale references, and cross-document contradictions; with --fix, interactively apply fixes and sync Chinese translations of governance files. Use when docs may have drifted after code or structure changes, or to verify documentation accuracy before a commit or PR.
description_zh: 对照仓库实际状态审计治理文档（README.md、CLAUDE.md、AGENTS.md、docs/），报告失效路径、未记录内容、过期引用与文档间矛盾；--fix 可交互式应用修复并同步治理文件的中文翻译。适用于代码或目录结构变更后怀疑文档过期，或在提交 / PR 前核对文档准确性。
---

Check whether governance documents are consistent with the actual repository state, and report actionable findings.

**Arguments:** Optional flags may appear in the argument list.

- `--scope <file>`: Limit the check to specific governance files (e.g., `--scope README.md`, `--scope docs/guide.md`). May be repeated.
- `--fix`: After reporting, apply fixes to the discovered issues (Phase 6) and sync governance-file translations (Phase 7).
- `--verbose`: Show `[OK]` entries for checks that pass.

**No-argument behavior:** Scan the current repository root for governance documents (`README.md`, `CLAUDE.md`, `AGENTS.md`, any `AGENTS.md` or `CLAUDE.md` in subdirectories, and all `.md` files under `docs/`). The `docs/` directory may not exist; if absent, skip it silently without reporting an error. Run all phases against every governance file found.

## Workflow

### Phase 1: Discovery

Gather the raw inputs needed for all subsequent checks.

1. **Locate governance documents.** Find all files matching `README.md`, `CLAUDE.md`, `AGENTS.md` (root and subdirectories), plus all `.md` files under `docs/` (skip silently if the directory does not exist). If `--scope` is set, keep only the specified files.
2. **Capture the directory tree.** Run `find . -not -path './.git/*' -not -path './node_modules/*'` (or equivalent) to build the current file/directory listing. Respect `.gitignore` where practical.
3. **Capture the git timeline.** For each governance document, run `git log -1 --format='%H %ai' -- <file>` to get its last-modified commit and date. Also collect the set of paths modified since that commit: `git diff --name-only <commit>..HEAD`.

Print a brief summary: how many governance files found, their last-modified dates.

### Phase 2: Structural Alignment

Compare what the documents describe against what actually exists.

For each governance document:

1. **Extract referenced paths.** Parse the document for file paths, directory names, and shell commands. Look in:
   - Markdown tables (especially `| Directory | Purpose |` style)
   - Code blocks (especially `bash` fenced blocks)
   - Inline code spans referencing paths (e.g., `` `03-custom-skills/` ``)
   - Link targets (e.g., `[text](path/file.md)`)

2. **Verify each referenced path exists.** Check files and directories against the actual tree from Phase 1.
   - Mark as `[PHANTOM]` if the path does not exist.

3. **Detect unreferenced content.** For structural documents (README, AGENTS.md) that enumerate directories or skills:
   - Compare the listed items against actual items in the relevant directory.
   - Mark as `[MISSING]` if an actual item is not documented.

4. **Verify shell commands.** For commands referenced in the document (e.g., in a "Common Commands" section):
   - Check that referenced scripts exist and are executable.
   - Mark as `[PHANTOM]` if the script does not exist.

### Phase 3: Staleness Detection

Identify content that exists but may be outdated.

For each governance document:

1. Using the git timeline from Phase 1, identify paths that:
   - Are referenced in the document, AND
   - Have been modified after the document's last edit.

2. For each such path, check whether the modification is semantically relevant:
   - File renamed or moved → `[STALE]`
   - File content changed significantly → `[STALE]`
   - Only formatting/whitespace changes → skip

3. Check version numbers, dates, or counts mentioned in the document against current values.

### Phase 4: Cross-Document Consistency

Check that governance documents do not contradict each other.

1. **Directory descriptions.** If multiple documents describe the same directory, verify descriptions are compatible (not identical — just non-contradictory).
2. **Instruction conflicts.** Check for rules in one document that contradict rules in another (e.g., CLAUDE.md says "never X" while AGENTS.md says "always X").
3. **Structural overlap.** If both README.md and AGENTS.md list directory tables, verify they agree on which directories exist and their stated purposes.

Mark contradictions as `[MISMATCH]`.

### Phase 5: Report

Output all findings grouped by severity, then by source document.

**Report format:**

```
## Audit Report

### [PHANTOM] — References to non-existent content
- README.md (line ~N): references `path/that/does-not-exist`
  → Suggested fix: remove the reference or create the missing content

### [MISSING] — Undocumented content
- `03-custom-skills/gen-governance/` exists but is not listed in README.md skill table
  → Suggested fix: add entry to the skill list table

### [STALE] — Outdated references
- CLAUDE.md (line ~N): references `04-scripts/old-script.sh`, last modified 30 days after CLAUDE.md
  → Suggested fix: review and update the reference

### [MISMATCH] — Cross-document contradictions
- README.md says "directory X does Y" but AGENTS.md says "directory X does Z"
  → Suggested fix: align the descriptions

### Summary
- N PHANTOM findings
- N MISSING findings
- N STALE findings
- N MISMATCH findings
- N checks passed
```

**Priority order for suggested fixes:** `[PHANTOM]` > `[MISSING]` > `[STALE]` > `[MISMATCH]`.

If `--verbose` is set, append a section listing all `[OK]` checks that passed.

### Phase 6: Fix Application

Apply the reported fixes interactively.

**Trigger condition:** `--fix` is set AND there is at least one finding. If not triggered, print why this phase is skipped (no `--fix`, or no findings) and continue to Phase 7.

1. Iterate through findings in priority order (`[PHANTOM]` > `[MISSING]` > `[STALE]` > `[MISMATCH]`).
2. For each finding, show the proposed change, then confirm via `AskUserQuestion` with four options: apply this fix / skip this fix / apply all remaining / skip all remaining. Once an "all remaining" option is chosen, stop asking per item and apply (or skip) every remaining finding accordingly.
3. **Record the list of files actually modified in this phase** — Phase 7 takes it as input.
4. Print a final summary of applied vs. skipped fixes.

### Phase 7: Translation Sync

Keep the Chinese translations of governance documents in step with applied fixes.

**Trigger condition:** This run used `--fix` AND at least one fix was actually applied. If not triggered (report-only mode, or `--fix` where every fix was skipped), print why this phase is skipped.

1. From Phase 6's modified-file list, select the governance files: any `CLAUDE.md` or `AGENTS.md`, at any directory level (root or subdirectories).
2. If the selection is non-empty: invoke the `md-to-zh` skill via the Skill tool, passing those file paths as arguments. Its incremental-update mode skips unchanged files, so this stays cheap.
3. Do NOT pass `README.md` or `docs/` files even if they were fixed — their translations land in `.tiga/translationss git-ignored, so syncing them has no lasting effect.
4. If the modified-file list contains no governance files, print that as the skip reason.

Note the outcome of the translation sync (or that it was skipped) in the final output.
