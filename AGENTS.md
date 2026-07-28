# Tiga-Skills: Centralized Agent Skills Repository

Tiga-Skills registers external and custom Agent Skills through flat symlinks and exposes them to Claude Code and Codex. It holds content and Bash only — no application code, build system, or runtime dependency. The core constraint: `02-agent-skills/` is a symlink registry, custom skill sources live in `03-custom-skills/`, and every registration or removal goes through `./04-scripts/manage-skills.sh`.

## Structure

| Path | Purpose | Authority |
| --- | --- | --- |
| `.agents/skills/` | Project-operation skills; `.claude/skills` and `.codex/skills` are symlinks to it, so every agent shares one library | primary |
| `02-agent-skills/` | Flat registry — every entry is a symlink, never real content | derived |
| `03-custom-skills/` | Source files for the custom skills registered above | primary |
| `descriptions-zh.conf` | Authoritative Chinese descriptions the README skill table is generated from | primary |
| `SKILLS-INDEX.md` | Symlink to `~/Projects/AG-Tools/SKILLS-INDEX.md`, the AG-Tools-wide skill index | derived |
| `SKILLS-REFS.md` | Symlink to `~/Projects/AG-Tools/SKILLS-REFS.md`, the downstream-reference list | derived |

The table lists only paths whose purpose or authority is not self-evident; the rest of the tree describes itself. Only root-level governance files are maintained — do not create subdirectory `CLAUDE.md` files unless the user asks.

## Commands

```bash
./04-scripts/manage-skills.sh setup                      # user-level symlinks
./04-scripts/manage-skills.sh add <path> [--name <name>] # register an external skill
./04-scripts/manage-skills.sh add-custom <name>          # register a skill from 03-custom-skills/
./04-scripts/manage-skills.sh remove <name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh check                      # symlink and frontmatter health
./04-scripts/manage-skills.sh update-readme              # regenerate the README skill table
```

For a path under `$HOME`, `add` writes a user-portable relative symlink (e.g. `../../../AG-Tools/...`), assuming this repository sits at `~/Projects/Tiga/Skills` and AG-Tools at `~/Projects/AG-Tools`.

## Boundaries

**Always:**

- Edit a skill at its source: project-operation skills in `.agents/skills/<name>/`, registry skills in `03-custom-skills/<name>/`, external skills in their own upstream repository.
- Route registration, removal, and user-level link setup through `./04-scripts/manage-skills.sh` — hand-made link changes leave registration, user-level discovery, and README metadata out of sync.
- Keep `descriptions-zh.conf` aligned with what each skill actually does; its `<name>.description` is what the README table's description column is built from, and `<name>.arguments` is the fallback for the parameter column when a skill has no `argument-hint` frontmatter (external skills, whose sources must not be edited).
- After any registration, removal, or `descriptions-zh.conf` change, run `update-readme`, then `check`.

**Ask First:**

- Creating or deleting skills, prompts, or scripts.
- Registering, removing, or renaming a skill.
- Pulling or registering content from an external upstream repository — inspect its status first.

**Never:**

- Modify an external skill source reached through an `02-agent-skills/` symlink; that content belongs to an upstream repository.
- Create or delete symlinks under `02-agent-skills/` by hand, bypassing `manage-skills.sh`.
- Hand-edit the README block between `<!-- BEGIN SKILL LIST -->` and `<!-- END SKILL LIST -->`.
- Fabricate skill names, sources, or descriptions.
