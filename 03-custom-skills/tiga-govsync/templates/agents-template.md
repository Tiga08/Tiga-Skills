<!-- Target: AGENTS.md. Line budget: ≤ 60 lines. -->
# [Repo name — one-line positioning]

[Required. Replace the title and write one paragraph covering the repository purpose, tech stack, and core constraints.]

## Structure

[Required. Include only entries whose purpose or authority cannot be read off the path name and its contents. The Authority column marks how authoritative each entry is — a `derived` path that must never be edited directly is exactly the kind of row worth a table row; a self-describing directory is not.]

| Path | Purpose | Authority |
|------|---------|-----------|
| `dir/` | One-line description | primary / derived / config |

[Order the rows with directory entries first, then file entries; sort each group lexicographically by name.]
[If a subdirectory has its own CLAUDE.md, note it below the table, with one line stating that its rules win over this file inside that directory.]

## Commands

[Required if the repository has commands an agent cannot guess. List only repository-specific scripts and non-default invocations. Omit the section entirely when every relevant command is the ecosystem default.]

## Boundaries

[Required. Write only entries that hold in this repository specifically. If a rule reads just as true in any other repository, it belongs to the global config — leave it out.]

**Always:**

[3–5 mandatory behaviors for this repository.]

**Ask First:**

[3–5 operations requiring user confirmation.]

**Never:**

[3–5 strictly prohibited operations.]

<!-- Repository-specific sections are allowed only when they pass the necessity assessment in references/templates.md; place them after the required sections and keep the whole file within its line budget. -->
