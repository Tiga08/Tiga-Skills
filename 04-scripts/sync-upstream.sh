#!/usr/bin/env bash
# 用途：从上游 GitHub 仓库同步已导入的 Skills
# 用法：sync-upstream.sh <add-repo|remove-repo|list-repos|status|sync> [参数]

set -euo pipefail

# --- 颜色 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- 路径 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REGISTRY="$REPO_ROOT/02-agent-skills/skill-registry.json"
MANAGE_SKILLS="$SCRIPT_DIR/manage-skills.sh"

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [options]

Commands:
  add-repo <local-path> [--id <name>] [--branch <branch>] [--skills-path <path>]
                         注册一个上游仓库
  remove-repo <repo-id>  移除一个已注册的仓库
  list-repos             列出所有已注册的仓库
  status [--repo <id>]   检查上游仓库的同步状态
  sync [--repo <id>] [--dry-run] [--force]
                         从上游拉取更新并同步已导入的 Skills

Examples:
  $(basename "$0") add-repo /Users/bruce/Projects/AG-Tools/baoyu-skills
  $(basename "$0") add-repo /path/to/repo --id my-repo --branch main --skills-path skills
  $(basename "$0") status
  $(basename "$0") sync --dry-run
  $(basename "$0") sync --repo baoyu-skills
EOF
}

ensure_registry() {
  if [ ! -f "$REGISTRY" ]; then
    printf '{\n  "version": 2,\n  "repos": {},\n  "skills": []\n}\n' > "$REGISTRY"
  fi
}

# --- add-repo ---
cmd_add_repo() {
  local local_path=""
  local repo_id=""
  local branch=""
  local skills_path=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --id)
        repo_id="${2:-}"
        shift 2
        ;;
      --branch)
        branch="${2:-}"
        shift 2
        ;;
      --skills-path)
        skills_path="${2:-}"
        shift 2
        ;;
      *)
        local_path="$1"
        shift
        ;;
    esac
  done

  if [ -z "$local_path" ]; then
    echo -e "${RED}Error: local path is required${NC}" >&2
    echo "Usage: $(basename "$0") add-repo <local-path> [--id <name>] [--branch <branch>] [--skills-path <path>]" >&2
    exit 1
  fi

  # 解析为绝对路径
  local_path="$(cd "$local_path" 2>/dev/null && pwd)" || {
    echo -e "${RED}Error: path does not exist: $local_path${NC}" >&2
    exit 1
  }

  # 检查是否是 git 仓库
  local git_root
  git_root="$(git -C "$local_path" rev-parse --show-toplevel 2>/dev/null)" || {
    echo -e "${RED}Error: not a git repository: $local_path${NC}" >&2
    exit 1
  }
  local_path="$git_root"

  # 获取 remote URL
  local upstream_url origin_url
  upstream_url="$(git -C "$local_path" config --get remote.upstream.url 2>/dev/null || true)"
  origin_url="$(git -C "$local_path" config --get remote.origin.url 2>/dev/null || true)"

  if [ -z "$upstream_url" ]; then
    echo -e "${RED}Error: no 'upstream' remote configured in $local_path${NC}" >&2
    echo "Run: git -C '$local_path' remote add upstream <url>" >&2
    exit 1
  fi

  # 默认 repo_id = 目录 basename
  if [ -z "$repo_id" ]; then
    repo_id="$(basename "$local_path")"
  fi

  # 默认 branch = upstream 的默认分支，回退到本地当前分支
  if [ -z "$branch" ]; then
    branch="$(git -C "$local_path" remote show upstream 2>/dev/null \
      | grep 'HEAD branch' | awk '{print $NF}' || true)"
    if [ -z "$branch" ]; then
      branch="$(git -C "$local_path" branch --show-current 2>/dev/null || echo "main")"
    fi
  fi

  # 自动检测 skills_path
  if [ -z "$skills_path" ]; then
    if compgen -G "$local_path/skills/*/SKILL.md" > /dev/null 2>&1; then
      skills_path="skills"
    elif compgen -G "$local_path/*/SKILL.md" > /dev/null 2>&1; then
      skills_path="."
    else
      echo -e "${YELLOW}Warning: no SKILL.md files found, defaulting skills_path to '.'${NC}"
      skills_path="."
    fi
  fi

  ensure_registry

  # 写入 registry 并回填已有 skill 的 repoId
  python3 -c "
import json, sys

registry_path = sys.argv[1]
repo_id = sys.argv[2]
local_path = sys.argv[3]
upstream_url = sys.argv[4]
origin_url = sys.argv[5]
branch = sys.argv[6]
skills_path = sys.argv[7]

with open(registry_path) as f:
    data = json.load(f)

if 'repos' not in data:
    data['repos'] = {}

