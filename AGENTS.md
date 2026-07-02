# Tiga-Skills: Centralized Agent Skills Repository

Tiga-Skills is a content and script repository that centrally registers external and custom Agent Skills via flat symlinks, exposing them to Claude Code and Codex. This repository contains no application code, build systems, or runtime dependencies. The core constraint is that `02-agent-skills/` serves only as a flat symlink registry, custom skill source files live in `03-custom-skills/`, and all skill registration and removal must go through `./04-scripts/manage-skills.sh`.

## Structure

| Directory | Purpose | Authority |
| --------- | ------- | --------- |
| `.agents/skills/` | Project-level skills shared across agents; `.claude/skills` and `.codex/skills` symlink here | primary |
| `.claude/` | Claude Code project configuration; `skills/` is a symlink to `.agents/skills` | config |
| `.codex/` | Codex project configuration; `skills/` is a symlink to `.agents/skills` | config |
| `01-prompts/` | Reusable prompt templates | primary |
| `02-agent-skills/` | Flat Agent Skills registry; skill entries are symlinks placed directly in this directory, grouping by source is shown only in README | derived |
| `03-custom-skills/` | Source files for project-internal custom skills | primary |
| `04-scripts/` | Scripts for skill registration, removal, setup, link health checks, and README updates | primary |
| `agent-plan/` | Agent-generated plans and drafts; git-ignored | derived |
| `Todo/` | Local to-dos and working notes; git-ignored | derived |

Only root-level governance files are maintained. Do not generate subdirectory `CLAUDE.md` files unless the user explicitly requests it.

## Markdown Generation

- Only create Markdown files when explicitly requested by the user.
- Unless the user specifies another path, save generated Markdown under `agent-plan/`; create the directory if it does not exist.
- Name generated Markdown files `YYYY-MM-DD_{purpose}.md`.
- Exceptions:
  - Translation files follow the md-to-zh skill's output rules: governance files (`AGENTS.md`, `CLAUDE.md`) are translated as `.zh.md` next to the source; all other files are output to `agent-plan/translations/`.
  - Project governance files such as `CLAUDE.md`, `AGENTS.md`, `README.md`, and `CHANGELOG.md` stay at their conventional locations.

## Skills

### Project-level Skills

- Project-level skills live in `.agents/skills/<name>/SKILL.md`.
- `.claude/skills` and `.codex/skills` are symlinks pointing to `.agents/skills`, so all supported agents share one skill library.
- Project-level skills are for operating this repository itself (e.g., `manage-global-skills`).

### Registry Skills

- Create and edit registry skill source files in `03-custom-skills/`.
- Use `./04-scripts/manage-skills.sh add-custom <name>` to register a custom skill to `02-agent-skills/`.
- Use `./04-scripts/manage-skills.sh add <path> [--name <name>]` to register an external skill. For paths under `$HOME`, `add` creates a user-portable relative symlink (e.g., `../../../AG-Tools/...`), assuming this repository lives at `~/Projects/Tiga/Skills` and AG-Tools at `~/Projects/AG-Tools`.
- Use `./04-scripts/manage-skills.sh remove <name>` to remove a skill registration.
- Use `./04-scripts/manage-skills.sh check` to verify the health of skill symlinks and project-level links.
- After any skill registration, removal, or metadata change, run `./04-scripts/manage-skills.sh update-readme` to refresh the `README.md` skill list.

## Boundaries

**Always:**

- Read relevant files before modifying them.
- Treat `02-agent-skills/` as a flat symlink registry; never edit skill content directly within it.
- When modifying custom skills, edit the source files under `03-custom-skills/<name>/`.
- Use `./04-scripts/manage-skills.sh` for skill registration, removal, and user-level setup.
- Keep the `README.md` skill list consistent with the current registration state of `02-agent-skills/`.

**Ask First:**

- Creating or deleting skills, prompts, scripts, or governance files.
- Overwriting existing `AGENTS.md`, `CLAUDE.md`, or `README.md`.
- Modifying `.claude/`, `.gitignore`, or other core configuration.
- Registering, removing, or renaming skills.
- Pulling or syncing content from external upstream repositories.

**Never:**

- Directly modify external skill source files that are symlinked from `02-agent-skills/`.
- Manually create or delete symlinks directly under `02-agent-skills/` to bypass `manage-skills.sh`.
- Fabricate skill names, sources, or descriptions.
- Leak, commit, or output `.env`, tokens, cookies, private keys, or other sensitive data.
- Delete, bypass, or weaken validation steps in order to pass checks.

## Instruction Priority

1. Explicit user instructions
2. This `AGENTS.md`
3. Evidence from the current repository files and directory structure
4. Existing style and conventions
