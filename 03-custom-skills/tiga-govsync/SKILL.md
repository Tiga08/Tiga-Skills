---
name: tiga-govsync
description: Maintain a repository's governance docs end to end — generate or rebuild AGENTS.md / CLAUDE.md from actual repo evidence, sync Simplified Chinese translations of every SKILL.md / AGENTS.md / CLAUDE.md by invoking tiga-translate, and audit the docs against real repository state. Modes: check (read-only report of what is missing, stale, or inconsistent), update (rebuild governance files and sync all translations), fix (audit, then apply fixes interactively). Use when governance docs or their Chinese versions have drifted from the repository, or when a repo needs governance files created.
argument-hint: "check|update|fix [--force] [--scope <path>] [--no-translate]"
arguments: [mode]
disable-model-invocation: true
---

Keep a repository's governance documents and their Simplified Chinese translations in step with the repository's actual state, in one pass.

**Arguments:** the first positional argument is the mode; flags may appear anywhere. With no arguments, run `check` and close the output by listing all three modes so the user can pick the one they meant.

本次调用：`$ARGUMENTS` — 模式 `$mode`

Modes:

- `check`: read-only. Report which governance files are missing or would be rebuilt, which translations are missing or stale, and what the audit finds. Writes nothing.
- `update`: rebuild the governance files (merging still-valid old rules), sync translations of every `SKILL.md` / `AGENTS.md` / `CLAUDE.md`, then run a read-only audit.
- `fix`: audit, apply fixes interactively, then sync translations of the governance files that were modified.

Flags:

- `--force`: passed through to `tiga-translate` — force full re-translation instead of incremental updates.
- `--scope <path>`: limit generation, translation, and audit to one path (a file or directory). To cover two paths, run the skill twice.
- `--no-translate`: skip the translation phase (Phase 3).

## Workflow

### Phase 1: Preflight

1. Locate the repository root with `git rev-parse --show-toplevel`. If the command fails, report that this skill requires a git repository — translation freshness and staleness detection both read the git timeline, and a committed baseline is what makes a rebuild revertible — and stop.
2. Take `$mode` as the mode and collect the flags from `$ARGUMENTS`. An unrecognized mode is an error: report it, list the three valid modes, and stop. When `$mode` is empty, use `check`.

### Phase 2: Generate

Runs in `update`, and as a read-only preview in `check`. Skipped in `fix`.

Read [generate.md](${CLAUDE_SKILL_DIR}/references/generate.md) and follow it. It covers repository analysis, the global baseline, the criterion for subdirectory `CLAUDE.md` files, the generation plan, the merge-on-overwrite rule, and the deduplication pass. The templates and their line budgets live in [templates.md](${CLAUDE_SKILL_DIR}/references/templates.md).

Existing files are merged and rewritten without prompting: merge-on-overwrite preserves the old rules that still hold, and Phase 1 has already established a git repository, so any rewrite is revertible.

Record the paths of the files actually written — Phase 3 takes them as input.

### Phase 3: Translate

Runs in `update` and `fix`. In `check` it degrades to the freshness check below. Skipped entirely when `--no-translate` is set — print that as the reason.

**Build the whitelist:**

1. Start from the governance files written in Phase 2 (in `fix`, from the files modified in Phase 4 instead).
2. In `update`, add every `SKILL.md` found by `find . -name SKILL.md -not -path './.git/*'`, plus every `AGENTS.md` and `CLAUDE.md` at any directory level.
3. Do **not** pass `-L` to `find`. Symlinked directories such as `02-agent-skills/`, `.claude/skills`, and `.codex/skills` must not be followed — external upstream sources are never to be modified.
4. Exclude files whose names end in `.zh.md` or `-zh.md`.
5. If `--scope` is set, keep only whitelist entries under the given path.

**Translate:** invoke the `tiga-translate` skill via the Skill tool once, passing the entire whitelist as arguments, plus `--force` when it is set. Its incremental mode prints "already up to date" and spends nothing on unchanged files, so a full whitelist stays cheap.

Its output rules apply unchanged: `AGENTS.md` / `CLAUDE.md` become `.zh.md` next to the source; `SKILL.md` becomes `.tiga/translations/{parent-dir-name}-SKILL.md`.

**Freshness check (`check` only):** do not invoke tiga-translate. For each whitelist entry, compute its output path per the rules above and classify it as **missing translation** (no output file), **stale translation**, or **up to date** — judging staleness by the same baseline criterion tiga-translate applies, documented in its `SKILL.md`. Print the three groups as lists.

### Phase 4: Audit

Runs in all three modes.

Read [audit.md](${CLAUDE_SKILL_DIR}/references/audit.md) and follow it. It covers the discovery inputs, the `[PHANTOM]` / `[MISSING]` / `[STALE]` / `[MISMATCH]` checks, the report, the fix priority order, and the interactive fix flow.

In `check` and `update`, the audit reports only and writes nothing. In `fix`, run the interactive fix flow after the report, then return to Phase 3 with the list of modified governance files (`CLAUDE.md` / `AGENTS.md` at any level) to sync their translations. Do not pass `README.md` or `docs/` files — their translations land in the git-ignored `.tiga/translations/`, so syncing them has no lasting effect.

`--scope` narrows the set of audited documents.

### Phase 5: Summary

Print a final summary covering:

- Governance files generated, skipped (with reason), or failed.
- Translation results counted by status: new / incremental update / already up to date / full re-translation / failed. In `check`, the missing / stale / up-to-date counts instead.
- Audit findings counted by category, and which fixes were applied vs. skipped.
- Any phase that was skipped, with the reason.
