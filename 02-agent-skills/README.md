# Agent Skills

存放 Agent 能力定义。所有 Skill 统一存放在 `skills/` 目录下，每个 Skill 是一个独立目录，包含 `SKILL.md` 文件。

## 用途

- 定义 Agent 可调用的结构化能力
- 统一管理所有智能体共享的 Skill
- 提供标准化的 Skill 描述和触发规则

## 目录结构

```text
02-agent-skills/
├── skills/
│   └── {skill-name}/
│       └── SKILL.md
├── skill-registry.json
└── README.md
```

## 本机链接

使用脚本将仓库中的 Skill 逐个链接到本机智能体配置目录：

```bash
./04-scripts/link-skills.sh              # 链接到所有 agent
./04-scripts/link-skills.sh --codex      # 仅链接到 ~/.codex/skills
./04-scripts/link-skills.sh --unlink     # 移除所有 symlink
./04-scripts/link-skills.sh --skill foo  # 仅处理指定 skill
```

每个 Skill 会被单独创建 symlink，不会影响目标目录中的已有内容（如 `~/.codex/skills/.system/`）。

## SKILL.md 格式

```markdown
---
name: skill-name
description: 一行说明这个 Skill 的功能
agents:        # 可选，控制链接到哪些 agent
  - codex
  - agents
---

Skill 的详细内容（Markdown 格式）
```

### Frontmatter 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | Skill 名称，kebab-case |
| `description` | 是 | 一行功能描述，用于触发匹配 |
| `agents` | 否 | 链接目标列表（`claude`/`codex`/`agents`），缺省时链接到所有 agent |

## 编写建议

编写 `description` 时应确保：

- 简洁准确，便于语义匹配
- 包含关键触发词
- 说明适用场景

## 外部 Skill 管理

使用 `manage-skills.sh` 可以从外部仓库导入或移除 Skill。导入记录保存在 `skill-registry.json` 中。

```bash
# 导入：从外部路径复制 Skill 到 skills/ 目录
../04-scripts/manage-skills.sh import /path/to/external/my-skill

# 移除：仅可移除 registry 中登记的外部 Skill
../04-scripts/manage-skills.sh remove my-skill

# 查看/检查
../04-scripts/manage-skills.sh list
../04-scripts/manage-skills.sh status
```

导入后的 Skill 与原生 Skill 共存于 `skills/` 目录，`link-skills.sh` 会一并链接到本机。

## 登记

添加新 Skill 后，请在 [00-skill-index](../00-skill-index/README.md) 中登记。
