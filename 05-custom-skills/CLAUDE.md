# CLAUDE.md — 05-custom-skills

This directory holds user-authored skills. Unlike `02-agent-skills/`, content here is **freely editable** — no registry tracking, no hash verification. Users create and maintain skills directly.

## File Structure

| Path | Purpose |
|------|---------|
| `skills/{name}/SKILL.md` | Skill definition (user-authored) |
| `README.md` | Format spec and usage guide |

## Read Rules

1. **Same SKILL.md format as `02-agent-skills/`.** Custom skills follow the identical frontmatter schema — see `02-agent-skills/CLAUDE.md` → File Format Standards for field constraints.
2. **`link-skills.sh` auto-discovers this directory.** The script scans both `02-agent-skills/skills/` and `05-custom-skills/skills/` — no additional configuration is needed to include custom skills in linking.

## Write Rules

1. **Follow the SKILL.md format.** Every skill must have a `SKILL.md` with valid `name` and `description` frontmatter fields. See `02-agent-skills/CLAUDE.md` → File Format Standards.
2. **Directory name must match the `name` field.** The skill directory name and the frontmatter `name` value must be identical (both kebab-case).
3. **Run `sync-index.sh` after adding or removing a skill.** The script regenerates the "自定义 Skills" section in `00-skill-index/README.md`. Other index sections are not affected.
4. **Do not place externally-sourced skills here.** Skills from external repositories belong in `02-agent-skills/` via `manage-skills.sh import`. This directory is exclusively for user-authored content.
