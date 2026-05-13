# CLAUDE.md — Tiga-Skills

## Repository Overview

Tiga-Skills is an **Agent capability library** that organizes prompts, agent skills, workflows, and utility scripts into a structured, discoverable collection.

## Directory Structure

```
Tiga-Skills/
├── 00-skill-index/      # Unified index of all capabilities
├── 01-prompts/          # Reusable prompt templates
├── 02-agent-skills/     # Agent skills (SKILL.md format)
├── 03-workflows/        # Multi-step workflow definitions
├── 04-scripts/          # Utility scripts
├── agent-plan/          # Agent-generated plan files
├── AGENTS.md            # Agent behavior guidelines
├── CLAUDE.md            # This file
└── README.md            # Project overview (Chinese)
```

## Conventions

- **File names**: kebab-case (e.g., `my-awesome-skill`)
- **Encoding**: UTF-8
- **Content language**: Simplified Chinese for user-facing docs; English for config files (`CLAUDE.md`, `AGENTS.md`, YAML frontmatter)
- **Markdown**: follow CommonMark spec

## Skill Format

Each skill lives under `02-agent-skills/{skill-name}/SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: One-line description of what the skill does
---
```

Followed by the skill body in Markdown.

## Adding Content

1. **Prompt** — create `01-prompts/{prompt-name}.md`
2. **Skill** — create `02-agent-skills/{skill-name}/SKILL.md`
3. **Workflow** — create `03-workflows/{workflow-name}.md`
4. **Script** — add to `04-scripts/` with a brief header comment
5. **Update index** — add an entry to `00-skill-index/README.md`
