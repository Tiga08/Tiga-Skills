@AGENTS.md

## Constraints

- Keep this a content-and-Bash repository. Do not introduce an application framework, build system, or runtime dependency unless the user asks for one.
- Keep scripts executable UTF-8 Bash in the existing direct-command style, and run `bash -n` on any shell script you modify.

## Common Gotchas

1. **Confusing the three skill locations.** `.agents/skills/` holds project-operation skills, `03-custom-skills/` holds custom registry sources, and `02-agent-skills/` holds only registration symlinks. Resolve a registry link to its target before deciding which source is safe to edit.

2. **Treating `.tiga/` as project content.** It is git-ignored and never authoritative; personal plans live in `.tiga/Todo.md`. Promote anything out of it only when the user explicitly asks.

3. **Using the old directory layout.** The layout is `01-prompts/`, `02-agent-skills/`, `03-custom-skills/`, `04-scripts/`. Do not reintroduce removed directories such as `00-skill-index/`, `03-workflows/`, or `05-custom-skills/`.