if repo_id in data['repos']:
    print(f'Warning: repo \"{repo_id}\" already registered, updating...', file=sys.stderr)

data['repos'][repo_id] = {
    'localPath': local_path,
    'upstreamUrl': upstream_url,
    'originUrl': origin_url,
    'branch': branch,
    'skillsPath': skills_path,
    'lastSyncedAt': None,
    'lastSyncedCommit': None
}

# 回填已有 skill 的 repoId
backfilled = 0
for skill in data.get('skills', []):
    if skill['source'].startswith(local_path + '/'):
        if 'repoId' not in skill or skill['repoId'] != repo_id:
            skill['repoId'] = repo_id
            backfilled += 1

with open(registry_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')

if backfilled > 0:
    print(f'Backfilled repoId for {backfilled} existing skill(s)')
" "$REGISTRY" "$repo_id" "$local_path" "$upstream_url" "$origin_url" "$branch" "$skills_path"

  echo -e "${GREEN}Registered repo: ${BOLD}$repo_id${NC}"
  echo -e "  Local path:   $local_path"
  echo -e "  Upstream:     $upstream_url"
  echo -e "  Origin:       ${origin_url:-（none）}"
  echo -e "  Branch:       $branch"
  echo -e "  Skills path:  $skills_path"
}

# --- remove-repo ---
cmd_remove_repo() {
  local repo_id="${1:-}"

  if [ -z "$repo_id" ]; then
    echo -e "${RED}Error: repo id is required${NC}" >&2
    echo "Usage: $(basename "$0") remove-repo <repo-id>" >&2
    exit 1
  fi

  ensure_registry

  python3 -c "
import json, sys

registry_path = sys.argv[1]
repo_id = sys.argv[2]

with open(registry_path) as f:
    data = json.load(f)

repos = data.get('repos', {})
if repo_id not in repos:
    print(f'Error: repo \"{repo_id}\" not found in registry', file=sys.stderr)
    sys.exit(1)

del repos[repo_id]

# 清除 skill 中的 repoId 引用
for skill in data.get('skills', []):
    if skill.get('repoId') == repo_id:
        del skill['repoId']

with open(registry_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" "$REGISTRY" "$repo_id"

  echo -e "${GREEN}Removed repo: $repo_id${NC}"
}

# --- list-repos ---
cmd_list_repos() {
  ensure_registry

  python3 -c "
import json, sys

with open(sys.argv[1]) as f:
    data = json.load(f)

repos = data.get('repos', {})
if not repos:
    print('No registered repos.')
    sys.exit(0)

skills = data.get('skills', [])

for repo_id, info in repos.items():
    skill_count = sum(1 for s in skills if s.get('repoId') == repo_id)
    synced = info.get('lastSyncedAt') or 'never'
    print(f'  \033[1m{repo_id}\033[0m')
    print(f'    Local:      {info[\"localPath\"]}')
    print(f'    Upstream:   {info[\"upstreamUrl\"]}')
    print(f'    Branch:     {info[\"branch\"]}')
    print(f'    Skills:     {info[\"skillsPath\"]}/ ({skill_count} imported)')
    print(f'    Last sync:  {synced}')
    print()
" "$REGISTRY"
}

# --- status ---
cmd_status() {
  local target_repo=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --repo)
        target_repo="${2:-}"
        shift 2
        ;;
      *)
        echo -e "${RED}Error: unknown option: $1${NC}" >&2
        exit 1
        ;;
    esac
  done

  ensure_registry

  python3 -c "
import json, subprocess, os, sys

registry_path = sys.argv[1]
target_repo = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None

with open(registry_path) as f:
    data = json.load(f)

repos = data.get('repos', {})
skills = data.get('skills', [])

if not repos:
    print('No registered repos.')
    sys.exit(0)

