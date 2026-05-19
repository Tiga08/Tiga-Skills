# 自定义 Skills

存放用户自定义的 Skill，与 `02-agent-skills` 中的标准/外部导入 Skill 隔离，便于独立维护。

## 与 `02-agent-skills` 的区别

| | `02-agent-skills` | `05-custom-skills` |
|---|---|---|
| 定位 | 标准 Skill 和外部导入 Skill | 用户自定义 Skill |
| 管理方式 | `manage-skills.sh` 管理外部导入 | 手动创建和维护 |
| 版本跟踪 | 导入记录在 `skill-registry.json` | 无需 registry |

## 目录结构

```text
05-custom-skills/
├── README.md          # 本文件
└── skills/            # 自定义 Skill 存放目录
    └── {skill-name}/  # 每个 Skill 一个目录
        └── SKILL.md   # Skill 定义文件
```

## SKILL.md 格式

与标准 Skill 格式一致，包含 YAML frontmatter：

```yaml
---
name: skill-name
description: One-line description of what the skill does
agents:        # 可选：链接到哪些 agent（默认：全部）
  - claude
  - codex
  - agents
---
```

后跟 Markdown 格式的 Skill 正文。

## 链接方式

`link-skills.sh` 会自动扫描 `05-custom-skills/skills/` 目录，无需额外配置：

```bash
./04-scripts/link-skills.sh              # 链接所有 Skill（含自定义）
./04-scripts/link-skills.sh --skill foo  # 链接指定 Skill（自动在两个目录中查找）
```

## 登记

添加新的自定义 Skill 后，请在 [00-skill-index](../00-skill-index/README.md) 的"自定义 Skills"章节中登记。
