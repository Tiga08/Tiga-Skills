---
name: tiga-local-skills
description: Init, add, update, remove, and list project-level skills in the current project's .agents/skills/, shared with Claude Code and Codex via .claude/skills and .codex/skills symlinks. Use when setting up a project's skill directory or importing/updating/removing skills for that project only; for the Tiga-Skills global registry (02-agent-skills/), use manage-global-skills.
---

Manage the `.agents/skills/` directory in the current project. Skills placed here are exposed to Claude Code and Codex via `.claude/skills` and `.codex/skills` symlinks.

**Arguments:** One positional operation argument is required.

- Positional operation (required, one of):
  - `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed.
  - `add <path> [--name <name>] [--link]` — copy a skill directory into `.agents/skills/<name>/` and record its source path in `.skill-source` (use `--link` for a symlink instead).
  - `update [<name>] [<path>]` — re-copy a copied skill from its recorded source (`.skill-source`); without `<name>`, batch-update all copied entries.
  - `remove <name>` — delete `.agents/skills/<name>` (directory or symlink).
  - `list` — scan `.agents/skills/` and display each skill's name, type, and description.

**No-argument behavior:** If the operation argument is missing or not one of the five above, do not guess. Use `AskUserQuestion` to let the user choose among `init` / `add` / `update` / `remove` / `list`, then collect any missing required arguments (source path for `add`, skill name for `remove`).

## Available Operations

Parse the user's intent and map it to one of the following operations:

| Intent | Operation |
| ------ | --------- |
| Initialize project skill directory | `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed |
| Import a skill | `add <path> [--name <name>] [--link]` — copy a skill directory into `.agents/skills/<name>/` and record its source in `.skill-source` (use `--link` for symlink instead) |
| Update imported skills | `update [<name>] [<path>]` — re-copy from the recorded source; without `<name>`, batch-update all copied entries |
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
- `update` — overwrites the copied entry: confirm once per single update; in batch mode, show the update plan list and confirm once for the whole batch.

`list` and a conflict-free `add` execute directly without confirmation.

### Phase 3: Report

Summarize the outcome for each path or entry touched (done / skipped / migrated / replaced / updated / removed). After `init`, remind the user to add `.agents/` to version control (`git add .agents/`).

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
# Default: copy (project is self-contained), then record the source path for later update
cp -R <source-path> .agents/skills/<name>
printf '%s\n' "$(cd <source-path> && pwd)" > .agents/skills/<name>/.skill-source

# --link: symlink (tracks upstream updates; no .skill-source needed)
ln -s <absolute-source-path> .agents/skills/<name>
```

**Parameters:**
- `<path>` — source skill directory (must contain `SKILL.md`)
- `--name <name>` — custom skill name (defaults to source directory name)
- `--link` — use symlink instead of copy

**Validation:**
- Source directory must contain `SKILL.md`; error otherwise.
- Target `.agents/skills/<name>/` must not already exist. On conflict, ask via `AskUserQuestion` with three options: overwrite the existing entry, import under a different name, or cancel.

### update

Re-copy copied skills from their recorded upstream source. Symlinked entries track upstream automatically and cannot (and need not) be updated.

**Single update — `update <name> [<path>]`:**

1. Entry must exist under `.agents/skills/`; error otherwise.
2. If the entry is a symlink → tell the user it tracks upstream automatically and needs no update, then stop.
3. Resolve the source path:
   - Explicit `<path>` argument takes precedence.
   - Otherwise read `.agents/skills/<name>/.skill-source`.
   - If the record is missing (e.g., copied before this feature existed) or the recorded path no longer exists → ask the user for the source path via `AskUserQuestion`.
4. Validate the source: must exist and contain `SKILL.md`.
5. Confirm, then execute:

```bash
src=<resolved-source-path>
rm -rf .agents/skills/<name>
cp -R "$src" .agents/skills/<name>
printf '%s\n' "$src" > .agents/skills/<name>/.skill-source
```

**Batch update — `update` with no name:**

1. Scan `.agents/skills/*/` and classify each entry:
   - Symlink → skip, note "symlink, tracks upstream automatically".
   - Copied entry with a valid `.skill-source` → to update.
   - Copied entry with no record, or whose recorded source is missing / lacks `SKILL.md` → skip, note the reason (batch mode never prompts per entry).
2. Show the plan list (name → source / skip reason) and confirm once via `AskUserQuestion`.
3. Execute the single-update steps for each entry to update; report per-entry results (updated / skipped + reason).

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
- `.skill-source` inside a copied entry records its upstream source path (absolute, one line) for `update`. The path is machine-specific; if it becomes invalid (e.g., after moving to another machine), `update` falls back to asking for the source path and rewrites the record.
- `--link` creates an absolute-path symlink, which is machine-specific and does not survive moving the project to another machine; use the default copy when portability matters.
- `.claude/skills` and `.codex/skills` are symlinks — edit skills in `.agents/skills/`, not through the symlinks.
- This skill runs shell commands directly; it does not depend on any external scripts.
