# Template Conventions

Rules for using the file-backed governance-document templates in Phase 2 and for assessing their section structures in Phases 2 and 4 of tiga-govsync.

## Template catalog

| Target | Template |
| --- | --- |
| `AGENTS.md` | `templates/agents-template.md` |
| Root `CLAUDE.md` | `templates/claude-root-template.md` |
| Subdirectory `CLAUDE.md` | `templates/claude-subdir-template.md` |
| Root `README.md` | `templates/readme-root-template.md` |
| Nested `README.md` outside `docs/` | `templates/readme-nested-template.md` |
| `docs/**/README.md` | `templates/docs-index-template.md` |

Topic documents under `docs/` have no template. Use the catalog templates as generation inputs where generation is allowed and as structural baselines for existing governed documents.

## Line budgets

| Target | Budget |
| --- | --- |
| `AGENTS.md` | ≤ 60 lines |
| Root `CLAUDE.md` | ≤ 40 lines |
| Subdirectory `CLAUDE.md` | ≤ 25 lines |
| Root `README.md` | ≤ 120 lines |
| Nested `README.md` outside `docs/` | ≤ 60 lines |
| `docs/**/README.md` | ≤ 40 lines |

These are targets, not hard cuts. When a file runs over, apply the necessity assessment below to each section and line; never truncate content.

## Template conventions

- The first line is an HTML comment naming the target and line budget. When materializing a real file, delete every HTML comment and every bracketed guidance line.
- The first guidance line for each section starts with `Required.` or `Required if <condition>.` Templates list only required sections, never optional ones.
- Every template ends with the same note: repository-specific sections are allowed only when they pass the necessity assessment below, follow all required sections, and keep the file within its line budget. Remove that HTML comment when materializing the file.
- Every template must respect the ownership table in `references/generate.md`. A fact owned by another file appears only as a link or one line of context.

## Section necessity assessment

Apply these questions in order to every required or repository-specific section:

1. Does this repository have truthful content for the section? If not, omit the whole section. A required section with nothing real to say is evidence that the file itself may not need to exist; never fill it with placeholders.
2. Under the Single-source rule, is this file the authoritative home for that content? If not, keep only a link and at most one sentence of context.
3. Would a reader or agent make a mistake without the section? If not, delete it.

Record every omitted required section and its reason in the Phase 6 summary.
