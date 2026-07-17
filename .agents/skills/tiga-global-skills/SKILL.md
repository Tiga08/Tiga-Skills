---
name: tiga-global-skills
description: Manage the Tiga-Skills global skill registry (02-agent-skills/) and its README metadata via manage-skills.sh and the root descriptions-zh.conf — set up user-level symlinks, add or remove skills, maintain Chinese descriptions, list entries, check link health and frontmatter compliance, and regenerate the README skill table. Use when registering, removing, or documenting globally shared skills in this repository; for a project's own .agents/skills/, use tiga-local-skills.
argument-hint: "setup|add|add-custom|remove|list|check|update-readme [args]"
compatibility: Only works inside the Tiga-Skills repository (drives 04-scripts/manage-skills.sh)
---

Manage the skills registered in `02-agent-skills/` via the management script — every operation runs through `./04-scripts/manage-skills.sh <operation> [args]`. Skills are stored flat: each entry is a symlink directly under `02-agent-skills/`, and its source (e.g., `superpowers`, `custom-skills`) is inferred by resolving the symlink target and used only for `list`/README grouping. README descriptions come only from the root `descriptions-zh.conf`.

**Arguments:** One positional operation argument is required.

- Positional operation (required, one of):
  - `setup` — create user-level symlinks (`~/.claude/skills`, `~/.codex/skills/tiga-skills`).
  - `add <path> [--name <name>]` — register a skill from an external path.
  - `add-custom <name>` — register a custom skill from `03-custom-skills/`.
  - `remove <name>` — remove a skill registration by name.
  - `list` — list registered skills grouped by source.
  - `check` — verify health of skill symlinks and project-level links, plus frontmatter compliance for in-repo sources and project-level skills.
  - `update-readme` — refresh the README skill list.

**No-argument behavior:** If the operation argument is missing or not one of the seven above, do not guess. Use `AskUserQuestion` to let the user choose among the four most common operations — `add` / `remove` / `list` / `check` — noting in the option descriptions that `setup`, `add-custom`, and `update-readme` can be entered via Other. Then collect any missing required arguments (source path for `add`, skill name for `add-custom` / `remove`).

## Workflow

### Phase 1: Resolve Repo & Operation

Locate the repository root and confirm the management script exists — this skill only works inside the Tiga-Skills repository:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
test -x "$REPO_ROOT/04-scripts/manage-skills.sh"
```

If the script is missing, report that this skill is only usable inside the Tiga-Skills repository and stop.

Then parse the operation and its arguments. If the operation is missing or invalid, follow **No-argument behavior** above.

### Phase 2: Execute Operation

Before `add`, `add-custom`, or `update-readme`, maintain the README metadata:

1. Read the affected `SKILL.md` and the root `descriptions-zh.conf`.
2. Prepare `<name>.description` from the skill's current behavior in Simplified Chinese. Keep it concise while including its core function, applicable context, a short usage guide, and every user-facing positional argument, operation or mode, and flag. If the skill has no fixed parameters, state the natural-language inputs it expects. Exclude options used only by internal implementation commands.
3. If the skill's core function, invocation, or parameters change, update this field. Write the description from the actual current behavior.
4. For a new skill, show the proposed description in the registration confirmation. Do not modify `descriptions-zh.conf` before the user confirms. After confirmation, write the config entry and then run the add command. The script rejects additions whose description is missing.

Dispatch to the matching section under **Operation Details**.

**Confirmation policy** (per AGENTS.md "Ask First: registering, removing skills"):

- `add` / `add-custom` / `remove` — always confirm via `AskUserQuestion` before executing, showing what will happen.
- `setup` — confirm only when the pre-check finds a conflicting link; if both user-level links are already correct or absent, execute directly.
- `list` / `check` / `update-readme` — read-only or idempotent; execute directly without confirmation.

### Phase 3: Report

Show the command output and summarize: which entries changed, which README metadata fields changed, that the README was refreshed automatically (`add` / `add-custom` / `remove` run `update-readme` themselves — no manual follow-up needed), and any remaining warnings.

## Operation Details

### setup

The script prompts interactively with `read` when a link conflicts, which fails (EOF, non-zero exit under `set -euo pipefail`) when run through the non-interactive Bash tool. So pre-check both user-level links with read-only commands first:

- `~/.claude/skills` — should be a symlink to `<REPO_ROOT>/02-agent-skills`.
- `~/.codex/skills/tiga-skills` — should be a symlink to the same target.

Each path is in one of four states: absent / correct symlink / symlink to another target / real directory (or other file).

- All correct or absent → run `./04-scripts/manage-skills.sh setup` directly.
- Any conflict → ask per conflicting path via `AskUserQuestion` (update the link / keep and skip), then run setup piping the answers in prompt order (claude first, then codex; only conflicting paths produce a prompt), e.g. `printf 'y\n' | ./04-scripts/manage-skills.sh setup`.

### add

Pre-check that the source path exists and contains `SKILL.md`. If `02-agent-skills/<name>` already exists, the script exits with an error — in that case ask via `AskUserQuestion` with three options: `remove` the old entry first and re-add, register under a different name with `--name`, or cancel.

Registering an external skill requires user confirmation per AGENTS.md — covered by the confirmation policy above. Before confirmation, prepare and display the Chinese description that would be written to `descriptions-zh.conf`, but do not write it yet.

### add-custom

Pre-check that `03-custom-skills/<name>` exists. If not, scan `03-custom-skills/` for directories containing `SKILL.md` and let the user pick from the candidates. On a name conflict in `02-agent-skills/`, handle like `add` but without the rename option: `remove` then re-add, or cancel.

### remove

Before confirming, show the entry as `name → target (category)`. Note that the script deletes the symlink and its matching `descriptions-zh.conf` metadata, but never touches the link target.

### list / check / update-readme

Execute directly. Before `update-readme`, compare the affected skill's current core behavior with its config entry and refresh stale descriptions. If `check` exits non-zero, summarize the failures and suggest fixes by category: for broken links, `remove` the entry or repair the upstream path and re-`add`; for frontmatter violations, edit the source `SKILL.md` (under `03-custom-skills/` or `.agents/skills/`).

## Notes

- `add-custom` creates symlinks directly under `02-agent-skills/` with relative paths (`../03-custom-skills/<name>`).
- `add` converts paths under `$HOME` to user-portable relative symlinks (e.g., `../../../AG-Tools/superpowers/skills/<name>`). This assumes the layout `~/Projects/Tiga/Skills` (this repo) and `~/Projects/AG-Tools`; paths outside `$HOME` stay absolute with a portability warning.
- For entries sourced from AG-Tools, `add` / `remove` also maintain the downstream-reference list `~/Projects/AG-Tools/SKILLS-REFS.md` automatically, skipping with a warning when AG-Tools is absent; `add` recreates a missing `SKILLS-REFS.md` from its template, while `remove` only warns.
- `check` verifies every symlink under `02-agent-skills/` (target resolvable, `SKILL.md` present) plus the project-level links `.claude/skills` / `.codex/skills` → `.agents/skills` and the root `SKILLS-REFS.md` symlink (must resolve to the AG-Tools downstream-reference file). For in-repo sources and `.agents/skills/` project-level skills it also validates frontmatter compliance (name format and consistency with the registered name, description non-empty and ≤1024 characters); external sources skip frontmatter validation. Any failure makes it exit non-zero.
- `update-readme` generates grouped two-column tables (`名称` / `描述`) from `descriptions-zh.conf`, including project-level skills from `.agents/skills/`.
- If listing available external skills from AG-Tools, scan `~/Projects/AG-Tools/superpowers/skills/`.
