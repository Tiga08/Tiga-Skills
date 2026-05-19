# CLAUDE.md — Tiga-Skills

## 仓库概览

Tiga-Skills 是一个 **Agent 能力库**，将 Prompt、Agent Skill、工作流和实用脚本组织为结构化、可发现的集合。

## 目录结构

```
Tiga-Skills/
├── 00-skill-index/      # 统一能力索引
├── 01-prompts/          # 可复用的 Prompt 模板
├── 02-agent-skills/     # Agent Skills（SKILL.md 格式）
│   └── skills/          # 所有 Skill 统一存放
├── 03-workflows/        # 多步骤工作流定义
├── 04-scripts/          # 实用脚本
├── 05-custom-skills/    # 用户自定义 Skills
│   └── skills/          # 自定义 Skill 存放目录
├── agent-plan/          # Agent 生成的计划文件
├── AGENTS.md            # Agent 行为规范
├── CLAUDE.md            # 本文件
└── README.md            # 项目概览（中文）
```

## 规范

- **文件名**：kebab-case（如 `my-awesome-skill`）
- **编码**：UTF-8
- **内容语言**：面向用户的文档使用简体中文；配置文件（`CLAUDE.md`、`AGENTS.md`、YAML frontmatter）使用英文
- **Markdown**：遵循 CommonMark 规范

## Skill 格式

每个 Skill 存放在 `02-agent-skills/skills/{skill-name}/SKILL.md` 或 `05-custom-skills/skills/{skill-name}/SKILL.md`，包含 YAML frontmatter：

```yaml
---
name: skill-name
description: One-line description of what the skill does
agents:        # 可选：链接到哪些 agent（默认：全部）
  - codex
  - agents
---
```

后跟 Markdown 格式的 Skill 正文。

## 添加内容

1. **Prompt** — 创建 `01-prompts/{prompt-name}.md`
2. **Skill** — 创建 `02-agent-skills/skills/{skill-name}/SKILL.md`
3. **自定义 Skill** — 创建 `05-custom-skills/skills/{skill-name}/SKILL.md`
4. **工作流** — 创建 `03-workflows/{workflow-name}.md`
5. **脚本** — 添加到 `04-scripts/`，包含简要注释头
6. **更新索引** — 在 `00-skill-index/README.md` 中添加条目

## 链接 Agent Skills

使用 `04-scripts/link-skills.sh` 将各个 Skill 逐一链接到本机 agent 配置目录：

```bash
./04-scripts/link-skills.sh              # 链接到所有 agent
./04-scripts/link-skills.sh --codex      # 仅链接到 ~/.codex/skills
./04-scripts/link-skills.sh --unlink     # 移除 symlink
./04-scripts/link-skills.sh --skill foo  # 仅处理指定 skill
```

脚本会同时扫描 `02-agent-skills/skills/` 和 `05-custom-skills/skills/`。每个 Skill 单独创建 symlink，不影响目标目录中的已有内容。

## 导入外部 Skills

使用 `04-scripts/manage-skills.sh` 从外部仓库（如 `khazix-skills`）导入 Skill：

```bash
./04-scripts/manage-skills.sh import <source-path>
./04-scripts/manage-skills.sh remove <skill-name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh status
./04-scripts/manage-skills.sh update <skill-name>
```

已导入的 Skill 记录在 `02-agent-skills/skill-registry.json` 中。

## 质量标准

- 每个 Skill 必须在 frontmatter 中包含 `name` 和 `description`。
- 描述应简洁（一行）且具有可操作性。
- Prompt 和工作流应在适当时包含使用示例。
- 脚本必须可执行并包含错误处理。
