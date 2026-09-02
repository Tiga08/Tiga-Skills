# Governance File Generation

Rules for Phase 2 of tiga-govsync — analyzing the repository, planning which governance files to write, generating them, reconciling ownership, and governing section structure.

## Single-source rule

Each fact has exactly one authoritative home; every other file may only link to it or give one line of context. Apply the most specific matching row:

| File | Authoritative for | Must not contain — link or one line of context instead |
| --- | --- | --- |
| Root `README.md` | The human-facing one-page repository overview: project positioning, task lines, closed-loop entry points, minimal getting-started, and a concise catalog of primary items | An exhaustive directory encyclopedia, component or Skill encyclopedia, current to-dos, dynamic statistics, detailed CLI reference |
| Nested `README.md` outside `docs/` | The human-facing one-page overview, entry points, and minimal usage for its directory | Repository-wide facts, exhaustive implementation details, detailed contracts already owned by a topic document |
| `docs/**/README.md` | Navigation and one-line descriptions for the documents in that `docs/` subtree | The detailed content of the linked topic documents |
| Other `docs/**/*.md` | Durable detail for its named topic, such as architecture, design decisions, data contracts, workflows, or detailed CLI reference | Repository or directory overview, agent-only operating rules, current to-dos, dynamic status or sample statistics |
| `AGENTS.md` | What an agent needs: repository structure and authority, commands, testing requirements, operational boundaries | Implementation details of an individual component or Skill, full data contracts, dynamic project status |
| Root `CLAUDE.md` | The few genuinely error-prone project-level constraints and gotchas beyond `@AGENTS.md` | Rules duplicated from `AGENTS.md` or any subdirectory `CLAUDE.md`, any dated status |
| Subdirectory `CLAUDE.md` | Rules unique to that directory that differ from the root | Content already covered or implied by the root files |

When more than one file matches the same row, the narrowest scope owns the fact: a nested `README.md` owns its directory overview rather than the root `README.md`; a leaf topic document owns its topic rather than a `docs/**/README.md` index. Preserve an existing explicit source-of-truth declaration when it agrees with this table. A link plus one sentence explaining why the destination matters is context, not duplication.

Discover every project-owned `README.md` at any depth and every Markdown file below any `docs/` directory from `git ls-files -co --exclude-standard`. Do not follow symlinked directories or include dependency, vendored, generated, or translation trees.

When the root `README.md` is missing, generate it from `assets/readme-root-template.md`. Never create a missing nested `README.md` (including `docs/**/README.md`) or topic document under `docs/`; their templates are structural baselines only. Existing README/docs files participate in analysis, cross-document reconciliation, section checks, and audit. In `update`, they may be minimally rewritten to enforce the single-source rule; in `check`, changes are previewed only; in `fix`, Phase 4 asks before applying each change.

## Step 1: Analyze the repository

- List the top two levels of the directory tree.
- Read every discovered `README.md` and `docs/**/*.md`, plus existing configuration and agent-governance files such as `AGENTS.md`, `CLAUDE.md`, or related files. For a large documentation set, inventory first and process files in bounded groups while maintaining one fact-to-owner map. Keep the content of existing governance files — Step 3 merges their still-valid rules into the new files.
- Read the available host-level agent instruction baselines. Treat already-loaded global instructions as authoritative; when reading files directly, resolve symlinks and use `~/.claude/CLAUDE.md` for Claude Code and `~/.codex/AGENTS.md` for Codex when present. Record which supported clients are covered.
- Treat a repository rule as globally redundant only when every supported client that needs it inherits an equivalent rule. Otherwise keep cross-client rules in `AGENTS.md` and keep Claude-only additions in the root `CLAUDE.md`.
- Identify the repository type: application, library, monorepo, content repository, or other.
- Identify the main functional layers of the project.
- Determine which top-level directories need their own `CLAUDE.md`.

Criterion for subdirectory `CLAUDE.md`:

> Generate a subdirectory `CLAUDE.md` only when that directory has ownership semantics, modification rules, or operational constraints that differ from the repository root.

## Step 2: Build the generation plan

