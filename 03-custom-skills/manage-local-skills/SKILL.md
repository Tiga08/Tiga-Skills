---
name: manage-local-skills
description: Manage project-level agent skills — init, add, remove, and list skills in .agents/skills/ for the current project
description_zh: 管理项目级 agent 技能 — 在当前项目的 .agents/skills/ 中初始化、导入、移除和列出技能
---

Manage the `.agents/skills/` directory in the current project. Skills placed here are exposed to Claude Code and Codex via `.claude/skills` and `.codex/skills` symlinks.

## Available Operations

Parse the user's intent and map it to one of the following operations:

| Intent | Operation |
| ------ | --------- |
| Initialize project skill directory | `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed |
| Import a skill | `add <path> [--name <name>]` — copy a skill directory into `.agents/skills/<name>/` (use `--link` for symlink instead) |
| Remove a skill | `remove <name>` — delete `.agents/skills/<name>/` |
| List installed skills | `list` — scan `.agents/skills/` and display names and descriptions |

## Project Context

Before performing any operation, determine which project you are operating on:

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
```

Display to the user: **"Operating on project: \`<PROJECT_ROOT>\`"**

All paths in subsequent operations are relative to this project root. This ensures correct targeting when the skill is invoked from different projects via global symlinks.

## Workflow

1. **Identify project** — resolve the project root and display it to the user.
2. **Clarify intent** — determine which operation the user wants and what arguments are needed.
3. **Confirm before acting** — show the user what will happen and ask for confirmation via `AskUserQuestion`.
4. **Execute** — run the corresponding shell commands.
5. **Report** — show the result and summarize changes.

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
- Target `.agents/skills/<name>/` must not already exist; ask user on conflict.

### remove

Delete `.agents/skills/<name>/` (directory or symlink).

```bash
rm -rf .agents/skills/<name>
```

**Validation:**
- Target must exist under `.agents/skills/`; error otherwise.

### list

Scan `.agents/skills/` and extract description from each `SKILL.md` frontmatter.

```bash
for dir in .agents/skills/*/; do
  # Read SKILL.md frontmatter for description
done
```

Output as a table:

| Name | Description |
| ---- | ----------- |

## Notes

- After `init`, remind the user to version-control `.agents/` (`git add .agents/`).
- `add` copies by default for self-containment. Use `--link` to track upstream updates.
- `.claude/skills` and `.codex/skills` are symlinks — edit skills in `.agents/skills/`, not through the symlinks.
- This skill runs shell commands directly; it does not depend on any external scripts.
