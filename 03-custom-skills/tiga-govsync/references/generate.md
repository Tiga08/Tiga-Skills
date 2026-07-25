# Governance File Generation

Rules for Phase 2 of tiga-govsync — analyzing the repository, planning which governance files to write, generating them, and self-checking the result.

## Step 1: Analyze the repository

- List the top two levels of the directory tree.
- Read the `README` and any existing configuration or governance files, including existing `AGENTS.md`, `CLAUDE.md`, or agent-related files. Keep the content of existing governance files — Step 3 merges their still-valid rules into the new files.
- Identify the repository type: application, library, monorepo, content repository, or other.
- Identify the main functional layers of the project.
- Determine which top-level directories need their own `CLAUDE.md`.

Criterion for subdirectory `CLAUDE.md`:

> Generate a subdirectory `CLAUDE.md` only when that directory has ownership semantics, modification rules, or operational constraints that differ from the repository root.

## Step 2: Build the generation plan and resolve conflicts

List every target file in generation order — `AGENTS.md`, root `CLAUDE.md`, then each subdirectory `CLAUDE.md`. Mark each target that already exists as a conflict. The plan's file count is the initial total N.

Resolve conflicts by mode:

- `--force` is set: mark every conflicting target as "overwrite"; no prompts.
- `dry-run`: print the analysis summary and the generation plan with conflict annotations, then **stop here** — no files are written.
- `update`: mark every conflicting target as "merge and rewrite"; no prompts.
- `init`: for each conflicting target, ask via `AskUserQuestion`:
  - Overwrite this file
  - Skip this file
  - Overwrite all remaining conflicts
  - Skip all remaining conflicts

  An "all remaining" choice applies to every subsequent conflict without further prompting. Remove each skipped file from the generation plan and reduce N accordingly; record it (with reason "skipped by user") for the final summary.

Print the analysis summary and the final generation plan (the N files that will actually be written) before generating anything.

## Step 3: Generate the files

Generate the planned files in order: `AGENTS.md` → root `CLAUDE.md` → each subdirectory `CLAUDE.md`. Before each file, print `[k/N] Generating <path> ...`, where k increments globally across all files and N is the final count from Step 2.

- Read [templates.md](templates.md) and use the corresponding template for each file.
- Every rule must derive from the actual repository structure, files, and observable conventions. Do not fabricate rules.
- **Directory-structure ordering:** whenever output enumerates a directory structure (e.g., the `Structure` table), list directory entries first, then file entries, with each group sorted lexicographically by name.
- **When overwriting an existing file, merge instead of discarding:** carry over rules from the old file that are still valid and not already covered by the newly generated content. Drop only rules that contradict the current repository state.

## Step 4: Quality self-check

Verify the generated files against this checklist and print each item with pass/fail status:

- [ ] **No duplication** — `AGENTS.md` and `CLAUDE.md` do not repeat the same descriptions unnecessarily.
- [ ] **Dangerous operations are covered** — the `Never` section lists the repository's most critical prohibitions.
- [ ] **Nothing is fabricated** — every rule derives from the actual repository structure, files, and observable conventions.
- [ ] **Subdirectory rules are specific** — each subdirectory `CLAUDE.md` contains at least one constraint absent from the root.
- [ ] **Instruction priority is clear** — conflicts between user instructions, subdirectory rules, and root rules are resolved by the stated priority order.
- [ ] **Structure ordering** — directory-structure entries list directories first, then files, each group sorted by name.

Any failed item must be fixed (edit the affected file, then re-check) before leaving Phase 2.
