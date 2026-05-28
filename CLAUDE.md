@AGENTS.md

# CLAUDE.md — Tiga-Skills

## Architecture Decisions

**Numbered-prefix directories:** The `00-` through `05-` prefixes enforce a discovery-order layout — index first, then content types by category, then tooling. Agents and humans scanning the repo encounter the index before content, and content before the scripts that operate on it.

**Separate `02-agent-skills` and `05-custom-skills`:** Imported external skills (tracked by `skill-registry.json`) live in `02-agent-skills/`, while user-authored skills live in `05-custom-skills/`. This prevents `manage-skills.sh remove` from accidentally deleting user work, and makes ownership clear at a glance.

**`agent-plan/` as scratch space:** Drafts and plans live outside the content directories. Content is promoted from `agent-plan/` to `01-prompts/`, `02-agent-skills/`, etc. through deliberate action — never automatically.

**`00-skill-index/` as derived index:** The index aggregates entries from content directories. `sync-index.sh` can regenerate the custom skills section, but standard skills and prompts require manual updates — full automation would require parsing all content formats.

**Per-directory `README.md` as format specs:** Each content directory defines its own file format and conventions in a `README.md`. This keeps format rules close to the content they govern and avoids bloating the root-level governance files.

**Subdirectory `CLAUDE.md` for ownership semantics:** `00-skill-index/`, `02-agent-skills/`, and `05-custom-skills/` each have their own `CLAUDE.md` because their read/write rules differ fundamentally from the root-level defaults — derived vs. imported-read-only vs. user-editable. A single root `CLAUDE.md` cannot encode these distinctions without becoming a dispatch table; layer-specific files let each directory state its own constraints directly.

## Common Gotchas

1. **Editing imported skills in place.** Skills in `skill-registry.json` have a `sourceHash`. Editing them directly causes `manage-skills.sh status` to report a mismatch, and `update` will overwrite your changes. Always edit at the external source and re-import.

2. **Forgetting the index update.** Adding a skill or prompt without updating `00-skill-index/README.md` makes it undiscoverable. `sync-index.sh` only covers custom skills — everything else needs a manual index entry.

3. **Treating `agent-plan/` as curated content.** Files there are drafts. If something is worth keeping, promote it to the appropriate content directory — don't reference `agent-plan/` paths as stable locations.

4. **Creating symlinks manually.** `link-skills.sh` has specific logic for preserving existing agent config content (e.g., `~/.codex/skills/.system/`). Manual symlinks can conflict with the script and cause silent failures on `--unlink`.

5. **Assuming `CLAUDE.zh.md` auto-updates.** It is a manual Chinese translation of this file. After modifying `CLAUDE.md`, the translation needs a separate update.

6. **Running `sync-upstream.sh sync` without checking status first.** Always run `status` to preview changes. The sync does a `--ff-only` merge in the local clone — if the local branch has diverged, it will fail. Resolve manually before re-running.

## Agent Collaboration Rules

1. **Plan mode for structural changes.** Tasks that add, remove, or reorganize directories, or modify governance files (`AGENTS.md`, `CLAUDE.md`, root `README.md`), must use plan mode first.
2. **Read directory READMEs before writing.** Each content directory has a `README.md` that is the authoritative format specification. Do not rely on memory or root-level summaries.
3. **Drafts go to `agent-plan/`.** Generated plans, analysis, or intermediate content goes to `agent-plan/`. Promote to a content directory only with user approval.
4. **Index updates are part of the task.** Adding content without updating `00-skill-index/README.md` is an incomplete task.
5. **Read subdirectory `CLAUDE.md` before operating on its files.** When a content directory has its own `CLAUDE.md`, read it before any read or write operation. Subdirectory rules take precedence over root-level rules for content in that directory.
