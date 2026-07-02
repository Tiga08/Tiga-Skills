@AGENTS.md

# Tiga-Skills: Claude Code Operating Guide

## Constraints

- This repository is an Agent Skills management repo, not an application or library. Do not add build systems, runtime dependencies, or application frameworks unless the user explicitly requests it.
- Skill entries directly under `02-agent-skills/` must remain symlinks (flat, no source subdirectories). Do not place regular skill directories there or directly edit symlink targets.
- Project-level skills (for operating this repository) live in `.agents/skills/`. `.claude/skills` and `.codex/skills` are symlinks pointing there.
- Registry skill source files live in `03-custom-skills/`. When modifying registry skills, work in the source directory, then run `./04-scripts/manage-skills.sh update-readme` to refresh documentation.
- External skills are maintained by upstream repositories. Check upstream status before syncing external skills, and only pull or register changes after user confirmation.
- Scripts use Bash and UTF-8. Write new or modified script comments in Simplified Chinese, and maintain the existing direct, executable script style.

## Common Gotchas

1. **Treating `02-agent-skills/` as a source directory.** It is a flat symlink registry; source classification is inferred by resolving each symlink's target and shown only in README grouping — there are no physical source subdirectories. To modify registry skills, edit `03-custom-skills/`. For external skills, go to the upstream repository. Project-level skills live in `.agents/skills/`, not here.

2. **Bypassing `manage-skills.sh` for symlink management.** Manually creating or deleting symlinks causes the README skill list to diverge from actual registration state. Use `./04-scripts/manage-skills.sh` for adding, removing, setup, and list updates.

3. **Forgetting to update the README skill list.** After skill changes, run `./04-scripts/manage-skills.sh update-readme`. This command scans symlinks directly under `02-agent-skills/`, inferring each entry's category by resolving its symlink target, and extracts metadata from each `SKILL.md`.

4. **Treating `agent-plan/` or `Todo/` as authoritative content.** These directories are local drafts and working notes, excluded by `.gitignore`. Only promote their content to formal directories when the user explicitly requests it.

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
