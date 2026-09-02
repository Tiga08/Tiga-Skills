# Tiga-Skills: Centralized Agent Skills Repository

Tiga-Skills registers external and custom Agent Skills and exposes them to Claude Code and Codex. It holds content, Bash, and standard-library Python utilities — no application code, build system, or package-managed runtime. The core constraint: `03-skills/` is the unified skill directory (custom skills as real directories, external skills as symlinks), and every registration or removal goes through `./02-scripts/manage-skills.sh`.

## Structure

| Path | Purpose | Authority |
| --- | --- | --- |
| `.agents/skills/` | Project-operation skills; `.claude/skills` and `.codex/skills` are symlinks to it, so every agent shares one library | primary |
| `03-skills/` | Unified skill directory — custom skills as real directories, external skills as symlinks | primary |
| `descriptions-zh.conf` | Authoritative Chinese descriptions the README skill table is generated from | primary |
| `SKILLS-INDEX.md` | Symlink to `~/Projects/AG-Tools/SKILLS-INDEX.md`, the AG-Tools-wide skill index | derived |
| `SKILLS-REFS.md` | Symlink to `~/Projects/AG-Tools/SKILLS-REFS.md`, the downstream-reference list | derived |

The table lists only paths whose purpose or authority is not self-evident; the rest of the tree describes itself. The rendered catalog of registered skills lives in `README.md`.

## Commands

```bash
./02-scripts/manage-skills.sh setup                      # user-level symlinks
./02-scripts/manage-skills.sh add <path> [--name <name>] # register an external skill
./02-scripts/manage-skills.sh remove <name>              # remove an external skill symlink
./02-scripts/manage-skills.sh list
./02-scripts/manage-skills.sh check                      # skill directory and frontmatter health
./02-scripts/manage-skills.sh update-readme              # regenerate the README skill table
```

For a path under `$HOME`, `add` writes a user-portable relative symlink (e.g. `../../../AG-Tools/...`); the required checkout layout is documented in the root `README.md`.

## Boundaries

**Always:**

- Edit a skill at its source: project-operation skills in `.agents/skills/<name>/`, custom skills in `03-skills/<name>/`, external skills in their own upstream repository.
- Route registration, removal, and user-level link setup through `./02-scripts/manage-skills.sh` — hand-made link changes leave registration, user-level discovery, and README metadata out of sync.
- Keep `descriptions-zh.conf` aligned with what each skill actually does; its `<name>.description` is what the README table's description column is built from, and `<name>.arguments` is the fallback for the parameter column when a skill has no `argument-hint` frontmatter (external skills, whose sources must not be edited).
- After any registration, removal, or `descriptions-zh.conf` change, run `update-readme`, then `check`.
- Keep `02-scripts/*.sh` executable UTF-8 Bash in the existing direct-command style, and run `bash -n` on any shell script you modify. Invoke skill-local Python helpers through `python3` and follow their owning `SKILL.md`; there is no shared test suite.

**Ask First:**

- Creating or deleting skills, prompts, or scripts.
- Registering, removing, or renaming a skill.
- Pulling or registering content from an external upstream repository — inspect its status first.
- Creating a subdirectory `CLAUDE.md`; this repository intentionally keeps governance at the root unless the user requests a narrower file.

**Never:**

- Modify an external skill source reached through a `03-skills/` symlink; that content belongs to an upstream repository.
- Create or delete symlinks under `03-skills/` by hand, bypassing `manage-skills.sh`.
- Hand-edit the README block between `<!-- BEGIN SKILL LIST -->` and `<!-- END SKILL LIST -->`.
- Fabricate skill names, sources, or descriptions.
- Reintroduce retired top-level layouts such as `00-skill-index/`, `02-agent-skills/`, `03-workflows/`, or `05-custom-skills/`.
