# CLAUDE.md — 00-skill-index

This directory contains the unified capability index. The index is **derived content** — it aggregates entries from content directories and must not be treated as an authoritative source.

## File Structure

| Path | Purpose |
|------|---------|
| `README.md` | The capability index — lists all prompts, skills, workflows, and scripts |

## Read Rules

1. **Do not treat index entries as authoritative.** The index is a discovery aid. For accurate details (descriptions, frontmatter, file structure), always read the source file in its content directory.
2. **Use the index only for discovery and navigation.** It tells you what exists and where to find it — not what the content says or how it works.

## Write Rules

1. **"自定义 Skills" section is managed by `sync-index.sh`.** Do not hand-edit this section — run `04-scripts/sync-index.sh` to regenerate it from `05-custom-skills/skills/`.
2. **All other sections require manual updates.** Prompts, Agent Skills, Workflows, and Scripts sections must be updated by hand when content is added, changed, or removed.
3. **Preserve the existing section order.** The index follows a fixed layout: Prompts → Agent Skills → 自定义 Skills → 工作流 → 脚本. Do not reorder sections.
4. **Remove index entries when content is deleted.** Deleting a skill, prompt, or script without removing its index entry leaves a broken reference. Both changes are part of the same task.
5. **Keep entries sorted alphabetically by name within each section.**
6. **Agent Skills table includes an "上游仓库" column.** The third column shows the upstream GitHub repository link, derived from `repoId` → `upstreamUrl` in `skill-registry.json`.
