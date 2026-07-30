@AGENTS.md

## Constraints

- Keep scripts executable UTF-8 Bash in the existing direct-command style.

## Common Gotchas

1. **Assuming a `02-agent-skills/` entry lives in this repository.** Some links resolve to `03-custom-skills/`, others to external AG-Tools forks, and the entry name does not say which. Resolve a link to its target before editing anything behind it.

2. **Treating `.tiga/` as project content.** It is git-ignored and never authoritative; personal plans live in `.tiga/Todo.md`. Promote anything out of it only when the user explicitly asks.

3. **Using the old directory layout.** The layout is `01-prompts/`, `02-agent-skills/`, `03-custom-skills/`, `04-scripts/`. Do not reintroduce removed directories such as `00-skill-index/`, `03-workflows/`, or `05-custom-skills/`.
