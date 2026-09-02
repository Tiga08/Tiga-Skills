---
name: tiga-local-skills
description: Init, add, update, remove, and list project-level skills in the current project's .agents/skills/, shared with Claude Code and Codex via .claude/skills and .codex/skills symlinks, while maintaining AG-Tools downstream references when applicable. Use when setting up or managing skills for one project only; for the Tiga-Skills global skill directory (03-skills/), use tiga-global-skills.
argument-hint: "init|add|update|remove|list [args]"
arguments: [mode]
disable-model-invocation: true
---

Manage the `.agents/skills/` directory in the current project. Skills placed here are exposed to Claude Code and Codex via `.claude/skills` and `.codex/skills` symlinks.

**Arguments:** Parse the invocation text as `init|add|update|remove|list [args]`. One positional operation is required. Claude Code also exposes the raw invocation as `$ARGUMENTS` and the declared first argument as `$mode`; do not treat either placeholder as input when the host does not expand it.

本次调用：`$ARGUMENTS` — 操作 `$mode`

- Positional operation (required, one of):
  - `init` — create `.agents/skills/`, set up `.claude/skills` and `.codex/skills` symlinks, migrate existing skills if needed.
  - `add <path> [--name <name>] [--copy]` — symlink a skill directory into `.agents/skills/<name>` (use `--copy` to copy it and keep a machine-local source record).
  - `update [<name>] [<path>]` — safely re-copy a copied skill from its recorded source; without `<name>`, batch-update all copied entries.
  - `remove <name>` — remove `.agents/skills/<name>` from discovery while keeping a recoverable local copy.
  - `list` — scan `.agents/skills/` and display each skill's name, type, and description.

**No-argument behavior:** If the operation is empty or not one of the five above, do not guess. Use the host's user-confirmation mechanism to let the user choose among `init` / `add` / `update` / `remove` / `list`, then collect any missing required arguments (source path for `add`, skill name for `remove`). If no structured confirmation mechanism is available, ask a concise plain-text question and stop until the user answers.

## Workflow

### Phase 1: Resolve Project & Operation

Determine which project you are operating on:

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)
```

Display to the user: **"Operating on project: \`<PROJECT_ROOT>\`"**

Run every subsequent shell command with its working directory set to `PROJECT_ROOT`. Merely computing the variable is insufficient: relative `.agents/`, `.claude/`, `.codex/`, and `.tiga/` paths must never resolve from the invocation subdirectory.

Then parse the operation and its arguments. If the operation is missing or invalid, follow **No-argument behavior** above.

Before constructing an entry path for `add`, `update <name>`, or `remove`, validate the intended name:

- Require 1–64 lowercase ASCII letters, digits, or single hyphens, matching `^[a-z0-9]+(-[a-z0-9]+)*$`.
- Reject `/`, `\`, `.`, `..`, empty segments, leading or trailing hyphens, and consecutive hyphens.
- Construct the entry only as `.agents/skills/<validated-name>` and keep every shell argument quoted. Never interpolate an unvalidated name into `rm`, `mv`, `cp`, or `ln`.

For `add`, parse the source `SKILL.md` frontmatter and use its `name` as the default entry name. If `--name` is supplied, require it to equal that frontmatter name; reject an alias instead of creating a directory/name mismatch that violates the Agent Skills format.

### Phase 2: Execute Operation

Dispatch to the matching section under **Operation Details**.

**Confirmation policy** — only destructive or overwriting actions require confirmation through the host mechanism, with a concise plain-text question as the fallback:

- `remove` — always confirm, after showing the entry type.
- `init` — confirm before migrating (Scenario B) or replacing (Scenario C).
- `add` — confirm only on a name conflict.
- `update` — overwrites the copied entry: confirm once per single update; in batch mode, show the update plan list and confirm once for the whole batch.

`list` and a conflict-free `add` execute directly without confirmation unless **Safety Invariants** requires approval to keep `.tiga/` local.

### Safety Invariants

Apply these rules to every operation:

1. Treat an entry as existing when either `[ -e "$entry" ]` or `[ -L "$entry" ]` succeeds, so a dangling symlink is still a conflict.
2. Resolve every source path before mutation. Require a directory containing `SKILL.md`, reject a source equal to or nested inside the destination entry, and verify its frontmatter `name` equals the validated entry name.
3. Never delete an existing entry before its replacement is ready. Build a candidate as a hidden sibling under `.agents/skills/`, validate it, move the old entry to `.tiga/local-skills/backups/`, then move the candidate into place. If the final move fails, restore the backup.
4. Keep machine-local source records and recoverable removals under `.tiga/local-skills/`, never inside a copied skill. In a Git repository, verify `.tiga/` is ignored before writing there. If it is not ignored, ask before adding `/.tiga/` to `.git/info/exclude`; stop the operation if the user declines. Never write an absolute local source path into a tracked file.
5. Preserve backups and report their paths. Remove them only on a later explicit user request.

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
3. Validate each directory name and its `SKILL.md` frontmatter name, then for each valid skill:
   - If `.agents/skills/<name>/` does not exist → move it there.
   - If `.agents/skills/<name>/` already exists → ask the user which version to keep, then move the other version to the backup directory.
4. Remove the now-empty original directory with `rmdir`; do not recursively delete it.
5. Create the symlink.

**Scenario C handling:** show the current symlink target, then ask whether to replace it with the standard symlink to `../.agents/skills` or keep it as-is. On replacement, move the old symlink to the backup directory before creating the standard link.

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
# Build a hidden candidate first; install it only after validation.
# Default: symlink (tracks upstream updates; no source record needed)
ln -s <link-target> <candidate-path>

# --copy: copy (project is self-contained); write the source record after installation
cp -R <source-path>/. <candidate-path>/
```

