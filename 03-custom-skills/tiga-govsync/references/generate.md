# Governance File Generation

Rules for Phase 2 of tiga-govsync — analyzing the repository, planning which governance files to write, generating them, and removing duplication from the result.

## Step 1: Analyze the repository

- List the top two levels of the directory tree.
- Read the `README` and any existing configuration or governance files, including existing `AGENTS.md`, `CLAUDE.md`, or agent-related files. Keep the content of existing governance files — Step 3 merges their still-valid rules into the new files.
- Read `~/.claude/CLAUDE.md` as the **global baseline** (if it is a symlink, read the file it points to). Everything it already states applies to this repository without being repeated; Step 4 checks the generated files against it.
- Identify the repository type: application, library, monorepo, content repository, or other.
- Identify the main functional layers of the project.
- Determine which top-level directories need their own `CLAUDE.md`.

Criterion for subdirectory `CLAUDE.md`:

> Generate a subdirectory `CLAUDE.md` only when that directory has ownership semantics, modification rules, or operational constraints that differ from the repository root.

## Step 2: Build the generation plan

List every target file in generation order — `AGENTS.md`, root `CLAUDE.md`, then each subdirectory `CLAUDE.md` — marking each target that already exists as "merge and rewrite".

In `check`, print the analysis summary and the plan with those annotations, then **stop here** — no files are written. Otherwise print both before generating anything.

## Step 3: Generate the files

Generate the planned files in order: `AGENTS.md` → root `CLAUDE.md` → each subdirectory `CLAUDE.md`.

- Read [templates.md](templates.md) and use the corresponding template for each file, including its line budget.
- Every rule must derive from the actual repository structure, files, and observable conventions. Do not fabricate rules.
- Do not write a rule that only restates the global baseline read in Step 1.
- The `Never` section must cover the repository's most critical prohibitions.
- Each subdirectory `CLAUDE.md` must carry at least one constraint absent from the root.
- **When overwriting an existing file, merge instead of discarding:** carry over rules from the old file that are still valid and not already covered by the newly generated content. Drop only rules that contradict the current repository state.

## Step 4: Deduplication pass

Re-read each generated file and remove every rule that is already stated elsewhere. Compare in three directions:

1. **Generated content ↔ global baseline** — a rule that only restates `~/.claude/CLAUDE.md` is deleted, not reworded.
2. **`AGENTS.md` ↔ `CLAUDE.md`** — a rule belongs to exactly one of them.
3. **Root ↔ subdirectory** — drop subdirectory rules already implied by the root.

Then go line by line and ask: would the agent get this wrong if this line were gone? If not, delete it. Apply the edits before leaving Phase 2.
