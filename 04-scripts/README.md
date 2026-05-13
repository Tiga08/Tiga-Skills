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
| `link-skills.sh` | 将 `02-agent-skills` 软链接到 `~/.claude/skills` 和 `~/.codex/skills` |

## 登记

添加新脚本后，请在 [00-skill-index](../00-skill-index/README.md) 中登记。
