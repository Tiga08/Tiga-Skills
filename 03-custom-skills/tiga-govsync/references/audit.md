# Governance Doc Audit

Rules for Phase 4 of tiga-govsync — checking governance documents against the repository's actual state, reporting findings, and (in `fix` mode) applying them.

## Step 1: Discovery

Gather the raw inputs needed for all subsequent checks.

1. **Build the project-owned inventory.** Use `git ls-files -co --exclude-standard` so tracked and untracked non-ignored files are visible without traversing symlinked directories. Derive the directory set from those file paths and record symlink entries without descending into them. Exclude dependency, vendored, generated, and translation trees even when they are not ignored.
2. **Locate governance documents.** From that inventory, select every `README.md`, `CLAUDE.md`, and `AGENTS.md` at any depth, plus every Markdown file below a `docs/` directory. If no `docs/` directory exists, skip that branch silently. Apply `--scope` after it has been validated in Phase 1.
3. **Capture the git timeline and working state.** For each governance document, run `git log -1 --format='%H %ai' -- <file>`. Separately collect staged paths with `git diff --cached --name-only`, unstaged paths with `git diff --name-only`, and untracked paths with `git ls-files --others --exclude-standard`. If a document has no committed baseline, mark it as untracked/new and use its current contents and mtime as evidence rather than running a commit-range diff.

Print a brief summary: how many governance files were found, their last committed dates or untracked status, and how many have current working-tree changes.

## Step 2: Structural alignment

Compare what the documents describe against what actually exists. For each governance document:

1. **Extract every path and command the document references.**
2. **Verify each referenced path exists** inside the repository without following a symlink outside it; use the Step 1 inventory to decide whether it is project-owned. Mark `[PHANTOM]` when it does not exist. Report a script as non-executable only when the documented command invokes the script directly rather than through an interpreter.
3. **Detect undocumented required content without demanding exhaustive catalogs.** Use the document's declared scope, ownership rule, and template:
   - A root `README.md` catalog covers primary user-facing items, not every repository entry.
   - An `AGENTS.md` structure table covers paths whose purpose or authority is not self-evident, not every directory.
   - A nested `README.md` covers entries readers need to navigate.
   - A `docs/**/README.md` index covers every direct topic document and documentation subtree in its declared scope.
   Mark `[MISSING]` only when an item required by that scope is absent.

## Step 3: Staleness detection

Identify content that exists but may be outdated. For each governance document:

1. Using the committed timeline plus staged, unstaged, and untracked state from Step 1, identify referenced paths changed after the document's baseline or changed currently.
2. For each such path, judge whether the change is semantically relevant: renamed, moved, or materially changed content → `[STALE]`; formatting or whitespace only → skip.
3. Check version numbers, dates, and counts stated in the document against their current values.

## Step 4: Cross-document consistency

Build a fact-to-owner map for all discovered governance documents using the ownership table and specificity rules in `references/generate.md`.

- Check that descriptions of the same directory are compatible, rules do not contradict each other, and directory tables agree on which directories exist and what they are for. Mark contradictions and facts placed in a file type that the ownership table explicitly excludes as `[MISMATCH]`.
- Mark `[DUPLICATE]` when the same fact is substantively restated in more than one governance document. Name the authoritative file in the finding and identify every non-authoritative copy. A link or one sentence of context is not duplication.
- Compare root and nested README files by scope, README indexes against their linked topic documents, topic documents against other topic documents covering the same subject, and all README/docs files against `AGENTS.md` / `CLAUDE.md`. Do not limit this check to the repository root.

## Step 5: Section structure

For every governed document with a template — root and nested `README.md`, `docs/**/README.md`, `AGENTS.md`, and root or subdirectory `CLAUDE.md` — read its template under `assets/` and the necessity assessment in `references/templates.md`.

Report `[SECTION]` for a required section that is missing when its condition holds, an empty or placeholder-only section, a section whose content belongs to another authoritative file, or a repository-specific section that fails the necessity assessment. Name the section, the applicable template rule, and the available repository evidence.

## Step 6: Report

Group findings by category in priority order — `[PHANTOM]` > `[MISSING]` > `[STALE]` > `[MISMATCH]` > `[SECTION]` > `[DUPLICATE]` — and within a category by source document.

Give each finding its location, the problem, and a suggested fix. Close with a count per category plus the number of checks that passed.

## Step 7: Fix application

Runs only in `fix` mode. If there are no findings, print that as the skip reason.

1. Iterate through the findings in the priority order above.
2. For each finding, show the proposed change, then ask through the host's user-confirmation mechanism with four choices: apply this fix / skip this fix / apply all remaining / skip all remaining. If the host has no structured confirmation tool, ask one concise plain-text question and wait. Once an "all remaining" choice is made, stop asking per item.
3. For `[SECTION]`, insert a missing required-section skeleton only when repository evidence can fill it; otherwise report the gap and skip it. Ask before deleting an unnecessary section. When that section contains the only copy of a fact, move the fact to its authoritative file instead of deleting it.
4. For `[DUPLICATE]`, preserve the complete fact in its authoritative file and replace each non-authoritative copy with a link or one line of context when readers still need a route. Never delete the only copy.
5. **Record the list of files actually modified** — Phase 5 takes only modified `SKILL.md`, `AGENTS.md`, and `CLAUDE.md` files as input for the translation sync; modified README/docs files remain in the audit summary but are not translated.
6. Print a summary of applied vs. skipped fixes.
