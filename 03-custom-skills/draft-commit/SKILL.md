---
name: draft-commit
description: Analyze all pending git changes and generate a ready-to-use git commit command without executing it
description_zh: 分析所有待提交的 git 变更，生成可直接使用的 commit 命令（不执行）
---

Analyze all uncommitted changes in the current repository and produce a single, ready-to-paste `git commit` command. **Do NOT execute** the commit.

## Workflow

1. **Gather state** — run the following commands and read their output carefully:
   - `git status` — overview of staged, unstaged, and untracked files
   - `git diff --cached --stat` — staged change summary
   - `git diff --stat` — unstaged change summary
   - `git diff --cached` — full staged diff
   - `git diff` — full unstaged diff
   - `git log --oneline -5` — recent commit style reference

2. **Analyze changes** — think deeply about what happened:
   - Group related changes by purpose (feature, fix, refactor, docs, chore, etc.)
   - Identify file renames / moves (`renamed:`, or delete + add pairs with similar content)
   - Identify new files vs. modified files
   - Understand the intent behind the changes as a whole
   - Note any untracked files that likely should be included

3. **Determine staging** — based on the analysis:
   - If all changes belong to one logical commit, prepare a single `git add` covering everything relevant
   - If there are unrelated changes that should be separate commits, mention this to the user and ask how to proceed via `AskUserQuestion`
   - Exclude files that should not be committed (secrets, build artifacts, OS files)

4. **Draft the commit message** — follow Conventional Commits format:
   - Use the type that best fits: `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`, `build`, `ci`
   - If changes span multiple types, pick the dominant one or use a broader type with a descriptive scope
   - Write the commit body in Simplified Chinese (per project convention)
   - Keep the subject line under 72 characters
   - Add a body paragraph if the changes are non-trivial, explaining what and why

5. **Output the command** — present the complete command block:

   ```bash
   git add <files...>
   git commit -m "$(cat <<'EOF'
   type(scope): subject line

   Body paragraph explaining the changes.
   EOF
   )"
   ```

   Show the command in a fenced code block so the user can copy-paste it directly.

## Rules

- **Never execute** `git commit` or `git add`. Only output the commands.
- If there are no changes to commit, say so and stop.
- If staged and unstaged changes exist, explain the current staging state and recommend what to include.
- Respect `.gitignore` — do not suggest adding ignored files.
- Do not suggest committing files that likely contain secrets (`.env`, credentials, keys).
