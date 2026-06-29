---
name: manage-skills
description: Manage agent skills — add, remove, list, and configure skill symlinks in Tiga-Skills
---

Manage the skills registered in `02-agent-skills/` via the management script.

## Available Operations

Parse the user's intent and map it to one of the following commands:

| Intent | Command |
| ------ | ------- |
| Set up user-level symlinks | `./04-scripts/manage-skills.sh setup` |
| Add a skill from an external path | `./04-scripts/manage-skills.sh add <path> [--name <name>]` |
| Add a custom skill from `03-custom-skills/` | `./04-scripts/manage-skills.sh add-custom <name>` |
| Remove a skill | `./04-scripts/manage-skills.sh remove <name>` |
| List registered skills | `./04-scripts/manage-skills.sh list` |
| Update the README skill list | `./04-scripts/manage-skills.sh update-readme` |

## Workflow

1. **Clarify intent** — determine which operation the user wants and what arguments are needed.
2. **Confirm before acting** — before `add`, `add-custom`, or `remove`, show the user what will happen and ask for confirmation via `AskUserQuestion`.
3. **Execute** — run the corresponding command.
4. **Report** — show the command output and summarize the result.

## Notes

- The `add` command creates absolute symlinks for external skills; `add-custom` creates relative symlinks for project-internal skills.
- Both `add` and `remove` automatically run `update-readme`，但脚本直接使用 SKILL.md 中的英文 description。执行完脚本后，需要手动将 README.md `## 技能清单` 表格中的 Description 栏翻译为简体中文。
- For `setup`, the script creates:
  - `~/.claude/skills` → `02-agent-skills`（整个目录作为软链接）
  - `~/.codex/skills/tiga-skills` → `02-agent-skills`（子目录下的软链接）
- If listing available custom skills, scan `03-custom-skills/` for directories containing `SKILL.md`.
- If listing available external skills from AG-Tools, scan `~/Projects/AG-Tools/baoyu-skills/skills/` (or other known repos).
