# Governance Doc Audit

Rules for Phase 5 of tiga-govsync — checking governance documents against the repository's actual state, reporting findings, and (in `fix` mode) applying them.

## Step 1: Discovery

Gather the raw inputs needed for all subsequent checks.

1. **Locate governance documents.** Find all files matching `README.md`, `CLAUDE.md`, `AGENTS.md` (root and subdirectories), plus all `.md` files under `docs/` (skip silently if the directory does not exist). If `--scope` is set, keep only the specified paths.
2. **Capture the directory tree.** Run `find . -not -path './.git/*' -not -path './node_modules/*'` (or equivalent) to build the current file/directory listing. Respect `.gitignore` where practical.
3. **Capture the git timeline.** For each governance document, run `git log -1 --format='%H %ai' -- <file>` to get its last-modified commit and date. Also collect the set of paths modified since that commit: `git diff --name-only <commit>..HEAD`.

Print a brief summary: how many governance files were found, and their last-modified dates.

## Step 2: Structural alignment

Compare what the documents describe against what actually exists. For each governance document:

1. **Extract every path and command the document references.**
2. **Verify each referenced path exists** against the tree from Step 1. Mark `[PHANTOM]` when it does not — including referenced scripts that are missing or not executable.
3. **Detect undocumented content.** For structural documents (README, AGENTS.md) that enumerate directories or skills, compare the listed items against the actual items in the relevant directory. Mark `[MISSING]` when an actual item is not documented.

## Step 3: Staleness detection

Identify content that exists but may be outdated. For each governance document:

1. Using the git timeline from Step 1, identify paths that are referenced in the document AND have been modified after the document's last edit.
2. For each such path, judge whether the change is semantically relevant: renamed, moved, or materially changed content → `[STALE]`; formatting or whitespace only → skip.
3. Check version numbers, dates, and counts stated in the document against their current values.

## Step 4: Cross-document consistency

Check that the governance documents do not contradict each other: descriptions of the same directory must be compatible (not identical — just non-contradictory), a rule in one document must not contradict a rule in another, and directory tables in `README.md` and `AGENTS.md` must agree on which directories exist and what they are for. Mark contradictions as `[MISMATCH]`.

## Step 5: Report

Group findings by category in priority order — `[PHANTOM]` > `[MISSING]` > `[STALE]` > `[MISMATCH]` — and within a category by source document.

Give each finding its location, the problem, and a suggested fix. Close with a count per category plus the number of checks that passed.

## Step 6: Fix application

Runs only in `fix` mode. If there are no findings, print that as the skip reason.

1. Iterate through the findings in the priority order above.
2. For each finding, show the proposed change, then confirm via `AskUserQuestion` with four options: apply this fix / skip this fix / apply all remaining / skip all remaining. Once an "all remaining" option is chosen, stop asking per item and apply (or skip) every remaining finding accordingly.
3. **Record the list of files actually modified** — Phase 3 takes it as input for the translation sync.
4. Print a summary of applied vs. skipped fixes.
