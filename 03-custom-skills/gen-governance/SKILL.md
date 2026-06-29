---
name: gen-governance
description: Analyze a repository and generate AGENTS.md / CLAUDE.md governance files for AI agent operation
---

Analyze the current repository and generate governance files (`AGENTS.md` and `CLAUDE.md`) so that AI agents can understand and operate correctly within the project.

**Arguments:** Optional flags may appear in the argument list.

- `--dry-run`: Perform the repository analysis and show what files would be generated, without writing anything.
- `--force`: Overwrite all existing governance files without conflict prompts.

**No-argument behavior:** Analyze the current project root directory and generate governance files for it.

**Conflict handling:**
- If `--force` is set, overwrite all existing governance files without prompting.
- If `--dry-run` is set, list what would be generated (including conflicts) without writing.
- Otherwise, if a target file already exists, use `AskUserQuestion` to ask the user:
  - Overwrite this file
  - Skip this file
  - Overwrite all remaining conflicts
  - Skip all remaining conflicts

Apply the chosen action accordingly.

## Workflow

### Phase 1: Repository Analysis

Before generating any files, inspect the repository and output a brief analysis summary.

Required analysis:

- List the top two levels of the directory tree.
- Read the `README` and any existing configuration or governance files, including existing `AGENTS.md`, `CLAUDE.md`, or agent-related files.
- Identify the repository type: application, library, monorepo, content repository, or other.
- Identify the main functional layers of the project.
- Determine which top-level directories need their own `CLAUDE.md`.

Criterion for subdirectory `CLAUDE.md`:

> Generate a subdirectory `CLAUDE.md` only when that directory has ownership semantics, modification rules, or operational constraints that differ from the repository root.

Print the analysis summary before proceeding to generation.

### Phase 2: Generate `AGENTS.md`

Generate `AGENTS.md` at the project root following the template in the [AGENTS.md Template](#agentsmd-template) section. Tailor all content to the actual repository structure, files, and observable conventions. Do not fabricate rules.

Print: `[1/N] Generating AGENTS.md ...`

### Phase 3: Generate Root `CLAUDE.md`

Generate the root `CLAUDE.md` following the template in the [Root CLAUDE.md Template](#root-claudemd-template) section.

Print: `[2/N] Generating CLAUDE.md ...`

### Phase 4: Generate Subdirectory `CLAUDE.md` Files

Generate subdirectory `CLAUDE.md` files only for directories identified as necessary in Phase 1. Use the template in the [Subdirectory CLAUDE.md Template](#subdirectory-claudemd-template) section.

Print: `[3/N] Generating <dir>/CLAUDE.md ...` for each subdirectory file.

### Phase 5: Quality Self-Check

After generating all files, verify the result against this checklist:

- [ ] **No duplication** — `AGENTS.md` and `CLAUDE.md` do not repeat the same descriptions unnecessarily.
- [ ] **Dangerous operations are covered** — the `Never` section lists the repository's most critical prohibitions.
- [ ] **Nothing is fabricated** — every rule derives from the actual repository structure, files, and observable conventions.
- [ ] **Subdirectory rules are specific** — each subdirectory `CLAUDE.md` contains at least one constraint absent from the root.
- [ ] **Instruction priority is clear** — conflicts between user instructions, subdirectory rules, and root rules are resolved by the stated priority order.

Print the checklist with pass/fail status.

### Output Summary

When done, print a final summary:

- Files generated (with paths)
- Files skipped (with reason)
- Files that failed (if any)

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
