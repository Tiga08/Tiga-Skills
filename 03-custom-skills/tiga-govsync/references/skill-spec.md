# Cross-client Skill Compliance

Rules for Phase 3 of tiga-govsync — checking project-owned skills against the portable Agent Skills core plus the official Claude Code and Codex extensions.

## Compatibility layers

Validate each layer independently. A field that is an official Claude Code extension is not an Agent Skills core violation merely because a strict portable validator does not recognize it.

### Portable Agent Skills core

| Field | Required | Form |
| --- | --- | --- |
| `name` | yes | 1–64 lowercase letters, digits, and hyphens; no leading, trailing, or consecutive hyphen; must equal the parent directory |
| `description` | yes | non-empty YAML string, ≤ 1024 characters; states what the skill does and when to use it |
| `license` | no | short license name or bundled-license reference |
| `compatibility` | no | non-empty string, ≤ 500 characters, only when runtime requirements need stating |
| `metadata` | no | mapping whose keys and values are strings |
| `allowed-tools` | no | space-separated string; experimental and not portable across every client |

Supporting resources normally live under `references/`, `scripts/`, or `assets/`, but other directories are allowed. Reference them with paths relative to the skill root, such as `references/policy.md` or `templates/report-template.md`.

### Claude Code extensions

Claude Code additionally recognizes:

| Field | Purpose |
| --- | --- |
| `when_to_use` | extra trigger text appended to `description` |
| `argument-hint` | slash-command autocomplete hint |
| `arguments` | names for positional `$name` substitutions |
| `disable-model-invocation` / `user-invocable` | automatic and user invocation policy |
| `allowed-tools` / `disallowed-tools` | turn-scoped tool grants or restrictions |
| `model` / `effort` | turn-scoped model and effort overrides |
| `context` / `agent` / `background` | forked-subagent execution |
| `hooks` / `paths` / `shell` | lifecycle, activation-path, and shell behavior |

`$ARGUMENTS`, `$ARGUMENTS[N]`, and `$N` work without `arguments`. Require `arguments` only when the body uses named substitutions such as `$mode`. The combined `description` and `when_to_use` listing text must not exceed Claude Code's 1536-character cap.

### Codex metadata

`agents/openai.yaml` is optional, but validate it when present:

- `interface.display_name`, `short_description`, and `default_prompt` are quoted strings; `short_description` is 25–64 characters.
- `interface.default_prompt` explicitly mentions `$<skill-name>`.
- `policy.allow_implicit_invocation` is a boolean when present and defaults to `true`.
- Validate declared MCP dependencies for complete `type`, `value`, `description`, `transport`, and `url` fields.

## Checks

- `[MISSING]` — portable `name` or `description` is absent or empty; a named `$argument` is used without a matching `arguments` entry; a declared supporting path or required dependency field is absent.
- `[UNKNOWN]` — a `SKILL.md` top-level key belongs to neither the portable core nor the supported Claude Code extensions, or an `agents/openai.yaml` key is outside the documented Codex schema. Report which compatibility layer rejected it.
- `[MISMATCH]` — a field violates its layer's form or length constraints; `name` differs from the parent directory; `argument-hint` disagrees with arguments the body parses; `agents/openai.yaml` is stale relative to the skill or has an invalid invocation policy.
- `[STALE]` — the body documents a command or skill-root-relative path that no longer exists. Product-specific variables such as `${CLAUDE_SKILL_DIR}` are stale portability assumptions when a shared Claude/Codex skill can use a skill-root-relative path instead.
- `[BLOAT]` — the body contains detail better loaded from supporting files. Judge content, not an invented 120-line limit: the official guidance is to keep `SKILL.md` under 500 lines and move branch-specific policies, schemas, examples, or templates out as needed.

## Invocation policy

For a shared task skill with side effects:

- Claude Code: normally set `disable-model-invocation: true`.
- Codex: set `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.

For a skill deliberately callable by another skill, keep Claude's `disable-model-invocation` unset and Codex implicit invocation enabled unless its documented calling contract provides another explicit route. `tiga-translate` is this repository's intentional example.

Do not remove valid Claude extensions merely to satisfy a strict portable-core validator. Report the portable validator result separately, then judge the shared skill against all three compatibility layers.

## Report and fixes

Group findings by priority — `[MISSING]` > `[UNKNOWN]` > `[MISMATCH]` > `[STALE]` > `[BLOAT]` — and then by file. State the affected compatibility layer, offending key or line, and concrete fix. Close with counts per category and per compatibility layer, plus the number of skills that passed.

`check` reports only. `update` applies fixes directly except for pre-existing dirty targets protected by Phase 1. `fix` asks through the host's user-confirmation mechanism, offering apply / skip / apply all remaining / skip all remaining.

**Hard constraint:** never modify a skill outside the governed repository. Do not follow registry directories such as `02-agent-skills/`, `.claude/skills`, or `.codex/skills`; report external sources without rewriting them.
