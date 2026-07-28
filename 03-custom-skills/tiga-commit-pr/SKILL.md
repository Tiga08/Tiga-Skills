---
name: tiga-commit-pr
description: "Analyze Git work in the current repository and prepare branch, Conventional Commit, and PR workflows in four modes: switch, commit, pr, and push. push commits on the current branch and pushes directly, skipping branch switching and PR (allowed on base branches for solo repos). Execute the generated commands by default, or print them without running anything with --dry-run, while preserving working-tree files and respecting pre-staged changes. Use when the user wants branch or commit commands for pending changes, wants to push existing branch commits and open or update a PR, or wants to commit and push directly on the current branch without a PR."
argument-hint: "switch|commit|pr|push [--dry-run]"
arguments: [mode]
disable-model-invocation: true
allowed-tools: Bash(git restore --staged *)
compatibility: Requires git and the GitHub CLI (gh)
---

Analyze the current repository state and generate the git/gh commands needed to switch branch, commit, and/or open a PR, staged by mode.

**Arguments:** One positional mode argument is required, followed by an optional flag.

本次调用：`$ARGUMENTS` — 模式 `$mode`

- Positional mode (required, one of): `switch` | `commit` | `pr` | `push`
  - `switch` — only generate the branch-switch command (Phase 1–2).
  - `commit` — generate switch + commit commands (Phase 1–3).
  - `pr` — generate switch + commit + push + PR commands (Phase 1–4).
  - `push` — commit on the **current branch** (Phase 1 + Phase 3), then push directly (Phase 5). Skips Phase 2 branch switching and Phase 4 PR. **Allowed even when the current branch is a base branch (`main`/`master`/`dev`)** — intended for solo-maintained repos where branch + PR ceremony is unnecessary.
- `--dry-run` (optional): when present, only print the commands in fenced code blocks — do not execute anything and make no real changes. When absent (default), run each generated command directly via the Bash tool.

**No-argument behavior:** The mode argument is required; if `$mode` is empty or not one of `switch`/`commit`/`pr`/`push`, ask the user which mode they want via `AskUserQuestion` instead of guessing.

## Workflow

### Phase 1: Gather state (all modes)

The state below was gathered before this run started — read it carefully and do **not** re-run these commands:

```!
git branch --show-current
git status --porcelain
git log --oneline -5
git diff --cached --stat
git diff --stat
```

Read it as: current branch name; machine-readable per-file state (staged / unstaged / untracked / deleted / renamed — the authoritative input for the staging protocol and execution fault tolerance below); recent commit style reference; staged change summary; unstaged change summary.

The full diffs (`git diff --cached`, `git diff`) are **not** pre-injected — read them on demand with the Bash tool when the change analysis needs them.

**Repository guard:** if the injected output above is `fatal: not a git repository` (or otherwise shows no repository), report that this skill requires a git repository and stop — generate nothing.

### Phase 2: Branch check + switch (`switch`, `commit`, `pr` modes)

**`push` mode skips this phase entirely** — it never creates a branch and never determines `<base>`; it commits and pushes on the current branch as-is (see Phase 5).

The allowed base branches are `main`, `master`, and `dev`. This phase decides whether a new branch is created, and determines `<base>` — this run's base branch, used by Phase 4 for the branch-range analysis and the PR target.

1. If the current branch is one of the allowed base branches:
   - Record it as `<base>`.
   - Analyze the pending changes and infer a Conventional Commits type (`feat`, `fix`, `refactor`, `docs`, `chore`, etc. — use the same inference logic as Phase 3) and a short kebab-case description.
   - Generate:
     ```bash
     git switch -c <type>/<kebab-case-desc>
     ```
   - Follow the branch naming style already used in this repo (e.g. `feat/grouped-registry-and-zh-descriptions`, `refactor/restructure-and-draft-commit`, visible in `git log`).
2. If the current branch is not an allowed base branch, do **not** abort — decide interactively:
   - `switch` mode: ask via `AskUserQuestion` — the current branch is `<name>`, not `main`/`master`/`dev`; still create a new branch from here? If confirmed, generate the switch command as in step 1; otherwise stop without generating any commands.
   - `commit` / `pr` mode, with pending changes (per `git status --porcelain`): ask via `AskUserQuestion` — create a new branch first, or commit on the current branch?
     - "Switch first": generate the switch command as in step 1, then continue to Phase 3.
     - "Stay on current branch": skip the switch command and continue to Phase 3 on the current branch.
   - `pr` mode, working tree clean: treat this as a **resume** run — no question needed; skip Phase 3 entirely and go straight to Phase 4 (push + create/update PR). This covers "branch was switched and committed in a previous run, now only push + PR is left" and "retry after a failed push".
   - In all of these non-base-branch cases, determine `<base>` by merge-base distance: among `main`/`master`/`dev` branches that exist locally, pick the one closest to `HEAD` (smallest `git rev-list --count <candidate>..HEAD`); if only one exists, use it.
   - This branch decision applies in both default (executing) and `--dry-run` modes — it is a scope question (see the Confirmation boundary rule), determining which commands are generated, not a per-command confirmation.

