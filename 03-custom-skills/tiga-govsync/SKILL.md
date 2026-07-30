---
name: tiga-govsync
description: "Govern repository-owned README, docs, and agent instruction files against repository evidence and a single-source ownership model, synchronize Simplified Chinese translations, and optionally audit local skills. Use when governance documents are missing, stale, duplicated, structurally inconsistent, or out of sync with the repository."
argument-hint: "check|update|fix [--scope <path>] [--no-translate] [--skills]"
disable-model-invocation: true
---

Keep a repository's governance documents and their Simplified Chinese translations in step with the repository's actual state and keep each fact in one authoritative file.

**Arguments:** parse the mode and flags from `$ARGUMENTS`; flags may appear before or after the mode. With no arguments, run `check` and close the output by listing all three modes so the user can pick the one they meant.

本次调用：`$ARGUMENTS`

Modes:

- `check`: read-only. Report which agent-governance files are missing or would be rebuilt, which existing README/docs files need reconciliation, which translations are missing or stale, and what the audit finds. Writes nothing.
- `update`: rebuild `AGENTS.md` / `CLAUDE.md` (merging still-valid old rules), reconcile every existing project-owned `README.md` and `docs/**/*.md`, update local skills when `--skills` is set, run the governance-document audit read-only, then sync translations of every project-owned `SKILL.md` / `AGENTS.md` / `CLAUDE.md`.
- `fix`: audit, apply fixes interactively, then sync translations of the modified `SKILL.md` / `AGENTS.md` / `CLAUDE.md` files.

Flags:

- `--scope <path>`: limit generation, translation, skill checks, and document audit to one path (a file or directory). To cover two paths, run the skill twice.
- `--no-translate`: skip the translation phase (Phase 5).
- `--skills`: additionally audit the repository's own `SKILL.md` files against the cross-client Agent Skills profile (Phase 3). `check` reports findings, `update` applies them subject to the dirty-target guard, and `fix` asks before each change. Without this flag, that phase does not run at all.

## Workflow

### Phase 1: Preflight

1. Locate the repository root with `git rev-parse --show-toplevel`. If the command fails, report that this skill requires a git repository because translation freshness and staleness detection read the git timeline, then stop.
2. Parse `$ARGUMENTS`. Accept at most one mode token (`check`, `update`, or `fix`) anywhere in the argument list; default to `check`. Parse `--scope <path>`, `--no-translate`, and `--skills`; reject unknown flags, missing flag values, or conflicting mode tokens.
3. If `--scope` is set, resolve it without following a symlink outside the repository. Require the resolved path to stay inside the repository root. An absent path is valid only when it is the root `README.md` targeted for preview or creation and its parent is the repository root; otherwise report it and stop.
4. Snapshot the pre-existing working-tree state with `git status --short`, including staged, unstaged, and untracked paths. In a writing mode, never overwrite a pre-existing dirty target blindly: preserve its content during the merge, show the proposed diff, and ask before replacing or removing any of it. If the host cannot request confirmation, skip that target and report why.
5. `check` is strictly read-only: do not create output directories, touch files, or invoke a workflow that may write.

### Phase 2: Generate

Runs in `update`, and as a read-only preview in `check`. Skipped in `fix`.

Read [generate.md](references/generate.md) and follow it. It covers governance-document discovery, repository analysis, the supported clients' global instruction baselines, the single-source ownership rule, the criterion for subdirectory `CLAUDE.md` files, the generation plan, the merge-on-overwrite rule, cross-document reconciliation, and section-structure governance. Template rules and line budgets live in [templates.md](references/templates.md); the templates themselves live under `templates/`.

Existing clean files are merged and rewritten without prompting; pre-existing dirty targets follow the Phase 1 confirmation guard. Merge-on-overwrite preserves old rules that still hold, and reconciliation changes only facts that violate the ownership model. Create a missing root `README.md` from its template; never create a missing nested `README.md` or topic document under `docs/`.

Record the paths of the files actually written for the Phase 5 summary and translation plan.

