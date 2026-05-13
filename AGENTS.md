# AGENTS.md — Agent Behavior Guidelines

## General Rules

- Communicate with the user in **Simplified Chinese**.
- Keep technical terms, commands, code, and API names in **English**.
- Write config files (`CLAUDE.md`, `AGENTS.md`, YAML frontmatter) in **English**.
- Use **UTF-8** encoding for all files.

## Naming Conventions

- File and directory names: **kebab-case** (e.g., `code-review`, `auto-deploy`)
- Skill directories: `02-agent-skills/{skill-name}/SKILL.md`
- Prompt files: `01-prompts/{prompt-name}.md`
- Workflow files: `03-workflows/{workflow-name}.md`

## Adding Content

### Adding a Prompt

1. Create `01-prompts/{prompt-name}.md`.
2. Include a clear title and purpose at the top.
3. Add an entry to `00-skill-index/README.md`.

### Adding a Skill

1. Create directory `02-agent-skills/{skill-name}/`.
2. Create `SKILL.md` with YAML frontmatter (`name`, `description`).
3. Write the skill body in Markdown.
4. Add an entry to `00-skill-index/README.md`.

### Adding a Workflow

1. Create `03-workflows/{workflow-name}.md`.
2. Define steps, triggers, and expected outcomes.
3. Add an entry to `00-skill-index/README.md`.

### Adding a Script

1. Add the script to `04-scripts/`.
2. Include a brief header comment explaining purpose and usage.
3. Add an entry to `00-skill-index/README.md`.

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
