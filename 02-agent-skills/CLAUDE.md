# CLAUDE.md — 02-agent-skills

This directory holds imported agent skills. All skills here are managed through `manage-skills.sh` and tracked in `skill-registry.json`. Treat content as **read-only** — edits must happen at the external source and be re-imported.

## File Structure

| Path | Purpose |
|------|---------|
| `skills/{name}/SKILL.md` | Skill definition (imported, read-only) |
| `skills/{name}/scripts/` | Optional supporting scripts (imported with the skill) |
| `skill-registry.json` | Import tracking — source paths, hashes, repo metadata |
| `README.md` | Format spec and usage guide |

## Read Rules

1. **Check the registry before modifying any skill.** If a skill appears in `skill-registry.json`, it is an external import — do not edit it in place. Run `manage-skills.sh status` to see whether local content matches the recorded `sourceHash`.
2. **Understand `repos` configuration.** The `repos` section in `skill-registry.json` maps repo IDs to local clone paths, upstream/origin URLs, and sync metadata. Skills reference their source repo via the `repoId` field. The `upstreamUrl` is also used to populate the "上游仓库" column in the skill index.
3. **Registry `description` may override SKILL.md.** The `description` field in `skill-registry.json` can be customized after import to better fit the local index — it is not required to match the SKILL.md frontmatter verbatim.

## Write Rules

1. **Never directly edit an imported skill.** Edit at the external source, then run `manage-skills.sh update {name}` to re-import. Direct edits will be overwritten on next update and cause `sourceHash` mismatches.
2. **Never hand-edit `skill-registry.json`.** Use `manage-skills.sh` commands (`import`, `remove`, `update`) to modify registry entries. Manual edits risk breaking hash tracking and repo associations.
3. **Run `manage-skills.sh status` before importing or updating.** This shows hash mismatches, missing sources, and pending updates — prevents accidental overwrites.
4. **Update the index after import changes.** After `import`, `update`, or `remove`, update `00-skill-index/README.md` with the corresponding entry change.
5. **Run `sync-upstream.sh status` before `sync`.** The sync uses `--ff-only` merge — if the local clone has diverged from upstream, it will fail. Check status first to preview changes and catch divergence early.

## File Format Standards — SKILL.md

Every skill directory must contain a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name            # Required: kebab-case, must match directory name
description: What it does   # Required: concise, includes trigger keywords
agents:                     # Optional: link targets (default: all)
  - claude
  - codex
  - agents
---
```

### Field Constraints

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | kebab-case; must match the containing directory name |
| `description` | Yes | One line; include trigger keywords for semantic matching |
| `agents` | No | Subset of `claude`, `codex`, `agents`; omit to target all |

The body after frontmatter is free-form Markdown — the skill's instructions, examples, and rules.
