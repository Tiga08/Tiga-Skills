# Tiga-Skills

集中式 Agent Skills 注册与分发仓库，让 Claude Code 和 Codex 共用一套项目级、外部与自定义技能。

Tiga-Skills 通过符号链接聚合技能源，并用 Bash 管理入口维护注册、检查和技能清单；仓库还包含 Skill 自带的无第三方依赖 Python 辅助工具，不含应用代码或构建系统。

## 快速开始

默认布局下，本仓库位于 `~/Projects/Tiga/Skills`；如需使用已注册的外部技能，还需将 [AG-Tools](https://github.com/Tiga08/AG-Tools) 放在 `~/Projects/AG-Tools`。

在仓库根目录配置用户级发现链接，然后检查注册表：

```bash
./04-scripts/manage-skills.sh setup
./04-scripts/manage-skills.sh check
```

## 使用方法

新增技能前，先在 `descriptions-zh.conf` 中配置 `<name>.description`；外部技能缺少 `argument-hint` 时，可再提供 `<name>.arguments`。

- 注册外部或自定义技能：`add <path> [--name <name>]` / `add-custom <name>`
- 移除注册项：`remove <name>`
- 查看、校验或刷新清单：`list` / `check` / `update-readme`

以上子命令均由 `./04-scripts/manage-skills.sh` 执行；完整的 Agent 操作命令见 [`AGENTS.md`](AGENTS.md#commands)。

## 资源目录

可复用 Prompt：

- [`en-chat-assistant.md`](01-prompts/en-chat-assistant.md) — 把中文聊天内容整理为可直接发送的英文回复。
- [`en-to-zh-assistant.md`](01-prompts/en-to-zh-assistant.md) — 理解并翻译英文文段、图片、网址、词汇或文件。
- [`zh-to-en-assistant.md`](01-prompts/zh-to-en-assistant.md) — 将中文词汇或消息转换为简洁、地道的英文。

下方 Agent Skills 清单由 `manage-skills.sh` 根据注册表与 `descriptions-zh.conf` 生成。

<!-- BEGIN SKILL LIST -->

### 项目级技能

位于 `.agents/skills/`，供操作本仓库使用

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| tiga-global-skills | setup\|add\|add-custom\|remove\|list\|check\|update-readme [args] | 管理 Tiga-Skills 全局技能注册表：配置用户级链接、注册与移除外部或自定义 skill、列出条目、检查链接与 frontmatter 健康状态、刷新 README 技能清单；中文说明来自根目录 descriptions-zh.conf。 |

### custom-skills

来源于 `03-custom-skills/`，通过 `add-custom` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| tiga-commit-push-pr | switch\|commit\|pr\|push [--dry-run] | 安全分析并执行 Git 分支切换、Conventional Commit、推送与 PR 工作流，适用于提交当前改动、直接推送当前分支或创建和更新 PR。 |
| tiga-govsync | check\|update\|fix [--scope <path>] [--no-translate] [--skills] | 依据仓库实况和单一权威来源模型治理项目自有 README、docs 与 Agent 指令文件，同步简体中文译文，并可审计本地 Skill。适用于治理文档缺失、陈旧、重复、章节结构不一致或与仓库状态脱节的情况。 |
| tiga-local-skills | init\|add\|update\|remove\|list [args] | 管理当前项目 `.agents/skills/` 中供 Claude Code 与 Codex 共享的项目级 skills，支持初始化、导入、更新、移除与列出；增删 AG-Tools 来源条目时同步维护其 SKILLS-REFS.md 下游引用清单。 |
| tiga-translate | <path...> | 翻译 Markdown 文件或目录前先判断需要翻译的内容与数量，再按文档类型自动放置简体中文译文；可手动调用，也可由 `tiga-govsync` 等其他技能调用。 |
| tiga-update-skills | — | 依据 Claude Code、Codex 与 Agent Skills 官方规范审查并更新本地 Skill，检查结构、兼容性、元数据、调用策略与规范漂移，并可刷新官方文档快照后自审自身。 |

### ECC-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| security-scan | scan [<path>]\|init [--min-severity <level>] [--format json\|markdown\|html] [--fix] [--opus] [--stream] | 使用 AgentShield 扫描 `.claude/` 中的 CLAUDE.md、settings.json、MCP、hooks 和 agent 定义，发现安全漏洞、配置错误与注入风险，也可初始化安全配置。 |
| skill-scout | — | 在创建、复刻或扩展 skill 前搜索并审查本地、marketplace、GitHub 和 Web 候选；无固定命令参数，调用时提供目标任务、触发条件、涉及领域与关键词。 |
| skill-stocktake | [full] | 按统一质量清单审查全局及当前项目的 Claude skills 和 commands，依据缓存自动执行增量 Quick Scan 或完整盘点，当前工作目录决定项目级扫描范围。 |

### anthropics-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| pptx | — | 创建、读取、编辑和校验 PowerPoint 的 `.pptx` 与 `.potx` 文件，适用于演示文稿、模板、布局、备注及评论等相关任务。 |

### baoyu-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| baoyu-format-markdown | <file> [--quotes\|-q] [--no-quotes] [--spacing\|-s] [--no-spacing] [--emphasis\|-e] [--no-emphasis] | 将纯文本或 Markdown 优化为带 frontmatter、标题、摘要、层级、列表和代码块的 `{filename}-formatted.md`，也可选择保留原结构或仅原地修正排版。 |
| baoyu-url-to-markdown | <url> [--output <path>] [--format markdown\|json] [--adapter x\|youtube\|hn\|generic] [--headless] [--wait-for none\|interaction\|force] ... | 通过 Chrome 抓取网页并用 X、YouTube、Hacker News 或通用适配器转换为 Markdown/JSON，可按需等待登录或人工交互后再抓取。 |

### mattpocock-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| grill-me | — | 通过持续访谈澄清并压力测试计划或设计，直到关键决策分支达成共同理解。 |

<!-- END SKILL LIST -->

## 文档

- [`AGENTS.md`](AGENTS.md) / [`AGENTS.zh.md`](AGENTS.zh.md) — 仓库结构、权属、命令与操作边界。
- [`SKILLS-INDEX.md`](SKILLS-INDEX.md) — AG-Tools 范围内的技能索引。
- [`SKILLS-REFS.md`](SKILLS-REFS.md) — AG-Tools 技能的下游引用清单。
