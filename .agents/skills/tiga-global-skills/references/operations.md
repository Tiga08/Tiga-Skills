# Operation Details

Per-operation rules for Phase 2 of tiga-global-skills. Dispatch to the section matching the resolved operation.

## setup

Setup wires two user-level locations differently:

- `~/.claude/skills` — stays a real directory, because Claude Code writes its own content there (`synced/` for skills synced from claude.ai) and only discovers skills one level deep. Setup links each `03-skills/<name>` as `~/.claude/skills/<name>` (absolute target), fixes dangling same-name links, and prunes links that point into `03-skills/` at entries that no longer exist. A same-name real directory or a link to another valid target is reported as a conflict and left untouched. If `~/.claude/skills` itself is a symlink (such as the legacy whole-directory link to `03-skills/`), setup skips it with a warning.
- `~/.codex/skills/tiga-skills` — a single symlink to `<REPO_ROOT>/03-skills` (Codex scans recursively). If it already exists and points elsewhere, setup skips it with a warning.

Setup never prompts or overwrites, so run `./02-scripts/manage-skills.sh setup` directly. Report any `冲突` / `跳过` warnings; the user decides whether to remove the conflicting path and rerun setup.

## add

Pre-check that the source path exists and contains `SKILL.md`. If `03-skills/<name>` already exists, the script exits with an error — in that case ask via `AskUserQuestion` with three options: `remove` the old entry first and re-add, register under a different name with `--name`, or cancel.

Registering an external skill requires user confirmation per AGENTS.md — covered by the confirmation policy in `SKILL.md`. Before confirmation, prepare and display the Chinese description that would be written to `descriptions-zh.conf`, but do not write it yet.

## remove

Before confirming, show the entry as `name → target (category)`. Note that the script only removes symlinks (external skills); for real directories (custom skills) it refuses and asks the user to handle manually. The script also removes the matching `descriptions-zh.conf` metadata, but never touches the link target.

## list / check / update-readme

Execute directly. Before `update-readme`, compare the affected skill's current core behavior with its config entry and refresh stale descriptions. If `check` exits non-zero, summarize the failures and suggest fixes by category: for broken links, `remove` the entry or repair the upstream path and re-`add`; for frontmatter violations, edit the source `SKILL.md` (under `03-skills/` or `.agents/skills/`).

## Notes

- `add` converts paths under `$HOME` to user-portable relative symlinks (e.g., `../../superpowers/skills/<name>` for a source inside AG-Tools; README grouping resolves the link, so the shorter form still groups under `superpowers`). This assumes the layout `~/Projects/AG-Tools/tiga-skills` (this repo) and `~/Projects/AG-Tools`; paths outside `$HOME` stay absolute with a portability warning.
- For entries sourced from AG-Tools, `add` / `remove` also maintain the downstream-reference list `~/Projects/AG-Tools/SKILLS-REFS.md` automatically, skipping with a warning when `SKILLS-REFS.md` is missing. `remove` deletes the row by the consumer column, so it works even when the link target no longer exists.
- `add` / `remove` resync `~/.claude/skills` links automatically (skipped with a warning while the legacy whole-directory symlink is still in place). After creating a custom skill directory under `03-skills/` by hand, run `setup` to link it.
- `check` verifies every entry under `03-skills/` — symlinks must resolve and have `SKILL.md`; real directories must have `SKILL.md` — plus the project-level links `.claude/skills` / `.codex/skills` → `.agents/skills`, the root `SKILLS-REFS.md` symlink (must resolve to the AG-Tools downstream-reference file), and the user-level links: `~/.claude/skills` must be a real directory with `<name>` → `03-skills/<name>` for every entry and no dangling links into `03-skills/`, and `~/.codex/skills/tiga-skills` must resolve to `03-skills/`. For in-repo sources (custom skills and `.agents/skills/` project-level skills) it also validates frontmatter compliance (name format and consistency with the registered name, description non-empty and ≤1024 characters, no unknown frontmatter keys); external sources skip frontmatter validation. Any failure makes it exit non-zero.
- `update-readme` generates grouped three-column tables (`名称` / `参数` / `描述`) from `SKILL.md` `argument-hint` values and `descriptions-zh.conf`, including project-level skills from `.agents/skills/`.
- If listing available external skills from AG-Tools, scan `~/Projects/AG-Tools/superpowers/skills/`.
