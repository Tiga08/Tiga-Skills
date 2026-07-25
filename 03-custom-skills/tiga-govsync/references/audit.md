# Governance Doc Audit

Rules for Phase 4 of tiga-govsync — checking governance documents against the repository's actual state, reporting findings, and (in `fix` mode) applying them.

## Step 1: Discovery

Gather the raw inputs needed for all subsequent checks.

1. **Locate governance documents.** Find all files matching `README.md`, `CLAUDE.md`, `AGENTS.md` (root and subdirectories), plus all `.md` files under `docs/` (skip silently if the directory does not exist). If `--scope` is set, keep only the specified paths.
2. **Capture the directory tree.** Run `find . -not -path './.git/*' -not -path './node_modules/*'` (or equivalent) to build the current file/directory listing. Respect `.gitignore` where practical.
3. **Capture the git timeline.** For each governance document, run `git log -1 --format='%H %ai' -- <file>` to get its last-modified commit and date. Also collect the set of paths modified since that commit: `git diff --name-only <commit>..HEAD`.

Print a brief summary: how many governance files found, their last-modified dates.

## Step 2: Structural alignment

Compare what the documents describe against what actually exists.

For each governance document:

1. **Extract referenced paths.** Parse the document for file paths, directory names, and shell commands. Look in:
   - Markdown tables (especially `| Directory | Purpose |` style)
   - Code blocks (especially `bash` fenced blocks)
   - Inline code spans referencing paths (e.g., `` `03-custom-skills/` ``)
   - Link targets (e.g., `[text](path/file.md)`)

2. **Verify each referenced path exists.** Check files and directories against the actual tree from Step 1.
   - Mark as `[PHANTOM]` if the path does not exist.

3. **Detect unreferenced content.** For structural documents (README, AGENTS.md) that enumerate directories or skills:
   - Compare the listed items against actual items in the relevant directory.
   - Mark as `[MISSING]` if an actual item is not documented.

4. **Verify shell commands.** For commands referenced in the document (e.g., in a "Common Commands" section):
   - Check that referenced scripts exist and are executable.
   - Mark as `[PHANTOM]` if the script does not exist.

5. **Check directory-structure ordering.** For directory-structure tables or lists in structural documents (README, AGENTS.md):
   - Entries must list directories first, then files, with each group sorted lexicographically by name.
   - Mark as `[ORDER]` if the entries violate this ordering.

## Step 3: Staleness detection

Identify content that exists but may be outdated.

For each governance document:

1. Using the git timeline from Step 1, identify paths that:
   - Are referenced in the document, AND
   - Have been modified after the document's last edit.

2. For each such path, check whether the modification is semantically relevant:
   - File renamed or moved → `[STALE]`
   - File content changed significantly → `[STALE]`
   - Only formatting/whitespace changes → skip

3. Check version numbers, dates, or counts mentioned in the document against current values.

## Step 4: Cross-document consistency

Check that governance documents do not contradict each other.

1. **Directory descriptions.** If multiple documents describe the same directory, verify descriptions are compatible (not identical — just non-contradictory).
2. **Instruction conflicts.** Check for rules in one document that contradict rules in another (e.g., CLAUDE.md says "never X" while AGENTS.md says "always X").
3. **Structural overlap.** If both README.md and AGENTS.md list directory tables, verify they agree on which directories exist and their stated purposes.

Mark contradictions as `[MISMATCH]`.

## Step 5: Report

Output all findings grouped by severity, then by source document.

**Report format:**

```
## Audit Report

### [PHANTOM] — References to non-existent content
- README.md (line ~N): references `path/that/does-not-exist`
  → Suggested fix: remove the reference or create the missing content

### [MISSING] — Undocumented content
- `03-custom-skills/tiga-govsync/` exists but is not listed in README.md skill table
  → Suggested fix: add entry to the skill list table

### [STALE] — Outdated references
- CLAUDE.md (line ~N): references `04-scripts/old-script.sh`, last modified 30 days after CLAUDE.md
  → Suggested fix: review and update the reference

### [MISMATCH] — Cross-document contradictions
- README.md says "directory X does Y" but AGENTS.md says "directory X does Z"
  → Suggested fix: align the descriptions

### [ORDER] — Directory-structure ordering violations
- AGENTS.md Structure table lists `descriptions-zh.conf` before `01-prompts/`
  → Suggested fix: reorder entries — directories first, then files, each group sorted by name

### Summary
- N PHANTOM findings
- N MISSING findings
- N STALE findings
- N MISMATCH findings
- N ORDER findings
- N checks passed
```

**Priority order for suggested fixes:** `[PHANTOM]` > `[MISSING]` > `[STALE]` > `[MISMATCH]` > `[ORDER]`.

If `--verbose` is set, append a section listing all `[OK]` checks that passed.

## Step 6: Fix application

Runs only in `fix` mode. If there are no findings, print that as the skip reason.

1. Iterate through findings in priority order (`[PHANTOM]` > `[MISSING]` > `[STALE]` > `[MISMATCH]` > `[ORDER]`).
2. For each finding, show the proposed change, then confirm via `AskUserQuestion` with four options: apply this fix / skip this fix / apply all remaining / skip all remaining. Once an "all remaining" option is chosen, stop asking per item and apply (or skip) every remaining finding accordingly.
3. **Preserve ordering when writing structure entries:** any fix that adds or modifies directory-structure entries (including `[MISSING]` fixes that append entries) must keep the result ordered — directories first, then files, each group sorted by name.
4. **Record the list of files actually modified** — Phase 3 takes it as input for the translation sync.
5. Print a summary of applied vs. skipped fixes.
