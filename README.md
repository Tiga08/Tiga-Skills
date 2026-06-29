# Tiga-Skills

集中式技能管理中心，通过软链接聚合来自外部仓库和自定义目录的 Agent Skills，并提供给 Claude Code 和 Codex 使用。

## 目录结构

```
Tiga-Skills/
├── .agents/skills/      # 项目级 Skills（跨 Agent 共享）
├── 01-prompts/          # 可复用的 Prompt 模板
├── 02-agent-skills/     # Agent Skills 注册表（全部为软链接）
├── 03-custom-skills/    # 用户自定义 Skills（源文件）
├── 04-scripts/          # 实用脚本
└── agent-plan/          # Agent 生成的计划文件（git-ignored）
```

- **.agents/skills/** — 项目级技能，`.claude/skills` 和 `.codex/skills` 均为指向此目录的软链接。
- **02-agent-skills/** — 所有条目均为软链接，指向外部仓库或 `03-custom-skills/` 中的技能目录。
- **03-custom-skills/** — 存放项目内自定义技能的源文件，通过相对路径软链接注册到 `02-agent-skills/`。

## 安装

运行 `setup` 命令创建用户级软链接，使 Claude Code 和 Codex 可以发现技能：

```bash
./04-scripts/manage-skills.sh setup
```

执行后将创建：
- `~/.claude/skills` → `<project>/02-agent-skills/`（整个目录作为软链接）
- `~/.codex/skills/tiga-skills` → `<project>/02-agent-skills/`（子目录下的软链接）

## 使用方法

```bash
# 从外部路径添加技能
./04-scripts/manage-skills.sh add ~/Projects/external-skills/my-skill

# 从 03-custom-skills/ 添加技能
./04-scripts/manage-skills.sh add-custom check-docs

# 移除技能
./04-scripts/manage-skills.sh remove my-skill

# 列出已注册技能
./04-scripts/manage-skills.sh list

# 更新 README 技能清单
./04-scripts/manage-skills.sh update-readme
```

## 技能清单

<!-- BEGIN SKILL LIST -->

| 名称 | 来源 | 描述 |
| ---- | ---- | ---- |
| brainstorming | superpowers | 创意工作前的需求探索与设计思考 |
| check-docs | custom | 检查治理文档（README.md、CLAUDE.md、AGENTS.md）是否与仓库实际状态一致 |
| dispatching-parallel-agents | superpowers | 并行调度多个独立任务 |
| draft-commit | custom | 分析所有待提交的 git 变更，生成可直接使用的 commit 命令（不执行） |
| executing-plans | superpowers | 在独立会话中按计划执行实施 |
| finishing-a-development-branch | superpowers | 开发分支完成后的集成决策 |
| gen-governance | custom | 分析仓库结构并生成 AGENTS.md / CLAUDE.md 治理文件 |
| md-to-zh | custom | 将英文 Markdown 文件翻译为简体中文 |
| receiving-code-review | superpowers | 收到审查反馈后的技术验证与实施 |
| requesting-code-review | superpowers | 完成任务后请求代码审查 |
| subagent-driven-development | superpowers | 在当前会话中使用子代理执行独立任务 |
| systematic-debugging | superpowers | 系统化调试，遇到 bug 时先分析再修复 |
| test-driven-development | superpowers | 测试驱动开发，先写测试再写实现 |
| using-git-worktrees | superpowers | 使用 git worktree 创建隔离工作区 |
| using-superpowers | superpowers | 会话启动时的技能发现与使用流程 |
| verification-before-completion | superpowers | 完成声明前的验证检查 |
| writing-plans | superpowers | 根据需求编写多步骤实施计划 |
| writing-skills | superpowers | 创建、编辑和验证技能 |

<!-- END SKILL LIST -->

## 技能来源

### 外部仓库

来源于 [AG-Tools/superpowers](https://github.com/Tiga08/AG-Tools)，通过 `add` 命令注册：

- **brainstorming** — 创意工作前的需求探索与设计思考
- **writing-plans** — 根据需求编写多步骤实施计划
- **executing-plans** — 在独立会话中按计划执行实施
- **subagent-driven-development** — 在当前会话中使用子代理执行独立任务
- **dispatching-parallel-agents** — 并行调度多个独立任务
- **using-git-worktrees** — 使用 git worktree 创建隔离工作区
- **test-driven-development** — 测试驱动开发，先写测试再写实现
- **systematic-debugging** — 系统化调试，遇到 bug 时先分析再修复
- **verification-before-completion** — 完成声明前的验证检查
- **requesting-code-review** — 完成任务后请求代码审查
- **receiving-code-review** — 收到审查反馈后的技术验证与实施
- **finishing-a-development-branch** — 开发分支完成后的集成决策
- **writing-skills** — 创建、编辑和验证技能
- **using-superpowers** — 会话启动时的技能发现与使用流程

### 自定义技能

位于 `03-custom-skills/` 中，通过 `add-custom` 命令注册：

- **check-docs** — 检查治理文档是否与仓库实际状态一致
- **draft-commit** — 分析所有待提交的 git 变更，生成可直接使用的 commit 命令
- **gen-governance** — 分析仓库并生成 AGENTS.md / CLAUDE.md 治理文件
- **md-to-zh** — 将英文 Markdown 文件翻译为简体中文

### 项目级技能

位于 `.agents/skills/` 中，供操作本仓库使用：

- **manage-skills** — 技能管理的自然语言接口
