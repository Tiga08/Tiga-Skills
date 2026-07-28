# Skill Spec Compliance

Rules for Phase 4 of tiga-govsync — checking `SKILL.md` files against the official Agent Skills specification, reporting findings, and (in `update` / `fix`) applying them.

## Frontmatter fields

Claude Code fields:

| Field | Required | Form |
| --- | --- | --- |
| `name` | yes | lowercase kebab-case, ≤ 64 chars, must equal the skill's directory name |
| `description` | yes | single-line string; what the skill does and when to use it |
| `when_to_use` | no | single-line string; trigger conditions when kept out of `description` |
| `argument-hint` | no | quoted usage string shown in the slash-command hint |
| `arguments` | no | list of positional argument names, e.g. `[mode]`, bound as `$mode` |
| `disable-model-invocation` | no | `true` makes the skill user-invocable only |
| `user-invocable` | no | `false` hides the skill from the slash-command list |
| `allowed-tools` / `disallowed-tools` | no | tool patterns permitted / denied for this skill |
| `model` / `effort` | no | model id; effort level for the skill's own execution |
| `context` / `agent` / `background` | no | run the skill in a fresh context / named subagent / background |
| `hooks` / `paths` / `shell` | no | lifecycle hooks; path scoping; shell to execute snippets with |

Agent Skills open-standard fields, valid but not interpreted by Claude Code: `license`, `compatibility`, `metadata`.

Any other top-level key is a violation — it is almost always a spelling drift (`when-to-use`, `argument_hint`, `allowed_tools`).

## Checks

Label findings the same way `audit.md` does, with two additions.

- `[MISSING]` — `name` or `description` absent or empty. `arguments` declared in the body but no `argument-hint`. A skill that reads `$ARGUMENTS` positionally but declares no `arguments`.
- `[MISMATCH]` — `name` differs from the directory name, is not lowercase kebab-case, or exceeds 64 chars. `argument-hint` disagrees with the modes/flags the body actually parses. `description` + `when_to_use` together exceed 1536 characters (the skill-listing truncation threshold).
- `[UNKNOWN]` — a top-level frontmatter key outside the table above.
- `[STALE]` — the body documents a command, path, or reference file that no longer exists.
- `[BLOAT]` — the body carries reference material that belongs in `references/`. `SKILL.md` stays in context for the whole session, so every line is a repeated token cost: keep the body to the invocation contract and workflow phases, and move per-branch operational detail out. A body past ~120 lines with no `references/` directory is the signal. Supporting files must be referenced as `${CLAUDE_SKILL_DIR}/references/<file>.md`; a bare relative path is itself a finding.

**`disable-model-invocation`:** a task-type skill with side effects (writes files, runs git, changes a registry) should set it `true` so it is only ever triggered deliberately. The exception is a skill invoked by other skills through the Skill tool — it must leave the field unset, or the caller cannot reach it. `tiga-translate` is exactly this case and says so in an "Invocation constraint" section; respect any such declaration in the body instead of flagging it.

## Report and fixes

Group findings by priority — `[MISSING]` > `[UNKNOWN]` > `[MISMATCH]` > `[STALE]` > `[BLOAT]` — and within a group by file. Give each finding its file, the offending key or line, and the concrete fix. Close with a count per category plus the number of skills that passed.

`check` reports only. `update` applies the fixes directly. `fix` confirms each one via `AskUserQuestion` before applying, offering apply / skip / apply all remaining / skip all remaining.

**Hard constraint:** never modify a skill outside the repository being governed. Registry directories such as `02-agent-skills/` are symlinks into upstream repositories — discovery must not follow them, and an external source is reported, never rewritten.
