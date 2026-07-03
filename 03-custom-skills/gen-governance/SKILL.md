---
name: gen-governance
description: Analyze repository structure and generate AGENTS.md / CLAUDE.md governance files (root and subdirectories) grounded in actual repo evidence, merging still-valid rules when overwriting, then invoke md-to-zh to sync Chinese translations. Use when a repository has no governance files or needs them regenerated after major restructuring; to audit existing docs against reality, use check-docs instead.
description_zh: 分析仓库结构，基于仓库实际证据生成根目录及子目录的 AGENTS.md / CLAUDE.md 治理文件，覆盖时合并仍然有效的旧规则，随后调用 md-to-zh 同步中文翻译。适用于仓库尚无治理文件、或大规模重构后需要重新生成的场景；若要审计现有文档与仓库是否一致，请改用 check-docs。
---

Analyze the current repository and generate governance files (`AGENTS.md` and `CLAUDE.md`) so that AI agents can understand and operate correctly within the project. After writing, invoke the `md-to-zh` skill to keep Chinese translations in sync.

**Arguments:** Optional flags may appear in the argument list.

- `--dry-run`: Run Phase 1 only — print the analysis summary and generation plan (including conflict annotations), write nothing, then stop.
- `--force`: Overwrite all existing governance files without conflict prompts.
- `--no-translate`: Skip Phase 4 (translation sync).

**No-argument behavior:** Analyze the current project root directory and generate governance files for it.

## Workflow

### Phase 1: Repository Analysis & Generation Plan

Inspect the repository, decide exactly which files will be generated, and resolve all conflicts before any writing happens.

**1. Analyze the repository:**

- List the top two levels of the directory tree.
- Read the `README` and any existing configuration or governance files, including existing `AGENTS.md`, `CLAUDE.md`, or agent-related files. Keep the content of existing governance files — Phase 2 merges their still-valid rules into the new files.
- Identify the repository type: application, library, monorepo, content repository, or other.
- Identify the main functional layers of the project.
- Determine which top-level directories need their own `CLAUDE.md`.

Criterion for subdirectory `CLAUDE.md`:

> Generate a subdirectory `CLAUDE.md` only when that directory has ownership semantics, modification rules, or operational constraints that differ from the repository root.

**2. Build the generation plan:** List every target file in generation order — `AGENTS.md`, root `CLAUDE.md`, then each subdirectory `CLAUDE.md`. Mark each target that already exists as a conflict. The plan's file count is the initial total N.

**3. Resolve conflicts:**

- If `--force` is set: mark every conflicting target as "overwrite"; no prompts.
- If `--dry-run` is set: print the analysis summary and the generation plan with conflict annotations, then **stop here** — no files are written and no later phase runs.
- Otherwise, for each conflicting target, ask via `AskUserQuestion`:
  - Overwrite this file
  - Skip this file
  - Overwrite all remaining conflicts
  - Skip all remaining conflicts

  An "all remaining" choice applies to every subsequent conflict without further prompting. Remove each skipped file from the generation plan and reduce N accordingly; record it (with reason "skipped by user") for the final summary.

**4. Print** the analysis summary and the final generation plan (the N files that will actually be written) before entering Phase 2.

### Phase 2: Generate Files

Generate the planned files in order: `AGENTS.md` → root `CLAUDE.md` → each subdirectory `CLAUDE.md`. Before each file, print `[k/N] Generating <path> ...`, where k increments globally across all files and N is the final count from Phase 1.

- Use the corresponding template from the [Templates](#templates) section for each file.
- Every rule must derive from the actual repository structure, files, and observable conventions. Do not fabricate rules.
- **When overwriting an existing file, merge instead of discarding:** carry over rules from the old file that are still valid and not already covered by the newly generated content. Drop only rules that contradict the current repository state.

### Phase 3: Quality Self-Check

Verify the generated files against this checklist and print each item with pass/fail status:

- [ ] **No duplication** — `AGENTS.md` and `CLAUDE.md` do not repeat the same descriptions unnecessarily.
- [ ] **Dangerous operations are covered** — the `Never` section lists the repository's most critical prohibitions.
- [ ] **Nothing is fabricated** — every rule derives from the actual repository structure, files, and observable conventions.
- [ ] **Subdirectory rules are specific** — each subdirectory `CLAUDE.md` contains at least one constraint absent from the root.
- [ ] **Instruction priority is clear** — conflicts between user instructions, subdirectory rules, and root rules are resolved by the stated priority order.

Any failed item must be fixed (edit the affected file, then re-check) before proceeding to Phase 4.

### Phase 4: Translation Sync

Keep Chinese translations of the generated governance files in step with this run.

**Trigger condition:** at least one governance file was actually written in Phase 2, AND `--no-translate` is not set.

- If triggered: invoke the `md-to-zh` skill via the Skill tool, passing the paths of all governance files written this run (including subdirectory `CLAUDE.md` files) as arguments. md-to-zh writes governance-file translations as `.zh.md` next to each source, and its incremental mode skips files that did not change.
- If not triggered: print the reason explicitly (`--no-translate` set, or no files were written).

### Phase 5: Output Summary

Print a final summary:

- Files generated (with paths)
- Files skipped (with reason)
- Files that failed (if any)
- Translation results per file: new translation / incremental update / skipped (or the reason Phase 4 was skipped)

---

## Templates

### AGENTS.md Template

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
- Save generated Markdown under `agent-plan/` unless the user specifies another path; create the directory if it does not exist.
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

### Root CLAUDE.md Template

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

### Subdirectory CLAUDE.md Template

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
