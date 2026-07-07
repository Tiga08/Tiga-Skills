---
name: manage-local-skills
description: Init, add, remove, and list project-level skills in the current project's .agents/skills/, shared with Claude Code and Codex via .claude/skills and .codex/skills symlinks. Use when setting up a project's skill directory or importing/removing skills for that project only; for the Tiga-Skills global registry (02-agent-skills/), use manage-global-skills.
description_zh: 初始化、导入、移除和列出当前项目 .agents/skills/ 中的项目级技能，通过 .claude/skills 与 .codex/skills 符号链接供 Claude Code 和 Codex 共享。适用于搭建项目技能目录或只为当前项目导入 / 移除技能；管理 Tiga-Skills 全局注册表（02-agent-skills/）请改用 manage-global-skills。
---

Manage the `.agents/skills/` directory in the current project. Skills placed here are exposed to Claude Code and Codex via `.claude/skills` and `.codex/skills` symlinks.

**Arguments:** One positional operation argument is required.

- Positional operation (required, one of):
  - `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed.
  - `add <path> [--name <name>] [--link]` — copy a skill directory into `.agents/skills/<name>/` (use `--link` for a symlink instead).
  - `remove <name>` — delete `.agents/skills/<name>` (directory or symlink).
  - `list` — scan `.agents/skills/` and display each skill's name, type, and description.

**No-argument behavior:** If the operation argument is missing or not one of the four above, do not guess. Use `AskUserQuestion` to let the user choose among `init` / `add` / `remove` / `list`, then collect any missing required arguments (source path for `add`, skill name for `remove`).

## Available Operations

Parse the user's intent and map it to one of the following operations:

| Intent | Operation |
| ------ | --------- |
| Initialize project skill directory | `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed |
| Import a skill | `add <path> [--name <name>] [--link]` — copy a skill directory into `.agents/skills/<name>/` (use `--link` for symlink instead) |
| Remove a skill | `remove <name>` — delete `.agents/skills/<name>` |
| List installed skills | `list` — scan `.agents/skills/` and display names, types, and descriptions |

## Workflow

### Phase 1: Resolve Project & Operation

Determine which project you are operating on:

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

Display to the user: **"Operating on project: \`<PROJECT_ROOT>\`"**

All paths in subsequent operations are relative to this project root. This ensures correct targeting when the skill is invoked from different projects via global symlinks.

Then parse the operation and its arguments. If the operation is missing or invalid, follow **No-argument behavior** above.

### Phase 2: Execute Operation

Dispatch to the matching section under **Operation Details**.

**Confirmation policy** — only destructive or overwriting actions require an `AskUserQuestion` confirmation first:

- `remove` — always confirm, after showing the entry type.
- `init` — confirm before migrating (Scenario B) or replacing (Scenario C).
- `add` — confirm only on a name conflict.

`list` and a conflict-free `add` execute directly without confirmation.

### Phase 3: Report

Summarize the outcome for each path or entry touched (done / skipped / migrated / replaced / removed). After `init`, remind the user to add `.agents/` to version control (`git add .agents/`).

## Operation Details

### init

Create `.agents/skills/` and establish agent configuration symlinks, migrating existing skills if necessary.

**Step 1 — Create shared directory:**

```bash
mkdir -p .agents/skills
```

**Step 2 — Check `.claude/skills` and `.codex/skills` separately:**

Each path falls into one of four scenarios:

| Scenario | Condition | Action |
| -------- | --------- | ------ |
| A | Correct symlink → `../.agents/skills` | Skip; report already configured |
| B | Real directory with existing skills | Migrate contents to `.agents/skills/`, remove directory, create symlink |
| C | Symlink → other target | Ask user whether to replace |
| D | Does not exist | Create symlink directly |

**Scenario B migration flow:**

1. List all skill subdirectories inside the real directory.
2. Display the list to the user and ask for confirmation before migrating.
3. For each skill subdirectory:
   - If `.agents/skills/<name>/` does not exist → move it there.
   - If `.agents/skills/<name>/` already exists → ask the user which version to keep.
4. Remove the now-empty original directory.
5. Create the symlink.

**Scenario C handling:** show the current symlink target, then ask via `AskUserQuestion` with two options: replace it with the standard symlink to `../.agents/skills`, or keep it as-is and skip this path.

```bash
# Detection logic for each path (e.g., .claude/skills)
if [ -L "$path" ]; then
  target=$(readlink "$path")
  if [ "$target" = "../.agents/skills" ]; then
    # Scenario A: correct symlink
  else
    # Scenario C: symlink to other target
  fi
elif [ -d "$path" ]; then
  # Scenario B: real directory — migrate
else
  # Scenario D: does not exist
  mkdir -p "$(dirname "$path")"
  ln -s ../.agents/skills "$path"
fi
```

**Important:**
- Check `.claude/skills` and `.codex/skills` independently — they may be in different states.
- Always confirm with the user before migrating or replacing anything.

**Step 3 — Report results:**

Summarize what was done for each path (skipped / created / migrated / replaced). Remind the user to add `.agents/` to version control (`git add .agents/`).

### add

Import a skill directory into `.agents/skills/<name>/`.

```bash
# Default: copy (project is self-contained)
cp -R <source-path> .agents/skills/<name>

# --link: symlink (tracks upstream updates)
ln -s <absolute-source-path> .agents/skills/<name>
```

**Parameters:**
- `<path>` — source skill directory (must contain `SKILL.md`)
- `--name <name>` — custom skill name (defaults to source directory name)
- `--link` — use symlink instead of copy

**Validation:**
- Source directory must contain `SKILL.md`; error otherwise.
- Target `.agents/skills/<name>/` must not already exist. On conflict, ask via `AskUserQuestion` with three options: overwrite the existing entry, import under a different name, or cancel.

### remove

Delete `.agents/skills/<name>` (directory or symlink).

Before deleting, show the entry type — regular directory, or `symlink → <target>` — and confirm via `AskUserQuestion`.

```bash
# Symlink: no trailing slash — removes the link itself, never the link target
if [ -L .agents/skills/<name> ]; then
  rm .agents/skills/<name>
else
  rm -rf .agents/skills/<name>
fi
```

**Validation:**
- Target must exist under `.agents/skills/`; error otherwise.

### list

Scan `.agents/skills/` and extract description from each `SKILL.md` frontmatter.

**Empty states:**
- `.agents/skills/` does not exist → report that the project is not initialized and suggest running `init`.
- `.agents/skills/` exists but is empty → report that no skills are installed.

```bash
for dir in .agents/skills/*/; do
  # Read SKILL.md frontmatter for description; detect entry type via [ -L ]
done
```

Output as a table. Type is `copy` for a regular directory, or `symlink → <target>` for a symlinked entry:

| Name | Type | Description |
| ---- | ---- | ----------- |

## Notes

- After `init`, remind the user to version-control `.agents/` (`git add .agents/`).
- `add` copies by default for self-containment. Use `--link` to track upstream updates.
- `--link` creates an absolute-path symlink, which is machine-specific and does not survive moving the project to another machine; use the default copy when portability matters.
- `.claude/skills` and `.codex/skills` are symlinks — edit skills in `.agents/skills/`, not through the symlinks.
- This skill runs shell commands directly; it does not depend on any external scripts.
