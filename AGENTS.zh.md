# Tiga-Skills: 集中式 Agent Skills 仓库

Tiga-Skills 是一个内容和脚本仓库，通过分组符号链接集中注册外部和自定义 Agent Skills，并将它们暴露给 Claude Code 和 Codex。该仓库不包含应用代码、构建系统或运行时依赖。核心约束是：`02-agent-skills/` 只作为分组符号链接注册表，自定义技能源文件位于 `03-custom-skills/`，并且所有技能注册和移除都必须通过 `./04-scripts/manage-skills.sh` 完成。

## 结构

| 目录 | 用途 | 权威性 |
| --------- | ------- | --------- |
| `.agents/skills/` | 跨 agent 共享的项目级技能；`.claude/skills` 和 `.codex/skills` 符号链接到这里 | primary |
| `.claude/` | Claude Code 项目配置；`skills/` 是指向 `.agents/skills` 的符号链接 | config |
| `.codex/` | Codex 项目配置；`skills/` 是指向 `.agents/skills` 的符号链接 | config |
| `01-prompts/` | 可复用的 prompt 模板 | primary |
| `02-agent-skills/` | 按来源分组的 Agent Skills 注册表；每个分组下的技能条目都应为符号链接 | derived |
| `03-custom-skills/` | 项目内部自定义技能的源文件 | primary |
| `04-scripts/` | 用于技能注册、移除、设置和 README 更新的脚本 | primary |
| `agent-plan/` | Agent 生成的计划和草稿；已被 git 忽略 | derived |
| `Todo/` | 本地待办事项和工作笔记；已被 git 忽略 | derived |

只维护根目录级治理文件。除非用户明确要求，否则不要生成子目录 `CLAUDE.md` 文件。

## Markdown 生成

- 只有在用户明确要求时才创建 Markdown 文件。
- 除非用户指定其他路径，否则将生成的 Markdown 保存到 `agent-plan/` 下；如果该目录不存在，则创建它。
- 生成的 Markdown 文件命名为 `YYYY-MM-DD_{purpose}.md`。
- 例外：
  - 翻译文件遵循 md-to-zh 技能的输出规则：治理文件（`AGENTS.md`、`CLAUDE.md`）翻译为与源文件同目录的 `.zh.md`；所有其他文件输出到 `agent-plan/translations/`。
  - 项目治理文件（如 `CLAUDE.md`、`AGENTS.md`、`README.md` 和 `CHANGELOG.md`）保留在其约定位置。

## 技能

### 项目级技能

- 项目级技能位于 `.agents/skills/<name>/SKILL.md`。
- `.claude/skills` 和 `.codex/skills` 是指向 `.agents/skills` 的符号链接，因此所有受支持的 agent 共享同一个技能库。
- 项目级技能用于操作此仓库本身（例如 `manage-global-skills`）。

### 注册表技能

- 在 `03-custom-skills/` 中创建和编辑注册表技能源文件。
- 使用 `./04-scripts/manage-skills.sh add-custom <name>` 将自定义技能注册到 `02-agent-skills/`。
- 使用 `./04-scripts/manage-skills.sh add <path> [--name <name>]` 注册外部技能。
- 使用 `./04-scripts/manage-skills.sh remove <name>` 移除技能注册。
- 在任何技能注册、移除或元数据变更后，运行 `./04-scripts/manage-skills.sh update-readme` 刷新 `README.md` 技能列表。

## 边界

**始终：**

- 修改文件前先读取相关文件。
- 将 `02-agent-skills/` 视为分组符号链接注册表；不要直接在其中编辑技能内容。
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
- 手动创建或删除 `02-agent-skills/` 子目录中的符号链接来绕过 `manage-skills.sh`。
- 编造技能名称、来源或描述。
- 泄露、提交或输出 `.env`、token、cookie、private key 或其他敏感数据。
- 为了让检查通过而删除、绕过或削弱验证步骤。

## 指令优先级

1. 显式用户指令
2. 此 `AGENTS.md`
3. 当前仓库文件和目录结构中的证据
4. 现有风格和约定
