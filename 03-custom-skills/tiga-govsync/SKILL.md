---
name: tiga-govsync
description: Maintain a repository's governance docs end to end — generate or rebuild AGENTS.md / CLAUDE.md from actual repo evidence, sync Simplified Chinese translations of every SKILL.md / AGENTS.md / CLAUDE.md by invoking tiga-translate, and audit the docs against real repository state. Modes: init (first-time generation), dry-run (read-only preview of what is missing or stale), update (regenerate governance files and sync all translations), check (audit report only), fix (audit then apply fixes interactively). Use when governance docs or their Chinese versions have drifted from the repository, or when a repo needs governance files created.
argument-hint: "init|dry-run|update|check|fix [--force] [--scope <path>] [--no-translate] [--verbose]"
---

Keep a repository's governance documents and their Simplified Chinese translations in step with the repository's actual state, in one pass.

**Arguments:** The first positional argument is the mode. Flags may appear anywhere in the argument list.

Modes:

- `init`: First-time generation — analyze the repository and write `AGENTS.md` / `CLAUDE.md`, prompting on every existing file, then sync translations.
- `dry-run`: Read-only preview — report which governance files are missing or would be rebuilt, which translations are missing or stale, and what the audit finds. Writes nothing.
- `update`: Regenerate governance files (merging still-valid old rules), sync translations of every `SKILL.md` / `AGENTS.md` / `CLAUDE.md`, then run a read-only audit.
- `check`: Audit only — report inconsistencies between the docs and the repository. Writes nothing.
- `fix`: Audit, apply fixes interactively, then sync translations of the governance files that were modified.

Flags:

- `--force`: In `init` / `update`, overwrite conflicting files without prompting. In the translation phase, force full re-translation of every file.
- `--scope <path>`: Limit generation, translation, and audit to the given path (a file or directory). May be repeated.
- `--no-translate`: Skip the translation phase (Phase 3).
- `--verbose`: Include `[OK]` entries for passing checks in the audit report.

**No-argument behavior:** Run `dry-run` — the read-only preview. At the end of the output, list all five modes so the user can pick the one they meant.

## Mode-to-phase map

| Mode | Phase 2 Generate | Phase 3 Translate | Phase 4 Audit |
| --- | --- | --- | --- |
| `init` | write (prompt on conflict) | yes | no |
| `dry-run` | preview only | freshness check only | read-only |
| `update` | write (merge) | yes | read-only |
| `check` | no | no | read-only |
| `fix` | no | yes (modified files only) | audit + interactive fix |

## Workflow

### Phase 1: Preflight

1. Locate the repository root with `git rev-parse --show-toplevel`. If the command fails, report that this skill requires a git repository — translation freshness and staleness detection both read the git timeline — and stop.
2. Parse the argument list: take the first positional argument as the mode, and collect the flags. An unrecognized mode is an error: report it, list the five valid modes, and stop. With no positional argument, use `dry-run`.
3. Print the mode, the active flags, and the phases this run will execute (per the map above).

### Phase 2: Generate

Runs in `init`, `update`, and as a preview in `dry-run`. Skipped in `check` and `fix`.

Read [references/generate.md](references/generate.md) and follow it. It covers repository analysis, the criterion for subdirectory `CLAUDE.md` files, the generation plan and conflict resolution, the merge-on-overwrite rule, directory-structure ordering, and the quality self-check. The file templates live in [references/templates.md](references/templates.md).

Mode differences:

- `init`: for every target that already exists, ask via `AskUserQuestion` (overwrite / skip / overwrite all remaining / skip all remaining).
- `update`: default to merging and rewriting existing files without prompting.
- `dry-run`: print the analysis summary and generation plan with conflict annotations, then write nothing.
- `--force`: overwrite every conflict without prompting, in both `init` and `update`.

Record the paths of the files actually written — Phase 3 takes them as input.

### Phase 3: Translate

Runs in `init`, `update`, and `fix`. In `dry-run` it degrades to the freshness check below. Skipped entirely when `--no-translate` is set — print that as the reason.

**Build the whitelist:**

1. Start from the governance files written in Phase 2 (in `fix`, from the files modified in Phase 4 instead).
2. In `update`, add every `SKILL.md` found by `find . -name SKILL.md -not -path './.git/*'`, plus every `AGENTS.md` and `CLAUDE.md` at any directory level.
3. Do **not** pass `-L` to `find`. Symlinked directories such as `02-agent-skills/`, `.claude/skills`, and `.codex/skills` must not be followed — external upstream sources are never to be modified.
4. Exclude files whose names end in `.zh.md` or `-zh.md`.
5. If `--scope` is set, keep only whitelist entries under the given paths.

**Translate:** invoke the `tiga-translate` skill via the Skill tool once, passing the entire whitelist as arguments. Pass `--force` through when it is set. tiga-translate's incremental mode prints "already up to date" and spends nothing on unchanged files, so a full whitelist stays cheap.

Its output rules apply unchanged: `AGENTS.md` / `CLAUDE.md` become `.zh.md` next to the source; `SKILL.md` becomes `.tiga/translations/{parent-dir-name}-SKILL.md`.

**Freshness check (`dry-run` only):** do not invoke tiga-translate. For each whitelist entry, compute its output path per the rules above and classify it:

1. Output path does not exist → **missing translation**.
2. Output exists → determine its baseline time the way tiga-translate does: if the translation is git-tracked with no uncommitted modifications, use `git log -1 --format=%ai -- <translation>`; otherwise use its mtime. If the source changed after that baseline (per `git status` and `git log`) → **stale translation**; otherwise → **up to date**.

Print the three groups as lists.

### Phase 4: Audit

Runs in `dry-run`, `update`, `check`, and `fix`. Skipped in `init` — files just generated from current repository evidence have nothing to drift from yet.

Read [references/audit.md](references/audit.md) and follow it. It covers the discovery inputs, the `[PHANTOM]` / `[MISSING]` / `[STALE]` / `[MISMATCH]` / `[ORDER]` checks, the report format, the fix priority order, and the interactive fix flow.

Mode differences:

- `dry-run`, `update`, `check`: report only, write nothing.
- `fix`: after the report, run the interactive fix flow, then return to Phase 3 with the list of modified governance files (`CLAUDE.md` / `AGENTS.md` at any level) to sync their translations. Do not pass `README.md` or `docs/` files — their translations land in the git-ignored `.tiga/translations/`, so syncing them has no lasting effect.
- `--scope` narrows the set of audited documents; `--verbose` appends the `[OK]` section.

### Phase 5: Summary

Print a final summary covering:

- Governance files generated, skipped (with reason), or failed.
- Translation results counted by status: new / incremental update / already up to date / full re-translation / failed. In `dry-run`, the missing / stale / up-to-date counts instead.
- Audit findings counted by category, and which fixes were applied vs. skipped.
- Any phase that was skipped, with the reason.

In no-argument runs, close by listing the five modes: `init`, `dry-run`, `update`, `check`, `fix`.
