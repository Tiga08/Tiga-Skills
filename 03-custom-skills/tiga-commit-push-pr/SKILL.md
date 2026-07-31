---
name: tiga-commit-push-pr
description: "Safely prepare or execute Git branch, Conventional Commit, push, and GitHub pull-request workflows. Use when switching branches, committing pending work, pushing the current branch directly, opening or updating a PR, or previewing these actions."
argument-hint: "switch|commit|pr|push [--dry-run]"
arguments:
  - mode
disable-model-invocation: true
compatibility: "Requires Git. push and pr require an origin remote; pr also requires the GitHub CLI (gh)."
---

# Tiga Commit, Push, and PR

Analyze the current repository and safely switch branches, create commits, push, or open a pull request.

Parse the invocation as one required mode followed by optional `--dry-run`. Claude Code also exposes the raw invocation as `$ARGUMENTS` and the declared first argument as `$mode`; do not treat either placeholder as input when the host does not expand it.

| Mode | Workflow |
| --- | --- |
| `switch` | Inspect and create a branch only. |
| `commit` | Inspect, decide the branch, and commit. |
| `pr` | Inspect, commit or resume, push, and create or update a PR. |
| `push` | Commit on the current branch and push it directly; never switch branches or open a PR. Base branches are allowed for solo repositories. |

With `--dry-run`, print state-changing commands without executing them. If the mode is missing or invalid, ask the user to choose one through the host confirmation mechanism; use one concise plain-text question when structured confirmation is unavailable.

## 1. Inspect

Gather fresh state on every run:

```bash
git branch --show-current
git status --porcelain=v1
git log --oneline -5
git diff --cached --stat
git diff --stat
```

Stop if this is not a Git repository. Treat `git status --porcelain=v1` as the authoritative staged, unstaged, untracked, deleted, and renamed path inventory.

Stop `switch` or `commit` when there are no pending changes. Stop `pr` or `push` when there are neither pending changes nor unpushed local commits. Do not generate empty branch, commit, or publish commands.

Before reading content diffs, identify likely sensitive paths such as `.env`, credentials, and keys. Exclude them without reading their contents and ask before inspecting any such file. Read other changes only through exact path-limited commands:

```bash
git diff --cached -- <safe-paths...>
git diff -- <safe-paths...>
```

## 2. Decide the branch

Skip this section in `push` mode.

Treat `main`, `master`, and `dev` as base branches.

- On a base branch, record it as `<base>` and derive `git switch -c <type>/<kebab-case-description>` from the pending change purpose and the repository's existing branch style.
- On a non-base branch in `switch` mode, ask whether to create another branch from the current branch; stop if declined.
- On a non-base branch with pending changes in `commit` or `pr` mode, ask whether to switch first or stay on the current branch.
- On a clean non-base branch in `pr` mode, treat the run as a resume: skip committing and continue to publishing.

For a non-base `pr` run, determine `<base>` from existing local `main`, `master`, or `dev` branches. Use the only candidate, or the one with the smallest `git rev-list --count <candidate>..HEAD`.

## 3. Commit

Run this section in `commit`, `pr`, and `push` modes when pending changes exist.

1. Analyze staged, unstaged, and untracked safe paths as one change set. Identify renames, additions, deletions, intent, and files that should remain excluded.
2. Split clearly independent purposes into separate commits automatically and order them logically. Ask whether to split only when boundaries are ambiguous; keep inseparable changes together.
3. Infer a Conventional Commits type (`feat`, `fix`, `refactor`, `docs`, `chore`, `style`, `test`, `build`, or `ci`) and optional scope for each group. Keep the subject under 72 characters and write a Simplified Chinese body explaining non-trivial changes.
4. Preserve the user's working tree and respect the current index:
   - With pre-staged content and multiple groups, run `git restore --staged .` first; it changes only the index.
   - Stage each group with `git add -A -- <exact-paths...>` so deletions are recorded correctly.
   - For one group whose staged scope already matches, add only missing paths or commit directly.
   - If a one-group index contains excluded or out-of-scope paths, run `git restore --staged -- <excluded-paths...>` before staging the intended scope.
   - Before every commit, require `git diff --cached --name-only` to match that group exactly. Correct the index and stop if a sensitive, excluded, or out-of-scope path remains.

Print `[k/N]` before each group and use:

```bash
git add -A -- <exact-paths...>
git commit -m "$(cat <<'EOF'
type(scope): subject

Simplified Chinese body explaining what changed and why.
EOF
)"
```

If `git add` reports a missing path, refresh `git status --porcelain=v1`. Continue only when the intended deletion or change is already staged; otherwise stop.

## 4. Publish

### `pr`

1. Run `gh pr view --json url` without suppressing errors. Exit code 0 means a PR already exists: show its URL, push the branch, and skip creation. Continue to creation only when the CLI explicitly reports no PR; stop on authentication, network, repository, or CLI errors.
2. Review the full branch with `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat`.
3. Push with `git push -u origin <current-branch>`.
4. If no PR exists, derive a title no longer than 70 characters and create it explicitly against `<base>`:

```bash
gh pr create --base <base> --title "<title>" --body "$(cat <<'EOF'
## Summary
- <what changed and why>

## Test plan
- [ ] <concrete verification step>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Use one to three summary bullets and concrete test steps. Base the content on the complete branch range, not only the latest commit.

### `push`

Print `⚠️ push 模式：将在当前分支 <name> 上提交并直接推送，跳过 PR`. When `<name>` is `main`, `master`, or `dev`, add that it is a direct base-branch push without PR review.

- With pending changes, complete section 3 and then push.
- With a clean tree, check for unpushed commits using the configured upstream; when no upstream exists, determine whether local commits need their first push.
- If the branch is already synchronized, report `无需推送` and stop.
- Otherwise run `git push -u origin <current-branch>`.

Choosing `push` authorizes the direct current-branch commit and push, including on a base branch. Do not ask for an additional execution confirmation and never run `gh pr` in this mode.

## Execution and safety

- Default execution runs the selected state-changing commands in order. Before each, state what will happen in one sentence.
- `--dry-run` prints only the applicable `git switch`, `git restore --staged`, `git add`, `git commit`, `git push`, or `gh pr create` commands in fenced blocks and changes nothing.
- Ask only questions that define scope, such as a branch choice or ambiguous commit grouping. Invoking the skill authorizes commands inside the resolved scope.
- Shell-quote every exact path, especially paths containing spaces or leading hyphens.
- Never run `git restore <path>` without `--staged`, `git checkout --`, `git reset --hard`, `git clean`, `git rm`, force push, or automatic pull/rebase/merge recovery.
- Record user-deleted files only with `git add -A -- <path>`; never delete or resurrect working-tree files.
- On any non-zero switch, commit, push, or PR-creation result, stop. Report completed, failed, and skipped commands; never attempt history-rewriting recovery.
- If there is nothing to commit or publish for the requested mode, explain and stop without empty commands.
- End with every generated or executed command and its status.
