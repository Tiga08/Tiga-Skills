# Operation Details

Per-operation rules for Phase 2 of tiga-global-skills. Dispatch to the section matching the resolved operation.

## setup

The script prompts interactively with `read` when a link conflicts, which fails (EOF, non-zero exit under `set -euo pipefail`) when run through the non-interactive Bash tool. So pre-check both user-level links with read-only commands first:

- `~/.claude/skills` — should be a symlink to `<REPO_ROOT>/02-agent-skills`.
- `~/.codex/skills/tiga-skills` — should be a symlink to the same target.

Each path is in one of four states: absent / correct symlink / symlink to another target / real directory (or other file).

- All correct or absent → run `./04-scripts/manage-skills.sh setup` directly.
- Any conflict → ask per conflicting path via `AskUserQuestion` (update the link / keep and skip), then run setup piping the answers in prompt order (claude first, then codex; only conflicting paths produce a prompt), e.g. `printf 'y\n' | ./04-scripts/manage-skills.sh setup`.

## add

Pre-check that the source path exists and contains `SKILL.md`. If `02-agent-skills/<name>` already exists, the script exits with an error — in that case ask via `AskUserQuestion` with three options: `remove` the old entry first and re-add, register under a different name with `--name`, or cancel.

Registering an external skill requires user confirmation per AGENTS.md — covered by the confirmation policy in `SKILL.md`. Before confirmation, prepare and display the Chinese description that would be written to `descriptions-zh.conf`, but do not write it yet.

## add-custom

Pre-check that `03-custom-skills/<name>` exists. If not, scan `03-custom-skills/` for directories containing `SKILL.md` and let the user pick from the candidates. On a name conflict in `02-agent-skills/`, handle like `add` but without the rename option: `remove` then re-add, or cancel.

## remove

Before confirming, show the entry as `name → target (category)`. Note that the script deletes the symlink and its matching `descriptions-zh.conf` metadata, but never touches the link target.

## list / check / update-readme

Execute directly. Before `update-readme`, compare the affected skill's current core behavior with its config entry and refresh stale descriptions. If `check` exits non-zero, summarize the failures and suggest fixes by category: for broken links, `remove` the entry or repair the upstream path and re-`add`; for frontmatter violations, edit the source `SKILL.md` (under `03-custom-skills/` or `.agents/skills/`).

## Notes

- `add-custom` creates symlinks directly under `02-agent-skills/` with relative paths (`../03-custom-skills/<name>`).
- `add` converts paths under `$HOME` to user-portable relative symlinks (e.g., `../../../AG-Tools/superpowers/skills/<name>`). This assumes the layout `~/Projects/Tiga/Skills` (this repo) and `~/Projects/AG-Tools`; paths outside `$HOME` stay absolute with a portability warning.
- For entries sourced from AG-Tools, `add` / `remove` also maintain the downstream-reference list `~/Projects/AG-Tools/SKILLS-REFS.md` automatically, skipping with a warning when AG-Tools is absent; `add` recreates a missing `SKILLS-REFS.md` from its template, while `remove` only warns.
- `check` verifies every symlink under `02-agent-skills/` (target resolvable, `SKILL.md` present) plus the project-level links `.claude/skills` / `.codex/skills` → `.agents/skills` and the root `SKILLS-REFS.md` symlink (must resolve to the AG-Tools downstream-reference file). For in-repo sources and `.agents/skills/` project-level skills it also validates frontmatter compliance (name format and consistency with the registered name, description non-empty and ≤1024 characters, no unknown frontmatter keys); external sources skip frontmatter validation. Any failure makes it exit non-zero.
- `update-readme` generates grouped three-column tables (`名称` / `参数` / `描述`) from `SKILL.md` `argument-hint` values and `descriptions-zh.conf`, including project-level skills from `.agents/skills/`.
- If listing available external skills from AG-Tools, scan `~/Projects/AG-Tools/superpowers/skills/`.