for repo_id, info in repos.items():
    if target_repo and repo_id != target_repo:
        continue

    local_path = info['localPath']
    branch = info['branch']
    upstream_url = info['upstreamUrl']

    print(f'\033[1m{repo_id}\033[0m ({upstream_url})')

    # 检查本地路径是否存在
    if not os.path.isdir(local_path):
        print(f'  \033[0;31m✗ Local path missing: {local_path}\033[0m')
        print()
        continue

    # git fetch upstream
    result = subprocess.run(
        ['git', '-C', local_path, 'fetch', 'upstream', branch],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'  \033[0;31m✗ Failed to fetch upstream: {result.stderr.strip()}\033[0m')
        print()
        continue

    # 检查当前分支
    current_branch = subprocess.run(
        ['git', '-C', local_path, 'branch', '--show-current'],
        capture_output=True, text=True
    ).stdout.strip()

    if current_branch != branch:
        print(f'  \033[0;33m⚠ On branch \"{current_branch}\", expected \"{branch}\"\033[0m')

    # 计算落后的 commit 数
    result = subprocess.run(
        ['git', '-C', local_path, 'rev-list', '--count', f'HEAD..upstream/{branch}'],
        capture_output=True, text=True
    )
    behind = int(result.stdout.strip()) if result.returncode == 0 else -1

    # 检查是否有分叉
    result_ahead = subprocess.run(
        ['git', '-C', local_path, 'rev-list', '--count', f'upstream/{branch}..HEAD'],
        capture_output=True, text=True
    )
    ahead = int(result_ahead.stdout.strip()) if result_ahead.returncode == 0 else 0

    if behind == 0:
        print(f'  \033[0;32m✓ Up-to-date with upstream/{branch}\033[0m')
    elif ahead > 0:
        print(f'  \033[0;33m⚠ Diverged: {ahead} ahead, {behind} behind upstream/{branch}\033[0m')
        print(f'    --ff-only merge will fail. Resolve manually or use --force')
    else:
        print(f'  \033[0;33m↓ {behind} commit(s) behind upstream/{branch}\033[0m')

    # 检查此仓库下已导入 skill 的状态
    repo_skills = [s for s in skills if s.get('repoId') == repo_id]
    if repo_skills:
        print(f'  Imported skills:')
        for s in repo_skills:
            source = s['source']
            old_hash = s.get('sourceHash', '')
            name = s['name']

            if not os.path.isdir(source):
                print(f'    \033[0;31m✗ {name}: source missing\033[0m')
                continue

            result = subprocess.run(
                ['bash', '-c', f\"find '{source}' -type f | sort | xargs shasum 2>/dev/null | shasum\"],
                capture_output=True, text=True
            )
            new_hash = result.stdout.strip()[:8] if result.returncode == 0 else '?'

            if new_hash == old_hash:
                print(f'    \033[0;32m✓ {name}: up-to-date\033[0m')
            else:
                print(f'    \033[0;33m↻ {name}: source changed ({old_hash} → {new_hash})\033[0m')
    else:
        print(f'  (no skills imported from this repo)')

    print()

if target_repo and target_repo not in repos:
    print(f'\033[0;31mError: repo \"{target_repo}\" not found\033[0m')
    sys.exit(1)
" "$REGISTRY" "${target_repo:-}"
}

# --- sync ---
cmd_sync() {
  local target_repo=""
  local dry_run=false
  local force=false

  while [ $# -gt 0 ]; do
    case "$1" in
      --repo)
        target_repo="${2:-}"
        shift 2
        ;;
      --dry-run)
        dry_run=true
        shift
        ;;
      --force)
        force=true
        shift
        ;;
      *)
        echo -e "${RED}Error: unknown option: $1${NC}" >&2
        exit 1
        ;;
    esac
  done

  ensure_registry

  python3 -c "
import json, subprocess, os, sys, datetime

registry_path = sys.argv[1]
target_repo = sys.argv[2] if sys.argv[2] else None
dry_run = sys.argv[3] == 'true'
force = sys.argv[4] == 'true'
manage_skills = sys.argv[5]

with open(registry_path) as f:
    data = json.load(f)

repos = data.get('repos', {})
skills = data.get('skills', [])

if not repos:
    print('No registered repos.')
    sys.exit(0)

if target_repo and target_repo not in repos:
    print(f'\033[0;31mError: repo \"{target_repo}\" not found\033[0m')
    sys.exit(1)

total_updated = 0
total_skipped = 0
total_failed = 0

