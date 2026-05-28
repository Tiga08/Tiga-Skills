---
name: sync-upstream
description: Sync imported skills from upstream GitHub repositories — check for updates, pull changes, and refresh local copies
---

Interactively sync imported skills from their upstream GitHub repositories.

## Workflow

1. **Check status first** — run `./04-scripts/sync-upstream.sh status` and present the results to the user.
2. **Confirm before syncing** — if any repos have pending upstream commits or changed skill hashes, ask the user whether to proceed with sync.
3. **Sync** — run `./04-scripts/sync-upstream.sh sync` (or `sync --repo <id>` if the user specified a particular repo).
4. **Rebuild symlinks** — run `./04-scripts/link-skills.sh` to update local agent symlinks.
5. **Report** — summarize what was updated and remind the user to commit changes in the Tiga-Skills repo.

## Commands Reference

```bash
# 查看所有已注册仓库
./04-scripts/sync-upstream.sh list-repos

# 检查同步状态
./04-scripts/sync-upstream.sh status
./04-scripts/sync-upstream.sh status --repo <repo-id>

# 执行同步
./04-scripts/sync-upstream.sh sync [--repo <id>] [--dry-run] [--force]

# 注册新仓库
./04-scripts/sync-upstream.sh add-repo <local-path> [--id <name>] [--branch <branch>]

# 移除仓库注册
./04-scripts/sync-upstream.sh remove-repo <repo-id>
```

## Notes

- The sync uses `--ff-only` merge. If local branches have diverged from upstream, it will fail. Use `--force` to reset (destructive), or resolve manually.
- `--dry-run` shows what would happen without making changes.
- After syncing, the user should review and commit changes in the Tiga-Skills repo.
