# 脚本

存放实用脚本，用于自动化操作、数据处理等辅助任务。

## 用途

- 提供可直接执行的自动化脚本
- 辅助 Skill 和工作流的运行
- 处理重复性操作任务

## 文件规范

- 文件名：kebab-case，如 `sync-index.sh`
- 编码：UTF-8
- 每个脚本文件顶部需包含注释头，说明用途和用法
- 确保脚本可执行（`chmod +x`）

## 注释头格式

```bash
#!/usr/bin/env bash
# 用途：简要说明
# 用法：script-name.sh [参数]
```

## 已有脚本

| 脚本 | 说明 |
|------|------|
| `link-skills.sh` | 将 Skills 逐个链接到本机 agent 配置目录（扫描 `02-agent-skills/skills/` 和 `05-custom-skills/skills/`） |
| `manage-skills.sh` | 管理外部 Skill 的导入、移除、查询和更新 |
| `sync-index.sh` | 同步自定义 Skills 到能力索引 |
| `sync-upstream.sh` | 从上游 GitHub 仓库同步已导入的 Skills |

### link-skills.sh

```bash
./04-scripts/link-skills.sh              # 链接到所有 agent（默认 --all）
./04-scripts/link-skills.sh --claude     # 链接到 ~/.claude/skills
./04-scripts/link-skills.sh --codex      # 链接到 ~/.codex/skills
./04-scripts/link-skills.sh --agents     # 链接到 ~/.agents/skills
./04-scripts/link-skills.sh --skill foo  # 仅处理指定 skill
./04-scripts/link-skills.sh --claude --codex --skill foo  # 仅链接指定 skill 到指定 agent
./04-scripts/link-skills.sh --unlink                      # 移除所有 skill 的 symlink
./04-scripts/link-skills.sh --unlink --skill foo          # 仅移除指定 skill 的 symlink
```

每个 Skill 单独创建 symlink，不影响目标目录已有内容（如 `~/.codex/skills/.system/`）。

### manage-skills.sh

从外部仓库（如 `khazix-skills`）导入 Skill 到本项目，或移除已导入的 Skill。导入记录保存在 `02-agent-skills/skill-registry.json` 中。可通过 `--description` 参数为导入或更新的 Skill 指定自定义说明，覆盖 SKILL.md 中的 description 字段。

```bash
./04-scripts/manage-skills.sh import [--description "说明"] <source-path>  # 导入外部 Skill
./04-scripts/manage-skills.sh remove <skill-name>                         # 移除已导入的 Skill
./04-scripts/manage-skills.sh list                                        # 列出已导入的 Skill
./04-scripts/manage-skills.sh status                                      # 检查上游是否有更新
./04-scripts/manage-skills.sh update [--description "说明"] <skill-name>   # 从来源重新导入
./04-scripts/manage-skills.sh update --description "新说明" my-skill       # 仅更新说明
```

`remove` 仅可移除 registry 中登记的外部 Skill，不会误删本仓库原生 Skill。

### sync-index.sh

扫描 `05-custom-skills/skills/` 目录，自动更新 `00-skill-index/README.md` 中的"自定义 Skills"章节。

```bash
./04-scripts/sync-index.sh              # 同步索引
./04-scripts/sync-index.sh --dry-run    # 仅预览，不修改文件
```

### sync-upstream.sh

从上游 GitHub 仓库拉取更新，并同步到 `02-agent-skills/skills/` 下的已导入 Skill。需先将上游仓库注册到 `skill-registry.json` 中。

```bash
# 注册上游仓库
./04-scripts/sync-upstream.sh add-repo /path/to/local-clone
./04-scripts/sync-upstream.sh add-repo /path/to/repo --id my-repo --branch main --skills-path skills

# 列出已注册仓库
./04-scripts/sync-upstream.sh list-repos

# 检查同步状态（会执行 git fetch）
./04-scripts/sync-upstream.sh status
./04-scripts/sync-upstream.sh status --repo baoyu-skills

# 执行同步
./04-scripts/sync-upstream.sh sync                      # 同步所有仓库
./04-scripts/sync-upstream.sh sync --repo baoyu-skills  # 仅同步指定仓库
./04-scripts/sync-upstream.sh sync --dry-run            # 预览变更，不实际修改
./04-scripts/sync-upstream.sh sync --force              # 分叉时强制重置到上游

# 移除仓库注册
./04-scripts/sync-upstream.sh remove-repo my-repo
```

`add-repo` 会自动从 git remote 读取 upstream/origin URL，自动检测 `skillsPath`（`skills` 或 `.`），并回填已有 skill 的 `repoId`。

## 常见操作

### 完整移除一个已导入的 Skill

1. 取消 symlink：`./04-scripts/link-skills.sh --unlink --skill <skill-name>`
2. 从 registry 移除并删除文件：`./04-scripts/manage-skills.sh remove <skill-name>`
3. 从 `00-skill-index/README.md` 中删除对应条目（`manage-skills.sh remove` 会自动处理）

### 仅对某个 agent 取消链接

```bash
./04-scripts/link-skills.sh --unlink --claude --skill <skill-name>
```

## 登记

添加新脚本后，请在 [00-skill-index](../00-skill-index/README.md) 中登记。
