# Tiga-Skills — Agent Capability Library

Tiga-Skills organizes prompts, agent skills, workflows, and utility scripts into a structured, discoverable collection. It is a pure content repository with no application code, no build system, and no runtime dependencies.

## Repository Structure

| Directory | Role | Purpose |
|-----------|------|---------|
| `00-skill-index/` | Index | Unified capability index (derived — partially regenerable) |
| `01-prompts/` | Content | Reusable prompt templates |
| `02-agent-skills/` | Content | Agent skills (SKILL.md format), including external imports tracked by `skill-registry.json` |
| `03-workflows/` | Content | Multi-step workflow definitions |
| `04-scripts/` | Tooling | Utility scripts for linking, importing, and index syncing |
| `05-custom-skills/` | Content | User-defined custom skills (isolated from imports) |
| `agent-plan/` | Scratch | Agent-generated plan files and drafts |
| `Todo/` | Scratch | Task tracking notes |

Each content directory has its own `README.md` defining format specifications and conventions.

Directories with additional layer-specific rules in their own `CLAUDE.md`: `00-skill-index/`, `02-agent-skills/`, `05-custom-skills/`.

## Source-of-Truth Rules

- `01-prompts/` is the primary source for prompt templates.
- `02-agent-skills/skills/` is the primary source for agent skill definitions. External imports are tracked in `02-agent-skills/skill-registry.json`.
- `05-custom-skills/skills/` is the primary source for user-defined skills.
- `03-workflows/` is the primary source for workflow definitions.
- `04-scripts/` is the primary source for automation scripts.
- `00-skill-index/README.md` is a derived index — aggregates entries from content directories.
- `agent-plan/` contains drafts and working notes — not authoritative.

## Working Rules

1. Read the target directory's `README.md` and `CLAUDE.md` (if present) before adding or modifying content.
2. Edit only what the task requires — do not reformat or reorganize adjacent files.
3. After adding content, update `00-skill-index/README.md` with a new entry.
4. Do not directly edit skills tracked in `skill-registry.json` — use `04-scripts/manage-skills.sh update`.
5. Use `04-scripts/link-skills.sh` to manage symlinks to local agent config directories.
6. Descriptions must accurately reflect content — do not exaggerate capabilities.
7. Communicate with the user in Simplified Chinese. Keep technical terms, commands, code, and API names in English. Write config files (`CLAUDE.md`, `AGENTS.md`, YAML frontmatter) in English. Use UTF-8 encoding, kebab-case file names, and CommonMark spec for all Markdown.

## Markdown Generation

- Create Markdown files only when explicitly requested.
- Save generated Markdown under `agent-plan/` unless the user specifies a path.
- Name generated files as `YYYY-MM-DD_{purpose}.md`.
- Create `agent-plan/` if it does not exist.
- Exceptions: translations stay next to the source file; project files (`CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`) stay at conventional locations.

## Boundaries

**Always:**
- Read the target directory's `README.md` before modifying its contents.
- Verify `name` and `description` exist in SKILL.md frontmatter.
- Update `00-skill-index/README.md` when adding or removing content.
- Use `link-skills.sh` and `manage-skills.sh` for symlink and import operations.

**Ask First:**
- Creating or deleting skill, prompt, or workflow files.
- Modifying `skill-registry.json` or imported skill content.
- Changing directory structure or renaming directories.
- Running destructive operations (`manage-skills.sh remove`, `link-skills.sh --unlink`).

**Never:**
- Fabricate skill descriptions that don't match actual content.
- Directly edit imported skills — use `manage-skills.sh update`.
- Delete or overwrite `skill-registry.json` manually.
- Create symlinks to agent config directories without using `link-skills.sh`.
- Treat `agent-plan/` content as authoritative.

## Instruction Priority

When instructions conflict, follow this order:

1. Explicit user instructions
2. Directory-level `CLAUDE.md` rules for the content being edited
3. Repository constraints in this file (`AGENTS.md`)
4. Evidence in source-of-truth directories
5. Existing style and conventions in source materials
6. Default model behavior
