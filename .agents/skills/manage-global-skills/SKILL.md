---
name: manage-global-skills
description: Manage the global agent skills registry — add, remove, list, and configure skill symlinks grouped by source in Tiga-Skills
description_zh: 管理全局 agent 技能注册表 — 在 Tiga-Skills 中添加、移除、列出技能，并按来源分组配置软链接
---

Manage the skills registered in `02-agent-skills/` via the management script. Skills are stored flat: each entry is a symlink directly under `02-agent-skills/`, and its source (e.g., `superpowers`, `custom-skills`) is inferred by resolving the symlink target.

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

1. **Clarify intent** — determine which operation the user wants and what arguments are needed.
2. **Confirm before acting** — before `add`, `add-custom`, or `remove`, show the user what will happen and ask for confirmation via `AskUserQuestion`.
3. **Execute** — run the corresponding command.
4. **Report** — show the command output and summarize the result.

## Notes

- `02-agent-skills/` is flat: every skill entry is a symlink placed directly in that directory. Source classification (`superpowers`, `custom-skills`, etc.) is inferred from each symlink's target and used only for `list`/README grouping — there are no physical source subdirectories.
- `add-custom` creates symlinks directly under `02-agent-skills/` with relative paths (`../03-custom-skills/<name>`).
- `add` converts paths under `$HOME` to user-portable relative symlinks (e.g., `../../../AG-Tools/superpowers/skills/<name>`). This assumes the layout `~/Projects/Tiga/Skills` (this repo) and `~/Projects/AG-Tools`; paths outside `$HOME` stay absolute with a portability warning.
- `check` verifies every symlink under `02-agent-skills/` (target resolvable, `SKILL.md` present) plus the project-level links `.claude/skills` / `.codex/skills` → `.agents/skills`, and exits non-zero if any link is broken.
- `remove` looks up the symlink by name directly under `02-agent-skills/` — no need to specify the source category.
- Both `add` and `remove` automatically run `update-readme` to refresh the skill list.
- `update-readme` generates grouped skill tables with source descriptions, and includes project-level skills from `.agents/skills/`.
- For `setup`, the script creates:
  - `~/.claude/skills` → `02-agent-skills`（整个目录作为软链接）
  - `~/.codex/skills/tiga-skills` → `02-agent-skills`（子目录下的软链接）
- If listing available custom skills, scan `03-custom-skills/` for directories containing `SKILL.md`.
- If listing available external skills from AG-Tools, scan `~/Projects/AG-Tools/superpowers/skills/`.