### Phase 3: Skill Spec

Runs only when `--skills` is set. Without the flag, skip it silently — the rest of the workflow is unchanged.

**Discovery:** find project-owned `SKILL.md` files in standard `.agents/skills/` directories and repository-owned source directories such as `03-custom-skills/`. Use the project-owned inventory from `git ls-files -co --exclude-standard`; do not traverse symlink registries, dependencies, vendored trees, generated output, or ignored paths. `--scope` narrows the set.

Read [skill-spec.md](references/skill-spec.md) and follow it. It separates the portable Agent Skills core, Claude Code extensions, and Codex `agents/openai.yaml`, then defines the `[MISSING]` / `[UNKNOWN]` / `[MISMATCH]` / `[STALE]` / `[BLOAT]` checks and fix flow.

In `check` the phase reports only. In `update` apply fixes directly except where the preflight dirty-target guard requires confirmation; in `fix` confirm each fix first. Record the containing directory of every modified `SKILL.md` for Phase 5; never record a bare `SKILL.md` path.

If `./04-scripts/manage-skills.sh` exists, also run `./04-scripts/manage-skills.sh check` and report its registry/link health separately from the specification verdict.

### Phase 4: Audit

Runs in all three modes.

Read [audit.md](references/audit.md) and follow it. It covers the discovery inputs, the `[PHANTOM]` / `[MISSING]` / `[STALE]` / `[MISMATCH]` / `[SECTION]` / `[DUPLICATE]` checks, the report, the fix priority order, and the interactive fix flow.

In `check` and `update`, the audit reports only and writes nothing. In `fix`, run the interactive fix flow after the report and record modified `CLAUDE.md` / `AGENTS.md` paths for Phase 5. Do not add modified `README.md` or `docs/` files to the translation whitelist.

`--scope` narrows the set of audited documents.

### Phase 5: Translate

Runs after every phase that may write. In `check` it performs only the freshness calculation below. Skip it entirely when `--no-translate` is set and print that reason.

**Build the whitelist:**

1. In `check` and `update`, discover every project-owned `SKILL.md`, `AGENTS.md`, and `CLAUDE.md` from `git ls-files -co --exclude-standard`. Exclude Chinese variants, ignored paths, dependencies, vendored or generated trees, and anything reached through a symlink registry. Convert each selected `SKILL.md` to its containing directory; keep `AGENTS.md` and `CLAUDE.md` as files.
2. In `fix`, start from only the translation-eligible paths modified in Phases 3 and 4, converting each `SKILL.md` to its containing directory.
3. Apply `--scope` to source paths before conversion. When the scope is a skill directory, its `SKILL.md`, or any descendant of that skill directory, select the whole skill directory so mirrored output paths remain stable. Otherwise keep only governance files inside the scope.
4. Deduplicate resolved paths and detect distinct skill directories with the same basename as an output collision before invoking translation.

**Translate (`update` / `fix`):** invoke the available `tiga-translate` skill once through the host's skill-invocation mechanism, passing the full whitelist. Its routing rules remain authoritative: `AGENTS.md` / `CLAUDE.md` become sibling `.zh.md` files, while a skill directory mirrors under `.tiga/translations/<skill-dir-name>/`.

**Freshness check (`check`):** do not invoke `tiga-translate`. Read its `SKILL.md`, compute every expected output using the same routing and baseline rules, and classify each as **missing translation**, **stale translation**, or **up to date**. Expanding a skill directory includes each translation-eligible Markdown file inside it. Print all three groups and their counts without creating directories.

### Phase 6: Summary

Print a final summary covering:

- Governance files generated, reconciled, skipped (with reason), or failed, including every omitted required section and its reason.
- Translation results counted by status: new / incremental update / already up to date / full re-translation / failed. In `check`, the missing / stale / up-to-date counts instead.
- Skill spec findings counted by category (`--skills` only), and which fixes were applied vs. skipped.
- Audit findings counted by category, and which fixes were applied vs. skipped.
- Any phase that was skipped, with the reason.
