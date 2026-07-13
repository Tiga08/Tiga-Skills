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
- **01-prompts/** — 可复用的 Prompt 模板，部分含个人信息的模板仅存于本地、不入库（见 `.gitignore`）。
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

```bash
# 从外部路径添加技能
./04-scripts/manage-skills.sh add ~/Projects/external-skills/my-skill

# 从 03-custom-skills/ 添加技能
./04-scripts/manage-skills.sh add-custom check-docs

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
| manage-global-skills | 通过 manage-skills.sh 管理 Tiga-Skills 全局技能注册表（02-agent-skills/）——配置用户级符号链接、添加外部或自定义技能、移除与列出条目、检查软链接健康并刷新 README 技能表。适用于在本仓库注册 / 移除全局共享技能或校验注册表链接状态；管理项目自身的 .agents/skills/ 请改用 manage-local-skills。 |

### custom-skills

来源于 `03-custom-skills/`，通过 `add-custom` 命令注册

| 名称 | 描述 |
| ---- | ---- |
| check-docs | 对照仓库实际状态审计治理文档（README.md、CLAUDE.md、AGENTS.md、docs/），报告失效路径、未记录内容、过期引用与文档间矛盾；--fix 可交互式应用修复并同步治理文件的中文翻译。适用于代码或目录结构变更后怀疑文档过期，或在提交 / PR 前核对文档准确性。 |
| gen-governance | 分析仓库结构，基于仓库实际证据生成根目录及子目录的 AGENTS.md / CLAUDE.md 治理文件，覆盖时合并仍然有效的旧规则，随后调用 md-to-zh 同步中文翻译。适用于仓库尚无治理文件、或大规模重构后需要重新生成的场景；若要审计现有文档与仓库是否一致，请改用 check-docs。 |
| manage-local-skills | 初始化、导入、更新、移除和列出当前项目 .agents/skills/ 中的项目级技能，通过 .claude/skills 与 .codex/skills 符号链接供 Claude Code 和 Codex 共享。适用于搭建项目技能目录或只为当前项目导入 / 更新 / 移除技能；管理 Tiga-Skills 全局注册表（02-agent-skills/）请改用 manage-global-skills。 |
| md-to-zh | 将英文 Markdown 文件或目录翻译为简体中文，逐行保留文档结构；已有译文仅按变动行增量更新，未变更的文件零成本跳过。治理文件（AGENTS.md / CLAUDE.md）在源文件旁生成 .zh.md，其余文件输出到 agent-plan/translations/。适用于为任何 Markdown 文档新建或刷新中文版本。 |
| switch-commit-pr | 分析待提交的 git 改动并按模式生成可直接运行的命令：switch（创建分支）、commit（追加 Conventional Commits 提交）、pr（追加 push 与 gh pr create）；默认仅打印命令，--execute 时直接执行。基准分支为 main/master/dev；处于其他分支时交互式询问是切出新分支还是留在当前分支继续（pr 模式工作区干净时直接续跑）。感知预暂存状态，明确独立的变更自动拆分为多个 commit，PR 指向本次运行的基准分支，绝不删除或恢复工作区文件。适用于工作区改动就绪后，需要从当前状态生成或执行分支 / 提交 / PR 命令的场景。 |

### mattpocock-skills

来源于外部路径，通过 `add` 命令注册

| 名称 | 描述 |
| ---- | ---- |
| ask-matt | 询问当前情境适合使用哪个技能或流程，作为本仓库中各项技能的路由器。 |
| claude-handoff | 将当前对话交接给新的后台代理，由其立即接手并继续工作。 |
| code-review | 以固定点（commit、branch、tag 或 merge-base）为基准，从“标准”（代码是否遵守仓库规范）和“规格”（代码是否满足原始 issue / PRD）两个维度审查变更，并通过并行子代理分别报告结果。适用于审查 branch、PR、开发中的变更，或用户要求“审查自某个固定点以来的改动”时。 |
| codebase-design | 用于设计深层模块的共享词汇。适用于设计或改进模块接口、寻找模块深化机会、确定 seam 的位置、提高代码的可测试性或 AI 可导航性，以及其他 skill 需要使用深层模块词汇时。 |
| design-an-interface | 使用并行子代理为模块生成多种显著不同的接口设计。适用于设计 API、探索接口方案、比较模块形态，或用户提出“设计两次”时。 |
| diagnosing-bugs | 用于疑难 Bug 和性能回退的诊断循环。适用于用户要求 diagnose / debug，或报告功能损坏、抛错、失败、运行缓慢时。 |
| domain-modeling | 构建并完善项目的领域模型。适用于明确领域术语或统一语言、记录架构决策，以及其他 skill 需要维护领域模型时。 |
| edit-article | 通过重组章节、提高清晰度和精简表达来编辑与改进文章。适用于用户希望编辑、修订或优化文章草稿时。 |
| git-guardrails-claude-code | 配置 Claude Code hooks，在执行前拦截危险的 Git 命令，例如 push、reset --hard、clean 和 branch -D。适用于防止破坏性 Git 操作、添加 Git 安全 hooks，或禁止 Claude Code 执行 push / reset 时。 |
| grill-me | 通过持续深入的访谈来完善计划或设计。 |
| grill-with-docs | 通过持续深入的访谈来完善计划或设计，并在过程中创建 ADR 和术语表等文档。 |
| grilling | 针对计划或设计持续深入地访谈用户。适用于用户希望在构建前对计划进行压力测试，或使用任何 grill 相关触发语时。 |
| handoff | 将当前对话压缩成一份交接文档，供另一个代理继续处理。 |
| implement | 根据规格或一组 tickets 实现具体工作。 |
| improve-codebase-architecture | 扫描代码库中的模块深化机会，以可视化 HTML 报告呈现结果，然后围绕用户选中的机会进行深入访谈。 |
| loop-me | 在当前工作区内，围绕用户想构建的工作流规格进行深入访谈。 |
| migrate-to-shoehorn | 将测试文件中的 `as` 类型断言迁移到 `@total-typescript/shoehorn`。适用于用户提及 shoehorn、希望替换测试中的 `as`，或需要构造部分测试数据时。 |
| obsidian-vault | 使用 wikilinks 和索引笔记在 Obsidian vault 中搜索、创建和管理笔记。适用于用户希望在 Obsidian 中查找、创建或整理笔记时。 |
| prototype | 构建一个可丢弃的原型来回答设计问题。适用于快速验证状态模型或逻辑是否合理，或探索 UI 应有的呈现方式时。 |
| qa | 开展交互式 QA 会话：用户以对话方式报告 Bug 或问题，代理负责创建 GitHub issues，并在后台探索代码库以补充上下文和领域语言。适用于用户希望报告 Bug、执行 QA、通过对话创建 issues，或提及 QA session 时。 |
| request-refactor-plan | 通过访谈制定由细小 commits 组成的详细重构计划，然后将其创建为 GitHub issue。适用于规划重构、创建重构 RFC，或将重构拆分为安全的增量步骤时。 |
| research | 基于高可信度的一手来源调查问题，并将结果记录为仓库中的 Markdown 文件。适用于研究主题、收集文档或 API 事实，或将资料阅读工作委派给后台代理时。 |
| resolving-merge-conflicts | 适用于解决正在进行的 Git merge / rebase 冲突。 |
| scaffold-exercises | 创建包含 sections、problems、solutions 和 explainers 且能通过 lint 的练习目录结构。适用于搭建练习、创建练习桩，或初始化新的课程章节时。 |
| setup-matt-pocock-skills | 为工程类 skills 配置当前仓库，包括 issue tracker、triage 标签词汇和领域文档布局。首次使用其他工程类 skills 前运行一次。 |
| setup-pre-commit | 在当前仓库中配置 Husky pre-commit hooks，并集成 lint-staged（Prettier）、类型检查和测试。适用于添加 pre-commit hooks、配置 Husky / lint-staged，或加入提交时的格式化、类型检查和测试时。 |
| setup-ts-deep-modules | 在 TypeScript 仓库中配置 dependency-cruiser，使每个 package 成为深层模块：实现隐藏在子目录中，只能通过入口文件访问。需由用户显式调用。 |
| tdd | 测试驱动开发。适用于用户希望以测试优先方式构建功能或修复 Bug、提及 red-green-refactor，或需要 integration tests 时。 |
| teach | 在当前工作区内教授用户一项新技能或概念。 |
| to-spec | 将当前对话整理为规格并发布到项目的 issue tracker；不再访谈，只综合已经讨论的内容。 |
| to-tickets | 将计划、规格或当前对话拆分为一组 tracer-bullet tickets，每个 ticket 声明其阻塞依赖，并发布到已配置的 tracker；本地 tracker 将依赖写入各 ticket 文件，真实 tracker 则创建原生 blocking links。 |
| triage | 通过一组 triage 角色组成的状态机处理 issues 和外部 PR，完成分类、验证、必要时的深入访谈，并产出代理可直接执行的任务说明。 |
| ubiquitous-language | 从当前对话中提取 DDD 风格的统一语言术语表，标记歧义并建议规范术语，保存到 `UBIQUITOUS_LANGUAGE.md`。适用于定义领域术语、构建词汇表、规范术语，或用户提及 domain model / DDD 时。 |
| wayfinder | 将超出单次代理会话容量的大型工作规划为 issue tracker 上共享的调查 tickets 地图，并逐项解决，直到通往目标的路径清晰。 |
| wizard | 生成交互式 Bash 向导，引导用户完成第三方配置、一次性迁移或 A→B 状态转换等人工流程，包括打开 URL、收集值、确认步骤，以及写入 `.env` 文件和 GitHub Actions secrets。 |
| writing-beats | 写作的 exploit 阶段：将原始材料组织成一连串叙事 beats，确保每个术语在后续内容依赖它之前得到充分说明。 |
| writing-fragments | 写作的 explore 阶段：从原始片段中挖掘素材，暂不建立结构。 |
| writing-great-skills | 编写和编辑高质量 skills 的参考资料，提供使 skill 行为可预测的词汇与原则。 |
| writing-shape | 写作的 exploit 阶段：将原始材料逐段塑造成文章。 |

<!-- END SKILL LIST -->