### Phase 3: Commit (`commit`, `pr`, and `push` modes)

For `commit` and `pr` this runs in addition to Phase 2; for `push` it runs directly after Phase 1 on the current branch (no Phase 2). The change analysis, grouping, staging protocol, message drafting, and file-safety hard rules below apply identically in all three modes.

1. **Analyze changes** — think deeply about what happened:
   - Analyze the **full change set**: staged + unstaged + untracked files merged as one whole. Whether the user pre-staged some or all of it must not affect the analysis. Use `git diff --cached`, `git diff`, and `git status --porcelain` together to understand each file's content change and exact state.
   - Group related changes by purpose (feature, fix, refactor, docs, chore, etc.)
   - Identify file renames / moves (`renamed:`, or delete + add pairs with similar content)
   - Identify new files vs. modified files vs. deleted files
   - Understand the intent behind the changes as a whole
   - Note any untracked files that likely should be included
2. **Decide grouping automatically**:
   - If the groups have clearly independent purposes and no dependency on each other, split into multiple commits directly — **do not ask**. Order the logical groups, then for each group generate an independent `git add` + `git commit` block with its own Conventional Commits message (per step 4). Print a `[k/N]` group index before each block, and unless `--dry-run`, run the blocks in group order.
   - If the group boundaries are ambiguous or the changes are coupled, ask how to proceed via `AskUserQuestion` (split into multiple commits / merge into one).
   - If the changes cannot be meaningfully split, keep a single commit.
   - Exclude files that should not be committed (secrets, build artifacts, OS files).
3. **Staging protocol** — respect what the user has already staged:
   - If pre-staged content exists **and** multiple commits are needed: the first generated command must be `git restore --staged .` to unstage everything. This touches **only the index, never working-tree files** — a staged deletion becomes an unstaged deletion, and the file stays deleted on disk exactly as the user left it.
   - Then for each group in order, generate `git add -A -- <group files...>` followed by its `git commit`. The `-A` + `--` pathspec form correctly stages deletions of files that no longer exist in the working tree.
   - If only a single commit is needed and the pre-staged content already matches the target scope: skip the restore step; just add whatever is missing (or commit directly if nothing is missing). Do not unstage and re-add for no reason.
4. **Draft the commit message** — follow Conventional Commits format:
   - Use the type that best fits: `feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`, `build`, `ci`.
   - If changes span multiple types, pick the dominant one or use a broader type with a descriptive scope.
   - Write the commit body in Simplified Chinese (per project convention).
   - Keep the subject line under 72 characters.
   - Add a body paragraph if the changes are non-trivial, explaining what and why.
5. **Generate** (one block per commit group):
   ```bash
   git add -A -- <files...>
   git commit -m "$(cat <<'EOF'
   type(scope): subject line

   Body paragraph explaining the changes.
   EOF
   )"
   ```

#### File-safety hard rules

These apply to every command this skill generates or executes:

- The only allowed unstaging command is `git restore --staged <path>` (or `.`) — it modifies the index only.
- **Never** generate or execute: `git restore <path>` (without `--staged`), `git checkout -- <path>`, `git reset --hard`, `git clean`, or `git rm`. All of them can delete or overwrite working-tree files.
- For files the user has already deleted: only record the deletion with `git add -A -- <path>`. Never delete a file on the user's behalf, and never resurrect a file the user deleted.
- **Never** generate or execute `git push --force` or `git push --force-with-lease` (rewrites remote history), and never auto-resolve a rejected push with `git pull --rebase` / merge (can touch working-tree files). If any push is rejected (e.g. non-fast-forward), stop and report — let the user decide.

### Phase 4: PR (`pr` mode only, in addition to Phase 2 + Phase 3)

When Phase 2 classified this run as a resume (clean non-base branch), Phase 3 is skipped and this phase starts directly from the current branch state.

1. **Check existing PR** — run `gh pr view --json url 2>/dev/null` or equivalent. If a PR already exists for this branch, tell the user and show its URL; still generate (or execute) the push step below so the existing PR gets updated, but skip steps 4–6 (`gh pr create`) — never create a duplicate.
2. **Analyze full branch range** — let `<base>` be this run's base branch as determined in Phase 2 (the allowed branch the run started from, or the merge-base-nearest of `main`/`master`/`dev`). If the branch has multiple commits ahead of `<base>`, run `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat` to understand the complete scope of the branch, not just the latest diff. Use this combined with Phase 3's change analysis to inform the PR content.
3. **Push** — generate:
   ```bash
   git push -u origin <branch>
   ```
