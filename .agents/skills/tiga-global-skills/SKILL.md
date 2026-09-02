---
name: tiga-global-skills
description: Manage the Tiga-Skills global skill directory (03-skills/) and its README metadata via manage-skills.sh and the root descriptions-zh.conf — set up user-level symlinks, add or remove external skills, maintain Chinese descriptions, list entries, check directory health and frontmatter compliance, and regenerate the README skill table. Use when registering, removing, or documenting globally shared skills in this repository; for a project's own .agents/skills/, use tiga-local-skills.
argument-hint: "setup|add|remove|list|check|update-readme [args]"
arguments: [operation]
disable-model-invocation: true
compatibility: Only works inside the Tiga-Skills repository (drives 02-scripts/manage-skills.sh)
---

Manage the skills in `03-skills/` via the management script — every operation runs through `./02-scripts/manage-skills.sh <operation> [args]`. Custom skills are real directories directly under `03-skills/`; external skills are symlinks. Source category (e.g., `custom-skills`, `baoyu-skills`) is inferred by entry type and symlink target and used only for `list`/README grouping. README descriptions come only from the root `descriptions-zh.conf`.

**Arguments:** One positional operation argument is required.

本次调用：`$ARGUMENTS` — 操作 `$operation`

- Positional operation (required, one of):
  - `setup` — create user-level symlinks (`~/.claude/skills`, `~/.codex/skills/tiga-skills`).
  - `add <path> [--name <name>]` — register an external skill as a symlink.
  - `remove <name>` — remove an external skill symlink (refuses to delete real directories).
  - `list` — list registered skills grouped by source.
  - `check` — verify health of skill directory and project-level links, plus frontmatter compliance for in-repo sources and project-level skills.
  - `update-readme` — refresh the README skill list.

**No-argument behavior:** If the operation argument is missing or not one of the six above, do not guess. Use `AskUserQuestion` to let the user choose among the four most common operations — `add` / `remove` / `list` / `check` — noting in the option descriptions that `setup` and `update-readme` can be entered via Other. Then collect any missing required arguments (source path for `add`, skill name for `remove`).

## Workflow

### Phase 1: Resolve Repo & Operation

Locate the repository root and confirm the management script exists — this skill only works inside the Tiga-Skills repository:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
test -x "$REPO_ROOT/02-scripts/manage-skills.sh"
```

If the script is missing, report that this skill is only usable inside the Tiga-Skills repository and stop.

Take `$operation` as the operation and collect its arguments from `$ARGUMENTS`. If the operation is missing or invalid, follow **No-argument behavior** above.

### Phase 2: Execute Operation

Before `add` or `update-readme`, maintain the README metadata:

1. Read the affected `SKILL.md` and the root `descriptions-zh.conf`.
2. Prepare `<name>.description` from the skill's current behavior in Simplified Chinese — its core function and applicable context only. Parameters belong in the `argument-hint` frontmatter field (or, for external skills whose source must not be touched, in the `<name>.arguments` fallback field); do not enumerate them in the description.
3. If the skill's core function or invocation changes, update these fields. Write them from the actual current behavior.
4. For a new skill, show the proposed description in the registration confirmation. Do not modify `descriptions-zh.conf` before the user confirms. After confirmation, write the config entry and then run the add command. The script rejects additions whose description is missing.

Dispatch to the matching section in [operations.md](${CLAUDE_SKILL_DIR}/references/operations.md).

**Confirmation policy** (per AGENTS.md "Ask First: registering, removing skills"):

- `add` / `remove` — always confirm via `AskUserQuestion` before executing, showing what will happen.
- `setup` — confirm only when the pre-check finds a conflicting link; if both user-level links are already correct or absent, execute directly.
- `list` / `check` / `update-readme` — read-only or idempotent; execute directly without confirmation.

### Phase 3: Report

Show the command output and summarize: which entries changed, which README metadata fields changed, that the README was refreshed automatically (`add` / `add-custom` / `remove` run `update-readme` themselves — no manual follow-up needed), and any remaining warnings.
