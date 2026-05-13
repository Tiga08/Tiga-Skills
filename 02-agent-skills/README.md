# Agent Skills

存放 Agent 能力定义，每个 Skill 是一个独立目录，包含 `SKILL.md` 文件。

## 用途

- 定义 Agent 可调用的结构化能力
- 与 Claude Code 插件系统兼容
- 提供标准化的 Skill 描述和触发规则

## 目录结构

每个 Skill 一个目录：

```
02-agent-skills/
└── {skill-name}/
    └── SKILL.md
```

## SKILL.md 格式

```markdown
---
name: skill-name
description: 一行说明这个 Skill 的功能
---

Skill 的详细内容（Markdown 格式）
```

### Frontmatter 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | Skill 名称，kebab-case |
| `description` | 是 | 一行功能描述，用于触发匹配 |

## 与 Claude Code 插件系统的关系

Claude Code 的插件系统会扫描 `SKILL.md` 文件，根据 `description` 字段匹配用户意图并自动调用对应 Skill。编写 `description` 时应确保：

- 简洁准确，便于语义匹配
- 包含关键触发词
- 说明适用场景

## 登记

添加新 Skill 后，请在 [00-skill-index](../00-skill-index/README.md) 中登记。
