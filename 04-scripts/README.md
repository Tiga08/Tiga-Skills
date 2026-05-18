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
| `link-skills.sh` | 将 Skills 逐个链接到本机 agent 配置目录 |
| `manage-skills.sh` | 管理外部 Skill 的导入、移除、查询和更新 |

### link-skills.sh

```bash
./04-scripts/link-skills.sh              # 链接到所有 agent
./04-scripts/link-skills.sh --claude     # 链接到 ~/.claude/skills
./04-scripts/link-skills.sh --codex      # 链接到 ~/.codex/skills
./04-scripts/link-skills.sh --agents     # 链接到 ~/.agents/skills
./04-scripts/link-skills.sh --unlink     # 移除 symlink
./04-scripts/link-skills.sh --skill foo  # 仅处理指定 skill
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
```

`remove` 仅可移除 registry 中登记的外部 Skill，不会误删本仓库原生 Skill。

## 登记

添加新脚本后，请在 [00-skill-index](../00-skill-index/README.md) 中登记。
