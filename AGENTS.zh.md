# Tiga-Skills: 集中式 Agent Skills 仓库

Tiga-Skills 是一个内容和脚本仓库，通过扁平符号链接集中注册外部和自定义 Agent Skills，并将它们暴露给 Claude Code 和 Codex。该仓库不包含应用代码、构建系统或运行时依赖。核心约束是：`02-agent-skills/` 只作为扁平符号链接注册表，自定义技能源文件位于 `03-custom-skills/`，并且所有技能注册和移除都必须通过 `./04-scripts/manage-skills.sh` 完成。

## 结构

| 路径 | 用途 | 权威性 |
| --------- | ------- | --------- |
| `.agents/skills/` | 跨 agent 共享的项目级技能；`.claude/skills` 和 `.codex/skills` 符号链接到这里 | primary |
| `.claude/` | Claude Code 项目配置；`skills/` 是指向 `.agents/skills` 的符号链接 | config |
| `.codex/` | Codex 项目配置；`skills/` 是指向 `.agents/skills` 的符号链接 | config |
| `.tiga/` | 已被 Git 忽略的用户本地工作区；Agent 输出位于 `agent-res/` 下，个人计划位于 `Todo.md`，后续本地模块也可添加于此 | derived |
| `01-prompts/` | 可复用的 prompt 模板 | primary |
| `02-agent-skills/` | 扁平的 Agent Skills 注册表；技能条目以符号链接形式直接放在该目录下，按来源的分组只体现在 README 中 | derived |
| `03-custom-skills/` | 项目内部自定义技能的源文件 | primary |
| `04-scripts/` | 用于技能注册、移除、设置、链接健康检查和 README 更新的脚本 | primary |
| `descriptions-zh.conf` | README 技能清单所用中文说明的权威来源 | primary |
| `SKILLS-REFS.md` | 指向 `~/Projects/AG-Tools/SKILLS-REFS.md` 的符号链接，即 AG-Tools 下游引用清单 | derived |

只维护根目录级治理文件。除非用户明确要求，否则不要生成子目录 `CLAUDE.md` 文件。

## Markdown 生成

- 只有在用户明确要求时才创建 Markdown 文件。
- 除非用户指定其他路径，否则将生成的 Markdown 保存到 `.tiga/agent-res/markdown/` 下；如果该目录不存在，则创建它。
- 生成的 Markdown 文件命名为 `YYYY-MM-DD_{purpose}.md`。
- 例外：
  - 翻译文件遵循 tiga-translate 技能的输出规则：治理文件（`AGENTS.md`、`CLAUDE.md`）翻译为与源文件同目录的 `.zh.md`；所有其他文件输出到 `.tiga/translations/`。
  - 项目治理文件（如 `CLAUDE.md`、`AGENTS.md`、`README.md` 和 `CHANGELOG.md`）保留在其约定位置。

## 用户本地工作区

- 将 `.tiga/` 作为用户相关本地文件的统一入口；整个目录均被 `.gitignore` 排除。
- 将个人计划和待办事项存放在 `.tiga/Todo.md`。
- 后续用户本地模块可作为新文件或子目录直接添加到 `.tiga/` 下；当相关约定会影响 Agent 行为时，在此处记录。

## 技能

### 项目级技能

- 项目级技能位于 `.agents/skills/<name>/SKILL.md`。
- `.claude/skills` 和 `.codex/skills` 是指向 `.agents/skills` 的符号链接，因此所有受支持的 agent 共享同一个技能库。
- 项目级技能用于操作此仓库本身（例如 `tiga-global-skills`）。

### 注册表技能

- 在 `03-custom-skills/` 中创建和编辑注册表技能源文件。
- 在根目录 `descriptions-zh.conf` 中维护每个已注册技能的 README 中文说明；不要从 `SKILL.md` frontmatter 派生 README 内容。
- 使用 `./04-scripts/manage-skills.sh add-custom <name>` 将自定义技能注册到 `02-agent-skills/`。
- 使用 `./04-scripts/manage-skills.sh add <path> [--name <name>]` 注册外部技能。对于 `$HOME` 下的路径，`add` 会创建用户级相对软链接（如 `../../../AG-Tools/...`），前提是本仓库位于 `~/Projects/Tiga/Skills`、AG-Tools 位于 `~/Projects/AG-Tools`。
- 使用 `./04-scripts/manage-skills.sh remove <name>` 移除技能注册。
- 使用 `./04-scripts/manage-skills.sh check` 检查技能软链接与项目级链接的健康状态。
- 在任何技能注册、移除或 `descriptions-zh.conf` 元数据变更后，运行 `./04-scripts/manage-skills.sh update-readme` 刷新 `README.md` 技能列表。

## 边界

**始终：**

- 修改文件前先读取相关文件。
- 将 `02-agent-skills/` 视为扁平符号链接注册表；不要直接在其中编辑技能内容。
- 修改自定义技能时，编辑 `03-custom-skills/<name>/` 下的源文件。
- 使用 `./04-scripts/manage-skills.sh` 进行技能注册、移除和用户级设置。
- 保持 `README.md` 技能列表与 `02-agent-skills/` 当前注册状态一致。

**先询问：**

- 创建或删除技能、prompt、脚本或治理文件。
- 覆盖现有 `AGENTS.md`、`CLAUDE.md` 或 `README.md`。
- 修改 `.claude/`、`.gitignore` 或其他核心配置。
- 注册、移除或重命名技能。
- 从外部上游仓库拉取或同步内容。

**绝不：**

- 直接修改从 `02-agent-skills/` 符号链接而来的外部技能源文件。
- 手动在 `02-agent-skills/` 下直接创建或删除符号链接来绕过 `manage-skills.sh`。
- 编造技能名称、来源或描述。
- 泄露、提交或输出 `.env`、token、cookie、private key 或其他敏感数据。
- 为了让检查通过而删除、绕过或削弱验证步骤。

## 指令优先级

1. 显式用户指令
2. 此 `AGENTS.md`
3. 根目录 `CLAUDE.md` 中与本文件不冲突的操作指导
4. 当前仓库文件和目录结构中的证据
5. 现有风格和约定
