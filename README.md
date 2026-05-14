# Tiga-Skills

Agent 能力库 —— 集中管理 Prompt、Agent Skills、工作流和实用脚本。

## 快速导航

| 目录 | 说明 |
|------|------|
| [00-skill-index](./00-skill-index/) | 统一能力索引 |
| [01-prompts](./01-prompts/) | 可复用的 Prompt 模板 |
| [02-agent-skills](./02-agent-skills/) | Agent Skills（SKILL.md 格式） |
| [03-workflows](./03-workflows/) | 多步骤工作流定义 |
| [04-scripts](./04-scripts/) | 实用脚本 |

## 目录结构

```text
Tiga-Skills/
├── 00-skill-index/      # 统一能力索引
├── 01-prompts/          # Prompt 模板
├── 02-agent-skills/     # Agent Skills
│   └── skills/          # 所有 Skill 统一存放
├── 03-workflows/        # 工作流
├── 04-scripts/          # 实用脚本
├── agent-plan/          # Agent 生成的计划文件
├── AGENTS.md            # Agent 行为规范
├── CLAUDE.md            # Claude Code 操作指引
└── README.md            # 本文件
```

## 使用方法

### 添加 Prompt

创建 `01-prompts/{prompt-name}.md`，写入 Prompt 内容，然后在索引中登记。

### 添加 Skill

1. 创建目录 `02-agent-skills/skills/{skill-name}/`
2. 编写 `SKILL.md`（包含 YAML frontmatter：`name`、`description`，可选 `agents`）
3. 在索引中登记

### 链接 Agent Skills

运行脚本可将 Skills 逐个链接到本机智能体配置目录：

```bash
./04-scripts/link-skills.sh              # 链接到所有 agent
./04-scripts/link-skills.sh --codex      # 仅链接到 ~/.codex/skills
./04-scripts/link-skills.sh --unlink     # 移除 symlink
./04-scripts/link-skills.sh --skill foo  # 仅处理指定 skill
```

每个 Skill 单独创建 symlink，不影响目标目录已有内容。

### 添加工作流

创建 `03-workflows/{workflow-name}.md`，定义步骤和触发条件，然后在索引中登记。

### 添加脚本

将脚本放入 `04-scripts/`，确保包含用途说明的注释头，然后在索引中登记。
