@AGENTS.md

# Tiga-Skills: Claude Code Operating Guide

## Constraints

- Preserve this repository as a content-and-Bash management repository. Do not introduce an application framework, build system, or runtime dependency unless the user explicitly requests it.
- Edit each skill at its authoritative location: project-operation skills in `.agents/skills/`, custom registry skills in `03-custom-skills/`, and external skills in their upstream repositories. Treat `02-agent-skills/` as derived state.
- Use `./04-scripts/manage-skills.sh` for registry and user-level link operations. After registry or skill-metadata changes, run `update-readme`, then `check`.
- Inspect external upstream status before proposing a sync, and obtain user confirmation before pulling or registering upstream changes.
- Keep scripts executable Bash encoded as UTF-8, follow the existing direct command style, and write new or changed script comments in Simplified Chinese. Run `bash -n` on modified shell scripts before finishing.

## Common Gotchas

1. **Confusing the three skill locations.** `.agents/skills/` contains project-operation skills, `03-custom-skills/` contains custom registry sources, and `02-agent-skills/` contains only flat registration symlinks. Resolve a registry link before deciding which source is safe to edit.

2. **Bypassing `manage-skills.sh` for symlink management.** Manual link changes can leave registration, user-level discovery, and README metadata inconsistent. Use the management script for `setup`, `add`, `add-custom`, and `remove`.

3. **Editing the generated README skill table by hand.** The section between `BEGIN SKILL LIST` and `END SKILL LIST` is derived from registered links and `SKILL.md` metadata. Refresh it with `update-readme`, then verify link health with `check`.

4. **Treating `.tiga/` as authoritative project content.** `.tiga/` is the git-ignored entry point for user-local files: Agent-generated plans and drafts belong in `.tiga/agent-res/markdown/`, personal plans belong in `.tiga/Todo.md`, and future local modules may live alongside them. Only promote its content to formal project directories when the user explicitly requests it.

5. **Using the old directory layout.** The current repository uses `01-prompts/`, `02-agent-skills/`, `03-custom-skills/`, and `04-scripts/`. Do not reintroduce removed directories such as `00-skill-index/`, `03-workflows/`, or `05-custom-skills/`.

## Common Commands

```bash
./04-scripts/manage-skills.sh setup
./04-scripts/manage-skills.sh add <path> [--name <name>]
./04-scripts/manage-skills.sh add-custom <name>
./04-scripts/manage-skills.sh remove <name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh check
./04-scripts/manage-skills.sh update-readme
```