4. **Derive PR title** — from the commit subjects or overall branch purpose, write a concise title ≤ 70 characters. For single-commit branches, reuse the commit subject directly. For multi-commit branches, synthesize a title that captures the overall goal.
5. **Generate PR body**:
   - **Summary**: 1–3 bullet points describing what changed and why. Derive from Phase 3 change analysis and multi-commit history. Focus on impact and purpose, not file lists.
   - **Test plan**: markdown checkbox checklist with concrete verification steps a reviewer can follow.
   - **Signature**: always end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
6. **Generate the command** — always pass `--base <base>` explicitly (even when `<base>` is the repo default branch), so a branch cut from `dev` opens its PR against `dev`:
   ```bash
   gh pr create --base <base> --title "<concise title ≤ 70 chars>" --body "$(cat <<'EOF'
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

### Phase 5: Push (`push` mode only, in addition to Phase 1 + Phase 3)

This phase replaces Phase 4 for `push` mode. There is no branch switch (Phase 2 was skipped), no `<base>` analysis, and no PR — just commit on the current branch, then push it directly.

1. **Warn** — always print a one-line warning first (in both default (executing) and `--dry-run` modes):
   `⚠️ push 模式：将在当前分支 <name> 上提交并直接推送，跳过 PR`。
   If `<name>` is a base branch (`main`/`master`/`dev`), extend the warning to state that this pushes directly to a protected branch with no PR review.
2. **Commit** — run Phase 3 exactly as written (change analysis, automatic grouping, staging protocol, Conventional Commit message, and the File-safety hard rules). `push` mode adds nothing to and removes nothing from Phase 3's commit behavior.
3. **Clean-tree resume** — decide from the Phase 1 state:
   - Pending changes exist → do Phase 3 (step 2), then push.
   - Working tree clean but the current branch has unpushed local commits (e.g. `git log @{u}..HEAD` non-empty, or no upstream yet with commits ahead) → skip the commit step and push the existing commits.
   - Working tree clean and already in sync with the remote → report "无需推送" and stop; do not generate any commands.
4. **Push** — generate exactly this, using the current branch name (never force, never auto-rebase):
   ```bash
   git push -u origin <current-branch>
   ```
   Do not run `gh pr ...` in this mode.

## Execution mode behavior

- **Read-only inspection commands** (`git status`, `git diff`, `git log`, `git branch`, `gh pr view`, etc.) may be run via the Bash tool in any mode — they are required for analysis.
- **Default (no `--dry-run`)**: call the Bash tool to run each generated state-changing command in order — `switch`/`commit`/`pr` run switch → [commit steps] → [push + pr steps]; `push` runs [commit steps] → `git push` on the current branch. Before each command, state in one sentence what is about to happen.
- **`--dry-run`**: only output the state-changing commands (`git switch`, `git restore --staged`, `git add`, `git commit`, `git push`, `gh pr create`) for the requested mode's phases, each in a fenced code block. Do not execute any of them; do not make any real changes.
- **`push` mode authorization**: explicitly choosing `push` mode is itself the user's authorization to commit and push directly on the current branch, including a base branch (`main`/`master`/`dev`). Print the Phase 5 warning, then proceed — do **not** add a second confirmation.
- **Staging command form**: all staging commands must use the `git add -A -- <paths>` form, and the path list must come from the actual `git status --porcelain` state gathered in Phase 1. Do not re-add files that are already staged in their target state.
- **`git add` pathspec fault tolerance**: if a `git add` fails with a pathspec error (e.g. the path exists in neither the working tree nor the index because its deletion was already staged), do not stop immediately. Re-run `git status --porcelain` and check: if the file's intended change is in fact already staged, skip that command and continue with the remaining commands; otherwise apply the normal stop-on-failure handling below.
- **Failure handling when executing**: for all other commands (switch / commit / push / pr create), if any command exits non-zero, stop immediately and do not run the remaining commands. Report which commands completed successfully, which one failed (with its error output), and which were not executed because of the failure.
- **Confirmation boundary**: scope questions (e.g., the branch decision on a non-base branch in Phase 2, or resolving ambiguous commit grouping in Phase 3) may use `AskUserQuestion` in any mode. What default execution forbids is per-command execution confirmation — the user invoking this skill is itself the authorization for this call's scope.

## Rules

- Do not suggest committing files that likely contain secrets (`.env`, credentials, keys); respect `.gitignore`.
- If there are no changes to commit (`switch`/`commit` scenarios) or nothing to push (`pr`/`push` scenario — no pending changes and no unpushed commits), explain the situation and stop — do not generate empty commands.
- End every run with a final summary listing each command generated (or executed) in this run and its status: printed / executed successfully / failed / not executed.
