# Tiga-Skills

集中式技能管理中心，通过软链接聚合来自外部仓库和自定义目录的 Agent Skills，并提供给 Claude Code 和 Codex 使用。

## 目录结构

```
Tiga-Skills/
├── .agents/skills/      # 项目级 Skills（跨 Agent 共享）
├── .claude/             # Claude Code 项目配置
├── .codex/              # Codex 项目配置
├── 01-prompts/          # 可复用的 Prompt 模板
├── 02-agent-skills/     # Agent Skills 注册表（扁平存放技能软链接，分组仅体现在下方技能清单文档中）
├── 03-custom-skills/    # 用户自定义 Skills（源文件）
├── 04-scripts/          # 实用脚本
├── agent-plan/          # Agent 生成的计划文件（git-ignored）
└── Todo/                # 本地待办和工作笔记（git-ignored）
```

- **.agents/skills/** — 项目级技能，`.claude/skills` 和 `.codex/skills` 均为指向此目录的软链接。
- **.claude/** / **.codex/** — Agent 项目配置目录，`skills` 均指向 `.agents/skills/`。
- **02-agent-skills/** — 技能注册表，技能条目以软链接形式直接扁平存放在该目录下，来源分组仅体现在 README 技能清单中。
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

### 项目级技能

位于 `.agents/skills/`，供操作本仓库使用

| 名称 | 描述 |
| ---- | ---- |
| manage-global-skills | 管理全局 agent 技能注册表 — 在 Tiga-Skills 中添加、移除、列出技能，并按来源分组配置软链接 |

### custom-skills

来源于 `03-custom-skills/`，通过 `add-custom` 命令注册

| 名称 | 描述 |
| ---- | ---- |
| check-docs | 检查治理文档（README.md、CLAUDE.md、AGENTS.md）是否与仓库实际状态一致 |
| gen-governance | 分析仓库结构并生成 AGENTS.md / CLAUDE.md 治理文件 |
| manage-local-skills | 管理项目级 agent 技能 — 在当前项目的 .agents/skills/ 中初始化、导入、移除和列出技能 |
| md-to-zh | 将英文 Markdown 文件翻译为简体中文 |
| switch-commit-pr | 根据待提交的改动分阶段生成 git 分支切换 / commit / PR 命令，支持直接同步执行 |

### superpowers

来源于 [AG-Tools/superpowers](https://github.com/Tiga08/AG-Tools)

| 名称 | 描述 |
| ---- | ---- |
| brainstorming | 在任何创意工作前使用 — 探索用户意图、需求和设计，再进行功能创建、组件构建或行为修改 |
| dispatching-parallel-agents | 面对 2 个以上无共享状态或顺序依赖的独立任务时使用 |
| executing-plans | 在独立会话中按审查检查点执行已编写的实施计划 |
| finishing-a-development-branch | 实现完成且测试通过后，指导选择合并、PR 或清理等完成方式 |
| receiving-code-review | 收到代码审查反馈后、实施建议前使用 — 要求技术严谨性和验证，拒绝盲目同意 |
| requesting-code-review | 完成任务、实现主要功能或合并前使用，请求代码审查以验证工作质量 |
| subagent-driven-development | 在当前会话中使用子 agent 执行包含独立任务的实施计划 |
| systematic-debugging | 遇到 bug、测试失败或意外行为时，在提出修复方案前使用 |
| test-driven-development | 实现功能或修复 bug 时，在编写实现代码前使用 |
| using-git-worktrees | 需要隔离工作区的功能开发或执行实施计划前使用 — 通过原生工具或 git worktree 确保隔离 |
| using-superpowers | 每次对话开始时使用 — 建立技能发现和使用方式，要求在任何响应前先调用技能 |
| verification-before-completion | 声称工作完成或通过之前使用 — 要求先运行验证命令并确认输出，再声明成功 |
| writing-plans | 有多步骤任务的规格或需求时，在编写代码之前使用 |
| writing-skills | 创建、编辑或部署前验证技能时使用 |

<!-- END SKILL LIST -->
