# AGENTS.md — Tiga-Skills

## General Rules

- Communicate with the user in **Simplified Chinese**.
- Keep technical terms, commands, code, and API names in **English**.
- Write config files (`CLAUDE.md`, `AGENTS.md`, YAML frontmatter) in **English**.
- Use **UTF-8** encoding for all files.

## Repository Overview

Tiga-Skills is an **Agent capability library** that organizes prompts, agent skills, workflows, and utility scripts into a structured, discoverable collection.

## Directory Structure

```
Tiga-Skills/
├── 00-skill-index/      # Unified index of all capabilities
├── 01-prompts/          # Reusable prompt templates
├── 02-agent-skills/     # Agent skills (SKILL.md format)
│   └── skills/          # All skills in one directory
├── 03-workflows/        # Multi-step workflow definitions
├── 04-scripts/          # Utility scripts
├── 05-custom-skills/    # User-defined custom skills
│   └── skills/          # Custom skill directory
├── agent-plan/          # Agent-generated plan files
├── AGENTS.md            # Agent behavior guidelines
├── CLAUDE.md            # Claude Code configuration
└── README.md            # Project overview (Chinese)
```

## Conventions

- **File names**: kebab-case (e.g., `my-awesome-skill`)
- **Encoding**: UTF-8
- **Content language**: Simplified Chinese for user-facing docs; English for config files (`CLAUDE.md`, `AGENTS.md`, YAML frontmatter)
- **Markdown**: follow CommonMark spec

## Skill Format

Each skill lives under `02-agent-skills/skills/{skill-name}/SKILL.md` or `05-custom-skills/skills/{skill-name}/SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: One-line description of what the skill does
agents:        # Optional: which agents to link to (default: all)
  - codex
  - agents
---
```

Followed by the skill body in Markdown.

## Adding Content

1. **Prompt** — create `01-prompts/{prompt-name}.md`
2. **Skill** — create `02-agent-skills/skills/{skill-name}/SKILL.md`
3. **Custom Skill** — create `05-custom-skills/skills/{skill-name}/SKILL.md`
4. **Workflow** — create `03-workflows/{workflow-name}.md`
5. **Script** — add to `04-scripts/` with a brief header comment
6. **Update index** — add an entry to `00-skill-index/README.md`

## Linking Agent Skills

Use `04-scripts/link-skills.sh` to link individual skills into local agent config directories:

```bash
./04-scripts/link-skills.sh              # Link to all agents
./04-scripts/link-skills.sh --codex      # Link to ~/.codex/skills only
./04-scripts/link-skills.sh --unlink     # Remove symlinks
./04-scripts/link-skills.sh --skill foo  # Process a single skill
```

The script scans both `02-agent-skills/skills/` and `05-custom-skills/skills/`. Each skill is symlinked individually, preserving existing content in the target directory.

## Importing External Skills

Use `04-scripts/manage-skills.sh` to import skills from external repositories (e.g., `khazix-skills`):

```bash
./04-scripts/manage-skills.sh import <source-path>
./04-scripts/manage-skills.sh remove <skill-name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh status
./04-scripts/manage-skills.sh update <skill-name>
```

Imported skills are tracked in `02-agent-skills/skill-registry.json`.

## Quality Standards

- Each skill must have a `name` and `description` in frontmatter.
- Descriptions should be concise (one line) and actionable.
- Prompts and workflows should include usage examples where helpful.
- Scripts must be executable and include error handling.

## Instruction Priority

1. **User's explicit instructions** — highest priority
2. **CLAUDE.md** — project-level configuration
3. **AGENTS.md** (this file) — agent behavior defaults
4. **Default model behavior** — lowest priority