for repo_id, info in repos.items():
    if target_repo and repo_id != target_repo:
        continue

    local_path = info['localPath']
    branch = info['branch']

    print(f'\033[1m=== {repo_id} ===\033[0m')

    # 检查本地路径
    if not os.path.isdir(local_path):
        print(f'  \033[0;31m✗ Local path missing: {local_path}\033[0m')
        total_failed += 1
        print()
        continue

    # fetch upstream
    print(f'  Fetching upstream/{branch}...')
    result = subprocess.run(
        ['git', '-C', local_path, 'fetch', 'upstream', branch],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'  \033[0;31m✗ Fetch failed: {result.stderr.strip()}\033[0m')
        total_failed += 1
        print()
        continue

    # 检查落后数
    result = subprocess.run(
        ['git', '-C', local_path, 'rev-list', '--count', f'HEAD..upstream/{branch}'],
        capture_output=True, text=True
    )
    behind = int(result.stdout.strip()) if result.returncode == 0 else 0

    if behind == 0:
        print(f'  \033[0;32m✓ Already up-to-date\033[0m')
    else:
        print(f'  {behind} new commit(s) from upstream')

        if dry_run:
            print(f'  \033[0;36m[dry-run] Would merge upstream/{branch}\033[0m')
        else:
            # 确保在正确的分支上
            current_branch = subprocess.run(
                ['git', '-C', local_path, 'branch', '--show-current'],
                capture_output=True, text=True
            ).stdout.strip()

            if current_branch != branch:
                print(f'  Switching to branch {branch}...')
                r = subprocess.run(
                    ['git', '-C', local_path, 'checkout', branch],
                    capture_output=True, text=True
                )
                if r.returncode != 0:
                    print(f'  \033[0;31m✗ Checkout failed: {r.stderr.strip()}\033[0m')
                    total_failed += 1
                    print()
                    continue

            # 尝试 --ff-only merge
            r = subprocess.run(
                ['git', '-C', local_path, 'merge', f'upstream/{branch}', '--ff-only'],
                capture_output=True, text=True
            )
            if r.returncode != 0:
                if force:
                    print(f'  \033[0;33m⚠ Fast-forward failed, --force specified\033[0m')
                    print(f'  \033[0;33m⚠ This will reset {branch} to upstream/{branch}, discarding local commits\033[0m')

                    # 非交互环境下直接执行 reset
                    r2 = subprocess.run(
                        ['git', '-C', local_path, 'reset', '--hard', f'upstream/{branch}'],
                        capture_output=True, text=True
                    )
                    if r2.returncode != 0:
                        print(f'  \033[0;31m✗ Reset failed: {r2.stderr.strip()}\033[0m')
                        total_failed += 1
                        print()
                        continue
                    print(f'  \033[0;32m✓ Reset to upstream/{branch}\033[0m')
                else:
                    print(f'  \033[0;31m✗ Fast-forward merge failed (branches have diverged)\033[0m')
                    print(f'    Resolve manually or use --force to reset')
                    total_failed += 1
                    print()
                    continue
            else:
                print(f'  \033[0;32m✓ Merged {behind} commit(s)\033[0m')

    # 检查并更新已导入的 skill
    repo_skills = [s for s in skills if s.get('repoId') == repo_id]
    if repo_skills:
        for s in repo_skills:
            source = s['source']
            old_hash = s.get('sourceHash', '')
            name = s['name']

            if not os.path.isdir(source):
                print(f'  \033[0;31m✗ {name}: source directory missing\033[0m')
                total_failed += 1
                continue

            result = subprocess.run(
                ['bash', '-c', f\"find '{source}' -type f | sort | xargs shasum 2>/dev/null | shasum\"],
                capture_output=True, text=True
            )
            new_hash = result.stdout.strip()[:8] if result.returncode == 0 else '?'

            if new_hash == old_hash:
                print(f'  \033[0;32m✓ {name}: no changes\033[0m')
                total_skipped += 1
            else:
                if dry_run:
                    print(f'  \033[0;36m[dry-run] Would update {name} ({old_hash} → {new_hash})\033[0m')
                    total_updated += 1
                else:
                    print(f'  Updating {name}...')
                    r = subprocess.run(
                        [manage_skills, 'update', name],
                        capture_output=True, text=True
                    )
                    if r.returncode == 0:
                        print(f'  \033[0;32m✓ {name}: updated\033[0m')
                        total_updated += 1
                    else:
                        print(f'  \033[0;31m✗ {name}: update failed\033[0m')
                        if r.stderr.strip():
                            print(f'    {r.stderr.strip()}')
                        total_failed += 1

    # 更新 lastSyncedAt 和 lastSyncedCommit（非 dry-run）
    if not dry_run:
        commit = subprocess.run(
            ['git', '-C', local_path, 'rev-parse', '--short', f'upstream/{branch}'],
            capture_output=True, text=True
        ).stdout.strip()

        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')

        # 重新读取 registry（可能被 manage-skills.sh update 修改过）
        with open(registry_path) as f:
            data = json.load(f)
        data['repos'][repo_id]['lastSyncedAt'] = now
        data['repos'][repo_id]['lastSyncedCommit'] = commit
        with open(registry_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')

    print()

# 摘要
print(f'\033[1m--- Summary ---\033[0m')
prefix = '[dry-run] ' if dry_run else ''
print(f'  {prefix}Updated: {total_updated}, Skipped: {total_skipped}, Failed: {total_failed}')
" "$REGISTRY" "${target_repo:-}" "$dry_run" "$force" "$MANAGE_SKILLS"
}

# --- 主入口 ---
if [ "$#" -eq 0 ]; then
  usage
  exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
  add-repo)    cmd_add_repo "$@" ;;
  remove-repo) cmd_remove_repo "$@" ;;
  list-repos)  cmd_list_repos "$@" ;;
  status)      cmd_status "$@" ;;
  sync)        cmd_sync "$@" ;;
  --help|-h)   usage ;;
  *)
    echo -e "${RED}Error: unknown command: $COMMAND${NC}" >&2
    usage >&2
    exit 1
    ;;
esac
