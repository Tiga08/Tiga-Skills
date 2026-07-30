---
name: tiga-update-skills
description: "Audit and update local Agent Skills against current Claude Code, Codex, and Agent Skills guidance, checking every skill in `.agents/skills` by default or one named or path target when supplied; use for skill quality, compatibility, metadata, invocation-policy, or official-spec drift reviews."
---

# Tiga Update Skills

Review local skills against a versioned official baseline, then apply only confirmed, evidence-backed updates.

**Arguments:** parse the invocation text as `[check|update] [<skill-name-or-path>] [--official]`. Claude Code also exposes it as `$ARGUMENTS`.

- No arguments: run `check` on every direct skill entry under `.agents/skills/`.
- `check`: report only; never write files.
- `update`: show findings and proposed diffs, then update the selected skill or skills.
- `<skill-name-or-path>`: limit the run to one skill. Resolve a bare name under `.agents/skills/`; resolve `tiga-update-skills` to this skill's source when it is not registered there.
- `--official`: also check the remote official documents. Always do this when the selected target is `tiga-update-skills`.

Reject unknown flags, more than one mode, or more than one target.

## Workflow

### 1. Preflight

1. Locate the repository root with `git rev-parse --show-toplevel`; stop if there is no repository.
2. Read the applicable `AGENTS.md` / `CLAUDE.md` instructions before inspecting targets.
3. Snapshot `git status --short`. In `update`, preserve unrelated changes and never overwrite a pre-existing dirty target without showing its diff and obtaining confirmation.
4. Resolve targets without treating registry links as owned source:
   - With no target, inspect every direct directory or symlink under `.agents/skills/` that exposes `SKILL.md`.
   - With a bare name, inspect `.agents/skills/<name>/`.
   - With a path, accept either a skill directory or its `SKILL.md`.
   - For this skill, use the directory containing this `SKILL.md`.
5. Read through symlinks for audit, but report the resolved source. Never update a resolved target outside the current repository unless the user explicitly placed that source in scope.

### 2. Establish the Baseline

Read [review-rules.md](references/review-rules.md) completely. It separates portable Agent Skills requirements from Claude Code extensions and Codex metadata.

Use the bundled official snapshots as the normal offline baseline:

- [Claude skill-creator](references/official/claude-skill-creator.md)
- [Codex skill-creator](references/official/codex-skill-creator.md)
- [snapshot manifest](references/official/sources.json)

When `--official` is set or this skill is the target, run:

```bash
python3 <skill-dir>/scripts/refresh-official-docs.py --check
```

Set `<skill-dir>` to the directory containing this `SKILL.md`; do not assume the current working directory is the skill directory. Interpret exit codes as `0` current, `1` remote content changed or a snapshot is missing, and `2` the remote check failed. In `check`, report drift without writing. In `update`, first run the command again with `--diff`, review the complete upstream changes, then run `--update`. Re-read both official documents fully and update `references/review-rules.md`, the templates under `assets/`, scripts, `SKILL.md`, and `agents/openai.yaml` only where the new requirements justify a change.

Never treat an upstream workflow preference as a format requirement unless the product documentation or Agent Skills specification makes it one.

### 3. Audit

Run the deterministic structural check:

```bash
python3 <skill-dir>/scripts/audit-skills.py [<skill-name-or-path>]
```

Then perform the semantic pass the script cannot:

1. Read each target's `SKILL.md` completely and load every directly referenced file needed to validate a claim.
2. Verify the description states both capability and concrete trigger scope without over-triggering.
3. Verify instructions are imperative, focused, internally consistent, and no longer than needed; keep `SKILL.md` below 500 lines and use progressive disclosure.
4. Verify bundled scripts, references, and assets are necessary, reachable, and documented from `SKILL.md`; test every modified script.
5. Verify portable core fields, Claude Code-only fields, and `agents/openai.yaml` in their own compatibility layers. Do not delete a valid product extension merely to satisfy a stricter portable validator.
6. Verify commands, paths, dependencies, invocation policy, and output contracts against the repository and current official baseline.
7. Check that generated Chinese translations required by repository instructions are present and current.

Use [review-report-template.md](assets/review-report-template.md) for the report structure.

### 4. Update

Run only in `update`.

1. Order fixes by `[ERROR]`, `[WARNING]`, then `[UPDATE]`.
2. Show the concrete change and why the official or repository evidence requires it.
3. Preserve the skill's name, intended behavior, supported clients, and local conventions unless the evidence proves they are stale.
4. Apply the smallest coherent patch. Do not reformat unrelated content or add speculative resources.
5. When changing a `SKILL.md`, invoke `tiga-translate` on the containing skill directory so its mirrored Chinese translation stays synchronized.
6. Re-run the structural audit, every modified script's smallest relevant test, and any repository-specific validator.

For a new or substantially rebuilt skill, start from [skill-template.md](assets/skill-template.md) and optionally [openai-template.yaml](assets/openai-template.yaml). The templates are a baseline, not a reason to overwrite justified product-specific fields.

### 5. Summary

Report:

- selected and skipped targets, including resolved symlink sources;
- official snapshot status and the manifest timestamp;
- findings and applied or deferred fixes by severity and compatibility layer;
- exact validation commands and outputs;
- remaining items that require user judgment.

In `check`, state explicitly that no files were changed.
