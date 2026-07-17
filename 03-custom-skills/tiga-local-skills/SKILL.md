---
name: tiga-local-skills
description: Init, add, update, remove, and list project-level skills in the current project's .agents/skills/, shared with Claude Code and Codex via .claude/skills and .codex/skills symlinks. Use when setting up a project's skill directory or importing/updating/removing skills for that project only; for the Tiga-Skills global registry (02-agent-skills/), use tiga-global-skills.
argument-hint: "init|add|update|remove|list [args]"
---

Manage the `.agents/skills/` directory in the current project. Skills placed here are exposed to Claude Code and Codex via `.claude/skills` and `.codex/skills` symlinks.

**Arguments:** One positional operation argument is required.

- Positional operation (required, one of):
  - `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed.
  - `add <path> [--name <name>] [--copy]` — symlink a skill directory into `.agents/skills/<name>` (use `--copy` to copy instead and record its source path in `.skill-source`).
  - `update [<name>] [<path>]` — re-copy a copied skill from its recorded source (`.skill-source`); without `<name>`, batch-update all copied entries.
  - `remove <name>` — delete `.agents/skills/<name>` (directory or symlink).
  - `list` — scan `.agents/skills/` and display each skill's name, type, and description.

**No-argument behavior:** If the operation argument is missing or not one of the five above, do not guess. Use `AskUserQuestion` to let the user choose among `init` / `add` / `update` / `remove` / `list`, then collect any missing required arguments (source path for `add`, skill name for `remove`).

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

Summarize the outcome for each path or entry touched (done / skipped / created / migrated / replaced / updated / removed). For `add` / `remove` involving an AG-Tools source, also report whether the downstream-reference list in `~/Projects/AG-Tools/SKILLS-REFS.md` was updated or skipped (and why). After `init`, remind the user to add `.agents/` to version control (`git add .agents/`).

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

### add

Import a skill directory into `.agents/skills/<name>/`.

```bash
# Default: symlink (tracks upstream updates; no .skill-source needed)
ln -s <link-target> .agents/skills/<name>

# --copy: copy (project is self-contained), then record the source path for later update
cp -R <source-path> .agents/skills/<name>
printf '%s\n' "$(cd <source-path> && pwd)" > .agents/skills/<name>/.skill-source
```

**Parameters:**
- `<path>` — source skill directory (must contain `SKILL.md`)
- `--name <name>` — custom skill name (defaults to source directory name)
- `--copy` — copy instead of symlink

**Link target convention** (matches Tiga-Skills `manage-skills.sh`):
- Source under `$HOME` → compute `<link-target>` as a path relative to `.agents/skills/` (e.g. `../../../../AG-Tools/baoyu-skills/skills/<name>` for a project at `~/Projects/<org>/<repo>`), so the link stays portable across machines sharing the same `~/Projects` layout.
- Source outside `$HOME` → use the absolute path and tell the user the link is machine-specific.

**Validation:**
- Source directory must contain `SKILL.md`; error otherwise.
- Target `.agents/skills/<name>/` must not already exist. On conflict, ask via `AskUserQuestion` with three options: overwrite the existing entry, import under a different name, or cancel.

**Downstream-reference maintenance** (applies to both the default link and `--copy`):

After a successful import, resolve the source to an absolute path. If it is under `~/Projects/AG-Tools/`, update the reference table in `~/Projects/AG-Tools/SKILLS-REFS.md`:

1. Build the row — 上游技能 = source path relative to the AG-Tools root; 引用方 = entry path relative to `~/Projects` including the entry name (covers `--name` renames); 方式 = `link` or `copy`. Example: `| baoyu-skills/skills/baoyu-format-markdown | Tiga/Skills/02-agent-skills/baoyu-format-markdown | link |`.
2. Insert the row at its sorted position in the table body (sorted by the 上游技能 column); if the identical row already exists, skip.
3. If `SKILLS-REFS.md` is missing, create it from this template first, then insert the row:

   ```markdown
   # 下游引用

   > 记录 AG-Tools 技能被下游仓库引用的情况，回答"哪些 skill 被哪些仓库引用"。
   > **维护契约**：本清单由下游消费方维护——各项目 `.agents/skills/` 条目的增删由 tiga-local-skills 负责，Tiga-Skills `02-agent-skills/` 注册表的增删由其 `manage-skills.sh` 负责。
   > 行格式：上游技能为相对 AG-Tools 根目录的路径；引用方为相对 `~/Projects` 的条目路径（含条目名，覆盖 `--name` 重命名）；方式为 `link` 或 `copy`。表体按"上游技能"列排序。

   | 上游技能 | 引用方 | 方式 |
   | -------- | ------ | ---- |
   ```

4. If `~/Projects/AG-Tools/` does not exist (another machine), skip this step and note it in the Phase 3 report.

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

**Downstream-reference maintenance:**

Before deleting, check whether the entry references AG-Tools — a symlink whose resolved target is under `~/Projects/AG-Tools/`, or a copied entry whose `.skill-source` points there. If so, after deletion remove the matching row (match on the 引用方 column) from the reference table in `~/Projects/AG-Tools/SKILLS-REFS.md`; if the file or row does not exist, note it and continue.

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

- `add` symlinks by default to track upstream updates at low maintenance cost. Use `--copy` when the project must be self-contained.
- `.skill-source` inside a copied entry records its upstream source path (absolute, one line) for `update`. The path is machine-specific; if it becomes invalid (e.g., after moving to another machine), `update` falls back to asking for the source path and rewrites the record.
- Default symlinks use a relative target for sources under `$HOME` (portable across machines sharing the same `~/Projects` layout) and an absolute target otherwise (machine-specific); use `--copy` when the layouts differ and portability matters.
- `.claude/skills` and `.codex/skills` are symlinks — edit skills in `.agents/skills/`, not through the symlinks.
- This skill runs shell commands directly; it does not depend on any external scripts.
