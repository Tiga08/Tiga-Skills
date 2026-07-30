# Skill Review Rules

Use this checklist for semantic review after `scripts/audit-skills.py` completes. The official snapshots remain the evidence source; this file is a maintained interpretation for repeatable audits.

## Contents

- [Source priority](#source-priority)
- [Portable Agent Skills core](#portable-agent-skills-core)
- [Claude Code layer](#claude-code-layer)
- [Codex layer](#codex-layer)
- [Review categories](#review-categories)
- [Update safeguards](#update-safeguards)
- [Self-review](#self-review)

## Source priority

Apply sources in this order:

1. The current [Agent Skills specification](https://agentskills.io/specification) for the portable core.
2. The current [Claude Code Skills documentation](https://code.claude.com/docs/en/skills) for Claude-specific behavior.
3. The current [Codex Build Skills documentation](https://developers.openai.com/codex/skills) for Codex-specific behavior.
4. The exact bundled [Claude skill-creator](official/claude-skill-creator.md) and [Codex skill-creator](official/codex-skill-creator.md) snapshots for creation and iteration guidance.
5. Repository instructions and verified repository evidence for local conventions.

If sources disagree, do not silently merge them. Apply the portable specification to the core verdict, then report each product-specific verdict separately. Treat a creator workflow as advice unless a product document or the portable specification states it as a format or behavior requirement.

## Portable Agent Skills core

### Structure

- Require a directory containing `SKILL.md`.
- Allow optional `scripts/`, `references/`, and `assets/`; other directories are also valid.
- Resolve file references from the skill root and avoid deep reference chains.
- Keep `SKILL.md` under 500 lines. Move detailed material to directly linked references.

### Frontmatter

| Field | Requirement |
| --- | --- |
| `name` | Required; 1–64 lowercase ASCII letters, digits, and hyphens; no leading, trailing, or consecutive hyphen; equals the parent directory name |
| `description` | Required; 1–1024 characters; states what the skill does and when to use it |
| `license` | Optional short license name or bundled-license reference |
| `compatibility` | Optional; 1–500 characters; only for real environment requirements |
| `metadata` | Optional mapping of string keys to string values |
| `allowed-tools` | Optional experimental space-separated tool list; client support varies |

Validate YAML syntax separately. A value that happens to parse is not sufficient when its type or meaning violates the field contract.

### Body and resources

- Write executable guidance in imperative form.
- Keep one focused job per skill. Remove background knowledge the agent already has.
- State inputs, outputs, branching decisions, safety boundaries, and verification where they affect correct execution.
- Prefer instructions to scripts until deterministic behavior, repetition, or external tooling justifies code.
- Make scripts self-contained or document dependencies, emit useful errors, and handle relevant edge cases.
- Reference every supporting file the agent needs from `SKILL.md`, explaining when to read or run it.
- Keep large references navigable. Anthropic recommends a table of contents beyond roughly 300 lines; Codex's creator guidance uses the stricter 100-line threshold.
- Keep downloaded upstream snapshots byte-exact for hash verification; do not add local tables of contents to them. Search their existing headings instead.
- Do not add auxiliary `README.md`, changelogs, installation guides, or other files that do not directly help the agent perform the skill.

## Claude Code layer

Claude Code follows the portable format and also recognizes these `SKILL.md` fields:

| Field | Review |
| --- | --- |
| `when_to_use` | Additional trigger text; combined listing text with `description` is capped at 1,536 characters |
| `argument-hint` | Matches the accepted invocation arguments |
| `arguments` | Names positional arguments used through `$name` substitutions |
| `disable-model-invocation` | `true` for user-only workflows or actions whose timing must be controlled |
| `user-invocable` | `false` only for model-only background knowledge |
| `allowed-tools` / `disallowed-tools` | Exact, minimal, turn-scoped tool grants or restrictions |
| `model` / `effort` | Justified turn-scoped overrides |
| `context` / `agent` / `background` | Internally consistent forked-agent execution |
| `hooks` / `paths` / `shell` | Valid lifecycle, activation-path, and shell behavior |

Arguments may use `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, or names declared through `arguments`. Verify every placeholder against the documented interface. Product-specific variables such as `${CLAUDE_SKILL_DIR}` are valid in Claude Code but must not be the only path strategy when the skill promises cross-client portability.

By default, both the user and Claude may invoke a skill. Use `disable-model-invocation: true` for side-effecting workflows that should run only on explicit user request.

## Codex layer

Codex requires `name` and `description` in `SKILL.md`, progressively loads the full body, and discovers repository skills from `.agents/skills` directories between the working directory and repository root. It follows symlinked skill folders.

`agents/openai.yaml` is optional. When present:

- quote `interface.display_name`, `short_description`, and `default_prompt`;
- keep `short_description` between 25 and 64 characters;
- make `default_prompt` a short example that explicitly mentions `$<skill-name>`;
- add icons or brand color only when supplied or justified by existing assets;
- validate complete MCP dependency records;
- set `policy.allow_implicit_invocation` to a boolean. `false` disables implicit selection while preserving explicit `$skill` invocation.

For a side-effecting shared skill, pair Claude's `disable-model-invocation: true` with Codex's `policy.allow_implicit_invocation: false`. For a read-only-by-default workflow, implicit invocation can remain enabled if update behavior requires an explicit mode.

## Review categories

- `[ERROR]`: missing or invalid required structure, YAML, field, referenced path, dependency, command, or script behavior.
- `[WARNING]`: likely over-triggering, ambiguous contract, unsafe invocation policy, portability problem, excessive size, stale metadata, or unverified script.
- `[UPDATE]`: an official snapshot changed and derived rules, templates, or the skill itself may need review.
- `[INFO]`: valid product-specific extension, optional metadata omission, symlink source, or deliberate local convention.

Report the affected layer (`core`, `claude`, `codex`, or `repository`), file, evidence, and smallest concrete fix. A strict validator failure caused only by a documented Claude extension is a portability result, not proof that the shared skill is invalid.

## Update safeguards

- In check mode, write nothing, including generated directories or refreshed snapshots.
- Before updates, capture dirty targets and show diffs. Never erase unrelated user changes.
- Preserve valid behavior and client-specific fields.
- Never update an external symlink target unless the user explicitly placed that source in scope.
- After editing `SKILL.md`, synchronize its Simplified Chinese translation according to repository instructions.
- Re-run structural checks, relevant script tests, and repository validators after every update.

## Self-review

When reviewing `tiga-update-skills`:

1. Run `<skill-dir>/scripts/refresh-official-docs.py --check`, resolving `<skill-dir>` from the active skill rather than the current working directory.
2. If upstream content changed, inspect the full diff before refreshing snapshots.
3. Re-read both refreshed documents completely.
4. Compare this checklist and every file in `assets/` against changed requirements.
5. Audit `SKILL.md`, `agents/openai.yaml`, and both scripts using the revised baseline.
6. Test `--check`, `--diff`, `--update` no-op behavior, default multi-skill discovery, and explicit self-target resolution.