**Parameters:**
- `<path>` — source skill directory (must contain `SKILL.md`)
- `--name <name>` — explicit skill name (defaults to the source `SKILL.md` frontmatter name and must equal it)
- `--copy` — copy instead of symlink

**Link target convention** (matches Tiga-Skills `manage-skills.sh`):
- Source under `$HOME` → compute `<link-target>` as a path relative to `.agents/skills/` (e.g. `../../../../AG-Tools/baoyu-skills/skills/<name>` for a project at `~/Projects/<org>/<repo>`), so the link stays portable across machines sharing the same `~/Projects` layout.
- Source outside `$HOME` → use the absolute path and tell the user the link is machine-specific.

**Validation:**
- Apply the source, name, containment, and dangling-symlink checks from **Safety Invariants**.
- On a target conflict, ask whether to safely replace the existing entry or cancel. Never offer a different link or directory name as an alias for the source frontmatter `name`.
- Build and validate the link or copy as a hidden sibling first. For `--copy`, omit any legacy `.skill-source` from the candidate, install it through the safe-replacement flow, then atomically write the resolved absolute source path to `.tiga/local-skills/sources/<name>.source`.

**Downstream-reference maintenance** (applies to both the default link and `--copy`):

After a successful import, resolve the source to an absolute path. If it is under `~/Projects/AG-Tools/`, update the reference table in `~/Projects/AG-Tools/SKILLS-REFS.md`:

