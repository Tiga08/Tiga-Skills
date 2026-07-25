# Templates

Templates for the governance files generated in Phase 2 of tiga-govsync.

## Line budgets

Target `AGENTS.md` ≤ 60 lines, root `CLAUDE.md` ≤ 40 lines, subdirectory `CLAUDE.md` ≤ 25 lines. These are targets, not hard cuts — when a file runs over, drop content by asking of each line "would the agent get this wrong without it?", never by truncating.

## AGENTS.md Template

```markdown
# [Repo name — one-line positioning]

[One paragraph: repository purpose, tech stack, and core constraints.]

## Structure

| Path | Purpose | Authority |
|------|---------|-----------|
| `dir/` | One-line description | primary / derived / config |

[Include only entries whose purpose or authority cannot be read off the path name and its contents. The Authority column marks how authoritative each entry is — a `derived` path that must never be edited directly is exactly the kind of row worth a table row; a self-describing directory is not.]
[Order the rows with directory entries first, then file entries; sort each group lexicographically by name.]
[If a subdirectory has its own CLAUDE.md, note it below the table, with one line stating that its rules win over this file inside that directory.]

## Commands

[Optional section. List only commands an agent cannot guess — repository-specific scripts and non-default invocations. Omit the section entirely when every relevant command is the ecosystem default.]

## Boundaries

**Always:**

[3–5 mandatory behaviors for this repository.]

**Ask First:**

[3–5 operations requiring user confirmation.]

**Never:**

[3–5 strictly prohibited operations.]

[Write only entries that hold in *this* repository specifically. If a rule reads just as true in any other repository, it belongs to the global config — leave it out.]
```

## Root CLAUDE.md Template

```markdown
@AGENTS.md

## Constraints

[1–5 operational constraints for the root project, each derived from this repository's own structure or conventions.]

## Common Gotchas

[1–5 pitfalls that newcomers, including AI agents, actually hit in this repository.]

Format each item as:

1. **Short title.** Explain why it is a pitfall and describe the correct approach.
```

## Subdirectory CLAUDE.md Template

```markdown
# [Directory name] — Operational Rules

[One paragraph: responsibilities and ownership semantics.]

## Rules

[3–5 operational rules specific to this directory. At least one must be a constraint that is not already present in the root `CLAUDE.md`.]
```
