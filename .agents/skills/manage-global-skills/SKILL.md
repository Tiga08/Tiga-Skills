---
name: manage-global-skills
description: Manage the Tiga-Skills global skill registry (02-agent-skills/) and its README metadata via manage-skills.sh and the root descriptions-zh.conf — set up user-level symlinks, add or remove skills, maintain Chinese descriptions, list entries, check link health, and regenerate the README skill table. Use when registering, removing, or documenting globally shared skills in this repository; for a project's own .agents/skills/, use tiga-local-skills.
---

Manage the skills registered in `02-agent-skills/` via the management script. Skills are stored flat: each entry is a symlink directly under `02-agent-skills/`, and its source (e.g., `superpowers`, `custom-skills`) is inferred by resolving the symlink target. README descriptions come only from the root `descriptions-zh.conf`.

**Arguments:** One positional operation argument is required.

- Positional operation (required, one of):
  - `setup` — create user-level symlinks (`~/.claude/skills`, `~/.codex/skills/tiga-skills`).
  - `add <path> [--name <name>]` — register a skill from an external path.
  - `add-custom <name>` — register a custom skill from `03-custom-skills/`.
  - `remove <name>` — remove a skill registration by name.
  - `list` — list registered skills grouped by source.
  - `check` — verify health of skill symlinks and project-level links.
  - `update-readme` — refresh the README skill list.

**No-argument behavior:** If the operation argument is missing or not one of the seven above, do not guess. Use `AskUserQuestion` to let the user choose among the four most common operations — `add` / `remove` / `list` / `check` — noting in the option descriptions that `setup`, `add-custom`, and `update-readme` can be entered via Other. Then collect any missing required arguments (source path for `add`, skill name for `add-custom` / `remove`).

## Available Operations

Parse the user's intent and map it to one of the following commands:

| Intent | Command |
| ------ | ------- |
| Set up user-level symlinks | `./04-scripts/manage-skills.sh setup` |
| Add a skill from an external path | `./04-scripts/manage-skills.sh add <path> [--name <name>]` |
| Add a custom skill from `03-custom-skills/` | `./04-scripts/manage-skills.sh add-custom <name>` |
| Remove a skill (looked up by name under `02-agent-skills/`) | `./04-scripts/manage-skills.sh remove <name>` |
| List registered skills (grouped by source) | `./04-scripts/manage-skills.sh list` |
| Check health of skill symlinks and project-level links | `./04-scripts/manage-skills.sh check` |
| Update the README skill list | `./04-scripts/manage-skills.sh update-readme` |

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

Execute directly. Before `update-readme`, compare the affected skill's current core behavior with its config entry and refresh stale descriptions. If `check` exits non-zero, summarize the broken links and suggest fixes: `remove` the broken entries, or repair the upstream path and re-`add`.

## Notes

- `02-agent-skills/` is flat: every skill entry is a symlink placed directly in that directory. Source classification (`superpowers`, `custom-skills`, etc.) is inferred from each symlink's target and used only for `list`/README grouping — there are no physical source subdirectories.
- `add-custom` creates symlinks directly under `02-agent-skills/` with relative paths (`../03-custom-skills/<name>`).
- `add` converts paths under `$HOME` to user-portable relative symlinks (e.g., `../../../AG-Tools/superpowers/skills/<name>`). This assumes the layout `~/Projects/Tiga/Skills` (this repo) and `~/Projects/AG-Tools`; paths outside `$HOME` stay absolute with a portability warning.
- `check` verifies every symlink under `02-agent-skills/` (target resolvable, `SKILL.md` present) plus the project-level links `.claude/skills` / `.codex/skills` → `.agents/skills`, and exits non-zero if any link is broken.
- `remove` looks up the symlink by name directly under `02-agent-skills/` — no need to specify the source category.
- `add` and `add-custom` require `<name>.description` in the root `descriptions-zh.conf`; a missing description stops the operation before creating a symlink.
- `remove` deletes the registry symlink and its matching description entry. `add`, `add-custom`, and `remove` all automatically run `update-readme`.
- `update-readme` generates grouped two-column tables (`名称` / `描述`) from `descriptions-zh.conf`, including project-level skills from `.agents/skills/`.
- For `setup`, the script creates:
  - `~/.claude/skills` → `02-agent-skills` (the whole directory as one symlink)
  - `~/.codex/skills/tiga-skills` → `02-agent-skills` (a sub-link under the skills directory)
- If listing available custom skills, scan `03-custom-skills/` for directories containing `SKILL.md`.
- If listing available external skills from AG-Tools, scan `~/Projects/AG-Tools/superpowers/skills/`.
