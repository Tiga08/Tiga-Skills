# Templates

Templates for the governance files generated in Phase 2 of tiga-gen-governance.

## AGENTS.md Template

```markdown
# [Repo name — one-line positioning]

[One paragraph: repository purpose, tech stack, and core constraints.]

## Structure

| Directory | Purpose | Authority |
|-----------|---------|-----------|
| `dir/` | One-line description | primary / derived / config |

[The Authority column marks how authoritative each directory's content is.]
[If a subdirectory has its own CLAUDE.md, note it below the table.]

## Markdown Generation

- Create Markdown files only when explicitly requested.
- Save generated Markdown under `.tiga/agent-res/markdown/` unless the user specifies another path; create the directory if it does not exist.
- Name generated Markdown files `YYYY-MM-DD_{purpose}.md`.
- Exceptions:
  - Translations stay beside their source file.
  - Project governance files such as `CLAUDE.md`, `AGENTS.md`, `README.md`, and `CHANGELOG.md` stay at their conventional locations.

## Skills

- Create custom skills in the project's `.agents/skills` directory.
- Make `.codex/skills` and `.claude/skills` symlinks pointing to `.agents/skills`.
- Keep all reusable skill source files in `.agents/skills` so every supported agent shares one skill library.

## Boundaries

**Always:**

[3–5 mandatory behaviors for this repository.]

**Ask First:**

[3–5 operations requiring user confirmation.]

Focus on:

- Creating or deleting files.
- Modifying core configuration.
- Changing public APIs.
- Changing build, deployment, or dependency behavior.

**Never:**

[3–5 strictly prohibited operations.]

Focus on:

- Fabricating content.
- Bypassing tests or validation.
- Leaking credentials or private data.
- Silently changing public behavior.

## Instruction Priority

1. Explicit user instructions
2. Subdirectory `CLAUDE.md` rules
3. This `AGENTS.md`
4. Evidence from repository files and existing style conventions
```

## Root CLAUDE.md Template

```markdown
@AGENTS.md

## Constraints

[1–5 operational constraints for the root project.]

Cover where relevant:

- Editing style.
- Dependency management.
- Testing requirements.
- Preservation of existing architecture, style, and public APIs.

## Common Gotchas

[1–5 pitfalls that newcomers, including AI agents, commonly hit.]

Format each item as:

1. **Short title.** Explain why it is a pitfall and describe the correct approach.
```

## Subdirectory CLAUDE.md Template

```markdown
# [Directory name] — Operational Rules

[One paragraph: responsibilities and ownership semantics.]

## Purpose

[This directory's core function and content type.]

## Rules

[3–5 operational rules specific to this directory.]

Requirements:

- Include at least one constraint that is not already present in the root `CLAUDE.md`.
- Cover read/write permissions where relevant.
- Cover the expected modification workflow.
- Cover formatting, validation, or review requirements where relevant.
```
