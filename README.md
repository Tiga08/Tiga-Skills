# Tiga-Skills

集中式 Agent Skills 仓库，通过符号链接聚合外部 Skill，让 Claude Code 和 Codex 共用一套高度自定义的 Skill 库。

## 快速开始

本仓库位于 `~/Projects/AG-Tools/tiga-skills`；前置条件：将 [AG-Tools 仓库](https://github.com/Tiga08/AG-Tools) clone 到本机 `~/Projects/AG-Tools` 路径下。

在仓库根目录执行如下指令：

```bash
# 设置 ~/.claude/skills 和 ~/.codex/skills/tiga-skills 软链接
./02-scripts/manage-skills.sh setup

# 检查 03-skills/ 中的 skill 是否存在、软链接是否有效，以及项目级链接是否正常
./02-scripts/manage-skills.sh check
```

## Skill 清单

由 `manage-skills.sh update-readme` 自动生成。

<!-- BEGIN SKILL LIST -->

### 项目级技能

位于 `.agents/skills/`，供操作本仓库使用

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| tiga-global-skills | setup\|add\|remove\|list\|check\|update-readme [args] | 管理 Tiga-Skills 全局技能目录：配置用户级链接、注册与移除外部 skill、列出条目、检查目录与 frontmatter 健康状态、刷新 README 技能清单；中文说明来自根目录 descriptions-zh.conf。 |

### custom-skills

来源于 `03-skills/` 中的自定义技能目录

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| tiga-commit-push-pr | switch\|commit\|pr\|push [--dry-run] | 安全分析并执行 Git 分支切换、Conventional Commit、推送与 PR 工作流，适用于提交当前改动、直接推送当前分支或创建和更新 PR。 |
| tiga-local-skills | init\|add\|update\|remove\|list [args] | 管理当前项目 `.agents/skills/` 中供 Claude Code 与 Codex 共享的项目级 skills，支持初始化、导入、更新、移除与列出；增删 AG-Tools 来源条目时同步维护其 SKILLS-REFS.md 下游引用清单。 |
| tiga-translate | <path...> | 翻译 Markdown 文件或目录前先判断需要翻译的内容与数量，再按文档类型自动放置简体中文译文；仅支持显式调用。 |
| tiga-update-skills | — | 依据 Claude Code、Codex 与 Agent Skills 官方规范审查并更新本地 Skill，检查结构、兼容性、元数据、调用策略与规范漂移，并可刷新官方文档快照后自审自身。 |

### mattpocock-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| grilling | — | 以设计树方式分轮追问计划、决策或想法：每轮把当前可判定的问题一次性列出并附推荐答案，事实由子代理自行查证，直到所有分支澄清并达成共同理解。 |

<!-- END SKILL LIST -->

## Prompt 清单

- [`en-chat-assistant.md`](01-prompts/en-chat-assistant.md) — 把中文聊天内容整理为可直接发送的英文回复。
- [`en-to-zh-assistant.md`](01-prompts/en-to-zh-assistant.md) — 理解并翻译英文文段、图片、网址、词汇或文件。
- [`zh-to-en-assistant.md`](01-prompts/zh-to-en-assistant.md) — 将中文词汇或消息转换为简洁、地道的英文。

## 文档

- [`AGENTS.md`](AGENTS.md) / [`AGENTS.zh.md`](AGENTS.zh.md) — 仓库结构、权属、命令与操作边界。
- [`SKILLS-INDEX.md`](SKILLS-INDEX.md) — AG-Tools 范围内的 skill 索引。
- [`SKILLS-REFS.md`](SKILLS-REFS.md) — AG-Tools skill 的下游引用清单。