1. Build the row — 上游技能 = source path relative to the AG-Tools root; 引用方 = entry path relative to `~/Projects`, including the entry name; 方式 = `link` or `copy`. Example: `| baoyu-skills/skills/baoyu-format-markdown | Acme/my-app/.agents/skills/baoyu-format-markdown | link |`.
2. Insert the row at its sorted position in the table body (sorted by the 上游技能 column); if the identical row already exists, skip.
3. If `SKILLS-REFS.md` is missing, create it from this template first, then insert the row:

   ```markdown
   # 下游引用

   > 记录 AG-Tools 技能被下游仓库引用的情况，回答"哪些 skill 被哪些仓库引用"。
   > **维护契约**：本清单由下游消费方维护——各项目 `.agents/skills/` 条目的增删由 tiga-local-skills 负责，Tiga-Skills `03-skills/` 注册表的增删由其 `manage-skills.sh` 负责。
   > 行格式：上游技能为相对 AG-Tools 根目录的路径；引用方为相对 `~/Projects` 的条目路径（含条目名）；方式为 `link` 或 `copy`。表体按"上游技能"列排序。

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
   - Otherwise read `.tiga/local-skills/sources/<name>.source`.
   - For compatibility, if the local record is missing, read the legacy `.agents/skills/<name>/.skill-source`.
   - If neither record is usable, ask the user for the source path.
4. Apply every source and name check from **Safety Invariants**, including rejecting a source equal to or nested inside the entry.
5. Show a path-only comparison of the current entry and source, then confirm.
6. Create and validate a complete candidate copy before touching the current entry. Exclude legacy `.skill-source`, move the current entry to a timestamped backup, install the candidate, and restore the backup if installation fails.
7. Atomically write the source record under `.tiga/local-skills/sources/`. If a legacy record was used, migrate it only after the replacement succeeds.

Do not display file contents during the comparison; a skill may contain private local material. Report the retained backup path after success.

**Batch update — `update` with no name:**

1. Scan `.agents/skills/*/` and classify each entry:
   - Symlink → skip, note "symlink, tracks upstream automatically".
   - Copied entry with a valid local source record, or a valid legacy `.skill-source` → to update.
   - Copied entry with no usable record, or whose recorded source is missing / lacks `SKILL.md` → skip, note the reason (batch mode never prompts per entry).
2. Validate every planned name and source before confirmation. Show the plan list (name → source / skip reason) and confirm once.
3. Execute the single-update steps for each entry to update; report per-entry results (updated / skipped + reason).

### remove

Remove `.agents/skills/<name>` from active discovery while retaining a recoverable copy.

Before removal, validate the name, show the exact entry path and type — regular directory, or `symlink → <target>` — and confirm.

Move the exact entry, without a trailing slash, to a unique timestamped path under `.tiga/local-skills/removed/`. This removes a symlink itself, never its target, and keeps a regular directory recoverable. If a local or legacy source record exists, retain it alongside the removed entry.

**Validation:**
- Target must satisfy `[ -e "$entry" ] || [ -L "$entry" ]`; error otherwise.
- Confirm the resolved entry path is the validated direct child of `.agents/skills/` before moving it.

**Downstream-reference maintenance:**

Before removal, check whether the entry references AG-Tools — a symlink whose resolved target is under `~/Projects/AG-Tools/`, or a copied entry whose local or legacy source record points there. If so, after removal delete the matching row (match on the 引用方 column) from `~/Projects/AG-Tools/SKILLS-REFS.md`; if the file or row does not exist, note it and continue.

### list

Scan `.agents/skills/` and extract description from each `SKILL.md` frontmatter.

**Empty states:**
- `.agents/skills/` does not exist → report that the project is not initialized and suggest running `init`.
- `.agents/skills/` exists but is empty → report that no skills are installed.

```bash
for entry in .agents/skills/*; do
  [ -e "$entry" ] || [ -L "$entry" ] || continue
  # Read SKILL.md frontmatter for description; detect entry type via [ -L ]
done
```

Output as a table. Type is `copy` for a regular directory, or `symlink → <target>` for a symlinked entry:

| Name | Type | Description |
| ---- | ---- | ----------- |

## Notes

- `add` symlinks by default to track upstream updates at low maintenance cost. Use `--copy` when the project must be self-contained.
- `.tiga/local-skills/sources/<name>.source` records a copied entry's upstream source path (absolute, one line) for `update`. It is machine-local and must stay ignored. Legacy `.skill-source` files remain readable and migrate after a successful update.
- Default symlinks use a relative target for sources under `$HOME` (portable across machines sharing the same `~/Projects` layout) and an absolute target otherwise (machine-specific); use `--copy` when the layouts differ and portability matters.
- `.claude/skills` and `.codex/skills` are symlinks — edit skills in `.agents/skills/`, not through the symlinks.
- This skill runs shell commands directly; it does not depend on any external scripts.
