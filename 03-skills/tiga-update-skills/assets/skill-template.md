---
name: skill-name
description: "Describe what the skill does and its boundaries. Use when the request includes the concrete tasks, artifacts, or situations this skill owns."
---

# Skill Title

State the outcome this skill produces in one concise sentence.

## Inputs

Describe accepted arguments, files, required context, and no-argument behavior.

## Workflow

1. Resolve and validate inputs.
2. Read only the supporting references needed for the selected branch.
3. Perform the task with the smallest safe, maintainable change.
4. Verify the output with the narrowest relevant checks.

## Resources

- Read `references/example.md` when detailed domain rules are needed.
- Run `scripts/example.py` when deterministic processing is required.
- Copy or adapt files under `assets/` only when producing an output artifact.

Remove unused resource entries and sections. Add product-specific frontmatter only when the target client requires that behavior; keep portable and product-specific review verdicts separate.