List every generated target in order — `AGENTS.md`, root `CLAUDE.md`, then each subdirectory `CLAUDE.md` — marking each target that already exists as "merge and rewrite". If the root `README.md` is missing, append it as "create from template". List every existing `README.md` or `docs/**/*.md` as "reconcile existing" and note that its section structure will be checked; never list a missing nested README or topic document as a generation target.

When `--scope` is set, use the full inventory as read-only evidence but include only the exact scoped file or descendants of the scoped directory as write targets. The missing root `README.md` exception from Phase 1 remains valid when that exact file is the scope. Never plan a write outside the resolved scope.

In `check`, print the analysis summary and the plan with those annotations, then return to the main workflow without writing. Otherwise print both before generating anything.

## Step 3: Generate the files

Generate the planned files in order: `AGENTS.md` → root `CLAUDE.md` → each subdirectory `CLAUDE.md` → root `README.md` (only when missing).

- Read the rules in `references/templates.md`, then use the corresponding file under `assets/`, including its line budget.
- Assess each required section in the order defined by `references/templates.md`. Omit sections that fail the assessment and record the reason for Phase 6; never invent content or keep placeholder text.
- Every rule must derive from the actual repository structure, files, and observable conventions. Do not fabricate rules.
- Do not write a rule that only restates every applicable global baseline read in Step 1; a rule covered for only one client may still be required by another.
- Place every fact in the file the [Single-source rule](#single-source-rule) assigns it to. When a fact's authoritative home is another file, write only a link to it or one line of context — never a restatement.
- The `Never` section must cover the repository's most critical prohibitions.
- Each subdirectory `CLAUDE.md` must carry at least one constraint absent from the root.
- **When overwriting an existing file, merge instead of discarding:** carry over rules from the old file that are still valid and not already covered by the newly generated content. Drop only rules that contradict the current repository state.
- For a target that was already dirty at Phase 1, preserve its current content, show the proposed diff, and obtain confirmation before replacing or removing any pre-existing line.

## Step 4: Cross-document reconciliation pass

Re-read every generated file and every discovered `README.md` and `docs/**/*.md`. Build a fact-to-owner map using the [Single-source rule](#single-source-rule). For each duplicated fact, keep the complete statement only in its authoritative file; in every other file, delete it or replace it with a link or one line of context. Compare in five directions:

1. **Generated content ↔ global baselines** — delete, rather than reword, a rule only when every supported client that needs it inherits an equivalent host-level rule.
2. **Root `README.md` ↔ nested `README.md`** — repository-wide overview stays at the root; directory-specific overview stays in the nearest directory.
3. **README files ↔ `docs/**/*.md`** — README files summarize and route; topic documents hold durable detail.
4. **README/docs ↔ `AGENTS.md` / `CLAUDE.md`** — human or topic documentation does not restate agent-only operating rules, and agent files do not absorb human overview or detailed reference content.
5. **`AGENTS.md` ↔ `CLAUDE.md`, root ↔ subdirectory** — an agent rule belongs at exactly one level and in exactly one file.

In `update`, apply the necessary edits only to the in-scope target set built in Step 2 and record every modified path. Use out-of-scope documents as evidence without rewriting them; report any cross-boundary reconciliation still needed as a deferred item in Phase 6. Preserve headings, surrounding prose, generated blocks, and unrelated formatting. Never remove the only copy of a fact when its authoritative destination does not exist or cannot be identified; leave it in place and let Phase 4 report the ownership problem instead.

Then go line by line through the generated agent files and ask: would the agent get this wrong if this line were gone? If not, delete it. Apply the edits before leaving Phase 2.

## Step 5: Section structure pass

Check every in-scope governed document that has a template — root and nested `README.md`, `docs/**/README.md`, `AGENTS.md`, and root or subdirectory `CLAUDE.md` — against its corresponding template and the necessity assessment in `references/templates.md`.

Identify missing required sections (when their condition holds), empty or placeholder-only sections, sections that merely repeat content owned by another file, and repository-specific sections that fail the necessity assessment. In `update`, make only edits justified by the single-source rule, such as moving authoritative content or replacing a duplicate with a link. Do not invent content for a missing section. Pass every unresolved finding to Phase 4 as `[SECTION]`.
