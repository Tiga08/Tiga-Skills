# Tiga-Skills

集中式技能管理中心，通过软链接聚合来自外部仓库和自定义目录的 Agent Skills，并提供给 Claude Code 和 Codex 使用。

## 目录结构

```
Tiga-Skills/
├── .agents/skills/       # 项目级 Skills（跨 Agent 共享）
├── .claude/              # Claude Code 项目配置
├── .codex/               # Codex 项目配置
├── .tiga/                # 用户相关的本地文件入口（git-ignored）
│   ├── agent-res/          # Agent 生成内容
│   │   └── markdown/         # Agent 生成的 Markdown 文件
│   └── Todo.md             # 用户个人计划与待办
├── 01-prompts/           # 可复用的 Prompt 模板
├── 02-agent-skills/      # Agent Skills 注册表（扁平存放技能软链接，分组仅体现在下方技能清单文档中）
├── 03-custom-skills/     # 用户自定义 Skills（源文件）
├── 04-scripts/           # 实用脚本
└── descriptions-zh.conf  # README 技能中文说明的权威配置
```

- **.agents/skills/** — 项目级技能，`.claude/skills` 和 `.codex/skills` 均为指向此目录的软链接。
- **.claude/** 、 **.codex/** — Agent 项目配置目录，`skills` 均指向 `.agents/skills/`。
- **02-agent-skills/** — 技能注册表，技能条目以软链接形式直接扁平存放在该目录下，来源分组仅体现在 README 技能清单中。外部技能软链接为用户级相对路径（如 `../../../AG-Tools/...`），要求 [AG-Tools](https://github.com/Tiga08/AG-Tools) 位于 `~/Projects/AG-Tools`、本仓库位于 `~/Projects/Tiga/Skills`。
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

新增技能前，先在项目根目录的 `descriptions-zh.conf` 中配置 README 所需的中文说明：

```ini
my-skill.description=说明 skill 的核心功能与适用场景。
my-skill.arguments=<file> [--flag]
```

`add` 与 `add-custom` 会在创建链接前校验 `description`；`remove` 会同步删除对应配置。`update-readme` 从该配置生成技能说明。

技能清单的「参数」列优先取 `SKILL.md` 的 `argument-hint` 字段，仅当该字段缺失（如不可修改的外部技能）时才回退到 `<name>.arguments`，两者都没有时显示 `—`。

```bash
# 从外部路径添加技能
./04-scripts/manage-skills.sh add ~/Projects/external-skills/my-skill

# 从 03-custom-skills/ 添加技能
./04-scripts/manage-skills.sh add-custom tiga-govsync

# 移除技能
./04-scripts/manage-skills.sh remove my-skill

# 列出已注册技能
./04-scripts/manage-skills.sh list

# 检查技能软链接与项目级链接的健康状态
./04-scripts/manage-skills.sh check

# 更新 README 技能清单
./04-scripts/manage-skills.sh update-readme
```

## 技能清单

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
| tiga-commit-pr | switch\|commit\|pr\|push [--dry-run] | 分析当前 Git 改动或已有分支提交，按模式准备分支、Conventional Commit、推送和 PR 流程；`push` 在当前分支直接提交并推送、跳过分支切换与 PR（面向个人独享仓库）；默认执行安全命令，保留工作区文件和已有暂存状态。 |
| tiga-govsync | check\|update\|fix [--scope <path>] [--no-translate] [--skills] | 依据仓库实况和单一权威来源模型治理项目自有 README、docs 与 Agent 指令文件，同步简体中文译文，并可审计本地 Skill。适用于治理文档缺失、陈旧、重复、章节结构不一致或与仓库状态脱节的情况。 |
| tiga-local-skills | init\|add\|update\|remove\|list [args] | 管理当前项目 `.agents/skills/` 中供 Claude Code 与 Codex 共享的项目级 skills，支持初始化、导入、更新、移除与列出；增删 AG-Tools 来源条目时同步维护其 SKILLS-REFS.md 下游引用清单。 |
| tiga-translate | <path...> | 翻译 Markdown 文件或目录前先判断需要翻译的内容与数量，再按文档类型自动放置简体中文译文；可手动调用，也可由 `tiga-govsync` 等其他技能调用。 |
| tiga-update-skills | — | 依据 Claude Code、Codex 与 Agent Skills 官方规范审查并更新本地 Skill，检查结构、兼容性、元数据、调用策略与规范漂移，并可刷新官方文档快照后自审自身。 |

### baoyu-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| baoyu-format-markdown | <file> [--quotes\|-q] [--no-quotes] [--spacing\|-s] [--no-spacing] [--emphasis\|-e] [--no-emphasis] | 将纯文本或 Markdown 优化为带 frontmatter、标题、摘要、层级、列表和代码块的 `{filename}-formatted.md`，也可选择保留原结构或仅原地修正排版。 |
| baoyu-url-to-markdown | <url> [--output <path>] [--format markdown\|json] [--adapter x\|youtube\|hn\|generic] [--headless] [--wait-for none\|interaction\|force] ... | 通过 Chrome 抓取网页并用 X、YouTube、Hacker News 或通用适配器转换为 Markdown/JSON，可按需等待登录或人工交互后再抓取。 |

### ECC-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 参数 | 描述 |
| ---- | ---- | ---- |
| security-scan | scan [<path>]\|init [--min-severity <level>] [--format json\|markdown\|html] [--fix] [--opus] [--stream] | 使用 AgentShield 扫描 `.claude/` 中的 CLAUDE.md、settings.json、MCP、hooks 和 agent 定义，发现安全漏洞、配置错误与注入风险，也可初始化安全配置。 |
| skill-scout | — | 在创建、复刻或扩展 skill 前搜索并审查本地、marketplace、GitHub 和 Web 候选；无固定命令参数，调用时提供目标任务、触发条件、涉及领域与关键词。 |
| skill-stocktake | [full] | 按统一质量清单审查全局及当前项目的 Claude skills 和 commands，依据缓存自动执行增量 Quick Scan 或完整盘点，当前工作目录决定项目级扫描范围。 |

<!-- END SKILL LIST -->
