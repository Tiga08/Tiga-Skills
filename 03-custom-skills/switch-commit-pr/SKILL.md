---
name: switch-commit-pr
description: Analyze pending git changes and generate ready-to-run commands by mode: switch (branch creation), commit (adds Conventional Commits commit), pr (adds push + gh pr create); prints commands by default, executes them with --execute. Use when working-tree changes are ready and the user wants branch, commit, or PR commands prepared or run from the current state.
description_zh: 分析待提交的 git 改动并按模式生成可直接运行的命令：switch（创建分支）、commit（追加 Conventional Commits 提交）、pr（追加 push 与 gh pr create）；默认仅打印命令，--execute 时直接执行。适用于工作区改动就绪后，需要从当前状态生成或执行分支 / 提交 / PR 命令的场景。
---

Analyze the current repository state and generate the git/gh commands needed to switch branch, commit, and/or open a PR, staged by mode.

**Arguments:** One positional mode argument is required, followed by an optional flag.

- Positional mode (required, one of): `switch` | `commit` | `pr`
  - `switch` — only generate the branch-switch command (Phase 1–2).
  - `commit` — generate switch + commit commands (Phase 1–3).
  - `pr` — generate switch + commit + push + PR commands (Phase 1–4).
- `--execute` (optional): when present, run each generated command directly via the Bash tool instead of only printing it. When absent (default), only print the commands in fenced code blocks — do not execute anything.

**No-argument behavior:** The mode argument is required; if it is missing or not one of `switch`/`commit`/`pr`, ask the user which mode they want via `AskUserQuestion` instead of guessing.

## Workflow

### Phase 1: Gather state (all modes)

Run the following commands and read their output carefully:

- `git status` — overview of staged, unstaged, and untracked files
- `git branch --show-current` — current branch name
- `git diff --cached --stat` — staged change summary
- `git diff --stat` — unstaged change summary
- `git diff --cached` — full staged diff
- `git diff` — full unstaged diff
- `git log --oneline -5` — recent commit style reference

### Phase 2: Switch (all modes)

1. If the current branch is `main` or `master`:
   - Analyze the pending changes and infer a Conventional Commits type (`feat`, `fix`, `refactor`, `docs`, `chore`, etc. — use the same inference logic as Phase 3) and a short kebab-case description.
   - Generate:
     ```bash
     git switch -c <type>/<kebab-case-desc>
     ```
   - Follow the branch naming style already used in this repo (e.g. `feat/grouped-registry-and-zh-descriptions`, `refactor/restructure-and-draft-commit`, visible in `git log`).
2. If the current branch is not `main`/`master`: do not generate a switch command. State plainly that the current branch is `<name>` and switch is skipped.

### Phase 3: Commit (`commit` and `pr` modes only, in addition to Phase 2)

1. **Analyze changes** — think deeply about what happened:
   - Group related changes by purpose (feature, fix, refactor, docs, chore, etc.)
   - Identify file renames / moves (`renamed:`, or delete + add pairs with similar content)
   - Identify new files vs. modified files
   - Understand the intent behind the changes as a whole
   - Note any untracked files that likely should be included
2. **Determine staging**:
   - If all changes belong to one logical commit, prepare a single `git add` covering everything relevant.
   - If there are unrelated changes that should be separate commits, mention this to the user and ask how to proceed via `AskUserQuestion` (split into multiple commits / merge into one).
     - If the user chooses to split: order the logical groups, then for each group generate an independent `git add` + `git commit` block with its own Conventional Commits message (per step 3). Print a `[k/N]` group index before each block, and under `--execute` run the blocks in group order.
     - If the user chooses to merge: keep a single commit.
   - Exclude files that should not be committed (secrets, build artifacts, OS files).
3. **Draft the commit message** — follow Conventional Commits format:
   - Use the type that best fits: `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`, `build`, `ci`.
   - If changes span multiple types, pick the dominant one or use a broader type with a descriptive scope.
   - Write the commit body in Simplified Chinese (per project convention).
   - Keep the subject line under 72 characters.
   - Add a body paragraph if the changes are non-trivial, explaining what and why.
4. **Generate**:
   ```bash
   git add <files...>
   git commit -m "$(cat <<'EOF'
   type(scope): subject line

   Body paragraph explaining the changes.
   EOF
   )"
   ```

### Phase 4: PR (`pr` mode only, in addition to Phase 2 + Phase 3)

1. **Check existing PR** — run `gh pr view --json url 2>/dev/null` or equivalent. If a PR already exists for this branch, tell the user and show its URL; still generate (or execute) the push step below so the existing PR gets updated, but skip steps 4–6 (`gh pr create`) — never create a duplicate.
2. **Analyze full branch range** — let `<default>` be the detected default branch (`main` or `master`, consistent with Phase 2's determination). If the branch has multiple commits ahead of `<default>`, run `git log <default>..HEAD --oneline` and `git diff <default>...HEAD --stat` to understand the complete scope of the branch, not just the latest diff. Use this combined with Phase 3's change analysis to inform the PR content.
3. **Push** — generate:
   ```bash
   git push -u origin <branch>
   ```
4. **Derive PR title** — from the commit subjects or overall branch purpose, write a concise title ≤ 70 characters. For single-commit branches, reuse the commit subject directly. For multi-commit branches, synthesize a title that captures the overall goal.
5. **Generate PR body**:
   - **Summary**: 1–3 bullet points describing what changed and why. Derive from Phase 3 change analysis and multi-commit history. Focus on impact and purpose, not file lists.
   - **Test plan**: markdown checkbox checklist with concrete verification steps a reviewer can follow.
   - **Signature**: always end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
6. **Generate the command**:
   ```bash
   gh pr create --title "<concise title ≤ 70 chars>" --body "$(cat <<'EOF'
   ## Summary
   - <what changed and why — bullet 1>
   - <bullet 2 if needed>
   - <bullet 3 if needed>

   ## Test plan
   - [ ] <concrete verification step 1>
   - [ ] <concrete verification step 2>

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

## Execution mode behavior

- **Default (no `--execute`)**: only output the state-changing commands for the requested mode's phases, each in a fenced code block. Do not execute any of them; do not make any real changes.
- **`--execute`**: call the Bash tool to run each generated command in order (switch → [commit steps] → [push + pr steps]). Before each command, state in one sentence what is about to happen.
- **Failure handling under `--execute`**: if any command exits non-zero, stop immediately and do not run the remaining commands. Report which commands completed successfully, which one failed (with its error output), and which were not executed because of the failure.
- **Confirmation boundary**: scope questions (e.g., whether to split unrelated changes into multiple commits in Phase 3) may use `AskUserQuestion` in any mode. What `--execute` forbids is per-command execution confirmation — passing `--execute` is itself the user's authorization for this call's scope.

## Rules

- Read-only inspection commands (`git status`, `git diff`, `git log`, `git branch`, `gh pr view`, etc.) may be run via the Bash tool in any mode — they are required for analysis.
- State-changing commands (`git switch`, `git add`, `git commit`, `git push`, `gh pr create`) may only be executed when `--execute` is present; without it, only print them.
- Do not suggest committing files that likely contain secrets (`.env`, credentials, keys); respect `.gitignore`.
- If there are no changes to commit (`switch`/`commit` scenarios) or nothing to push (`pr` scenario), explain the situation and stop — do not generate empty commands.
- In `pr` mode, if the current branch already has an associated remote PR, push to update it but never create a duplicate PR (see Phase 4 step 1).
- End every run with a final summary listing each command generated (or executed) in this run and its status: printed / executed successfully / failed / not executed.
