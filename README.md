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
├── descriptions-zh.conf  # README 技能中文说明的权威配置
├── 01-prompts/           # 可复用的 Prompt 模板
├── 02-agent-skills/      # Agent Skills 注册表（扁平存放技能软链接，分组仅体现在下方技能清单文档中）
├── 03-custom-skills/     # 用户自定义 Skills（源文件）
└── 04-scripts/           # 实用脚本
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
```

`add` 与 `add-custom` 会在创建链接前校验该字段；`remove` 会同步删除对应配置。`update-readme` 从该配置生成技能说明。

```bash
# 从外部路径添加技能
./04-scripts/manage-skills.sh add ~/Projects/external-skills/my-skill

# 从 03-custom-skills/ 添加技能
./04-scripts/manage-skills.sh add-custom tiga-check-docs

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

| 名称 | 描述 |
| ---- | ---- |
| manage-global-skills | 管理 Tiga-Skills 全局技能注册表，支持配置用户级链接（`setup`）、注册外部 skill（`add <path> [--name <name>]`）、注册自定义 skill（`add-custom <name>`）、移除（`remove <name>`）、列出（`list`）、检查（`check`）及刷新 README（`update-readme`）；中文说明来自根目录 descriptions-zh.conf。 |

### custom-skills

来源于 `03-custom-skills/`，通过 `add-custom` 命令注册

| 名称 | 描述 |
| ---- | ---- |
| tiga-check-docs | 对照仓库实际状态审计 README.md、CLAUDE.md、AGENTS.md 与 docs/，报告失效路径、遗漏内容、过期引用和文档矛盾；不传参数时扫描全部治理文档，支持重复指定 `--scope <file>` 限定范围、`--fix` 交互修复并同步治理文件译文、`--verbose` 显示通过项。 |
| tiga-commit-pr | 分析当前 Git 改动或已有分支提交，按必选模式 `switch`、`commit`、`pr` 准备分支、Conventional Commit、推送和 PR 流程；默认仅打印安全命令，传入 `--execute` 时按顺序执行，同时保留工作区文件和已有暂存状态。 |
| tiga-gen-governance | 根据真实仓库结构生成或重建 AGENTS.md 与 CLAUDE.md，合并仍有效的旧规则并同步简体中文版本；不传参数时处理当前项目，支持 `--dry-run` 仅输出计划、`--force` 无提示覆盖冲突文件、`--no-translate` 跳过译文同步。 |
| tiga-local-skills | 管理当前项目 `.agents/skills/` 中供 Claude Code 与 Codex 共享的项目级 skills；支持 `init`、`add <path> [--name <name>] [--link]`（默认复制，`--link` 改为符号链接）、`update [<name>] [<path>]`（省略名称时批量更新）、`remove <name>` 和 `list`。 |
| tiga-translate | 将一个或多个 Markdown 文件或目录路径翻译为简体中文，保留逐行结构并增量更新；调用格式为 `<path>... [--force] [--output <dir>] [--glossary <file>]`，分别用于强制全文重译、指定非治理文件输出目录和指定术语表；治理文件输出相邻 `.zh.md`。 |

### baoyu-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 描述 |
| ---- | ---- |
| baoyu-format-markdown | 将 `<file>` 的纯文本或 Markdown 优化为带 frontmatter、标题、摘要、层级、列表和代码块的 `{filename}-formatted.md`，也可选择保留原结构或仅原地修正排版；排版参数包括 `--quotes`/`-q`、`--no-quotes`、`--spacing`/`-s`、`--no-spacing`、`--emphasis`/`-e`、`--no-emphasis`。 |
| baoyu-url-to-markdown | 通过 Chrome 抓取 `<url>` 并用 X、YouTube、Hacker News 或通用适配器转换为 Markdown/JSON；支持 `--output <path>`、`--format markdown/json`/`--json`、`--adapter x/youtube/hn/generic`、`--headless`、`--wait-for none/interaction/force`（别名 `--wait-for-interaction`、`--wait-for-login`）、`--timeout <ms>`、`--interaction-timeout <ms>`、`--interaction-poll-interval <ms>`、`--download-media`、`--media-dir <dir>`、`--cdp-url <url>`、`--browser-path <path>`、`--chrome-profile-dir <path>`、`--debug-dir <dir>`。 |

### ECC-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 描述 |
| ---- | ---- |
| security-scan | 使用 AgentShield 扫描 `.claude/` 中的 CLAUDE.md、settings.json、MCP、hooks 和 agent 定义，或用 `init` 初始化安全配置；`scan [<path>]` 支持 `--path <path>`、`--min-severity <level>`、`--format json/markdown/html`、`--fix`，深度分析可组合 `--opus` 与 `--stream`。 |
| skill-scout | 在创建、复刻或扩展 skill 前搜索并审查本地、marketplace、GitHub 和 Web 候选；无固定命令参数，调用时提供目标任务、触发条件、涉及领域/工具/框架/数据源及 3–5 个关键词或同义词，也可明确要求跳过搜索或从零创建。 |
| skill-stocktake | 按统一质量清单审查全局及当前项目的 Claude skills 和 commands；运行 `/skill-stocktake` 时依据 `results.json` 自动执行 Quick Scan（无缓存则完整盘点），传入唯一可选位置参数 `full`（`/skill-stocktake full`）可强制 Full Stocktake，当前工作目录决定项目级扫描范围。 |

<!-- END SKILL LIST -->
