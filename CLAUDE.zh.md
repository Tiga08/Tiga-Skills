@AGENTS.md

# Tiga-Skills: Claude Code 操作指南

## 约束

- 此仓库是 Agent Skills 管理仓库，不是应用或库。除非用户明确要求，否则不要添加构建系统、运行时依赖或应用框架。
- `02-agent-skills/<source>/` 下的技能条目必须保持为符号链接；来源分组目录是真实目录。不要在那里放置常规技能目录，也不要直接编辑符号链接目标。
- 项目级技能（用于操作此仓库）位于 `.agents/skills/`。`.claude/skills` 和 `.codex/skills` 是指向该目录的符号链接。
- 注册表技能源文件位于 `03-custom-skills/`。修改注册表技能时，在源目录中工作，然后运行 `./04-scripts/manage-skills.sh update-readme` 刷新文档。
- 外部技能由上游仓库维护。同步外部技能前先检查上游状态，并且只在用户确认后拉取或注册变更。
- 脚本使用 Bash 和 UTF-8。新增或修改脚本注释时使用简体中文，并保持现有直接、可执行的脚本风格。

## 常见问题

1. **将 `02-agent-skills/` 当作源目录。** 它是分组注册表视图；`custom-skills/` 和 `superpowers/` 等来源目录是真实目录，其中的技能条目应为符号链接。要修改注册表技能，请编辑 `03-custom-skills/`。对于外部技能，请前往上游仓库。项目级技能位于 `.agents/skills/`，而不是这里。

2. **绕过 `manage-skills.sh` 进行符号链接管理。** 手动创建或删除符号链接会导致 README 技能列表与实际注册状态不一致。使用 `./04-scripts/manage-skills.sh` 进行添加、移除、设置和列表更新。

3. **忘记更新 README 技能列表。** 技能变更后，运行 `./04-scripts/manage-skills.sh update-readme`。该命令会扫描 `02-agent-skills/` 中分组子目录下的符号链接，并从每个 `SKILL.md` 中提取元数据。

4. **将 `agent-plan/` 或 `Todo/` 当作权威内容。** 这些目录是本地草稿和工作笔记，已被 `.gitignore` 排除。只有在用户明确要求时，才将其中内容提升到正式目录。

5. **使用旧目录布局。** 当前仓库使用 `01-prompts/`、`02-agent-skills/`、`03-custom-skills/` 和 `04-scripts/`。不要重新引入已移除的目录，例如 `00-skill-index/`、`03-workflows/` 或 `05-custom-skills/`。

## 常用命令

```bash
./04-scripts/manage-skills.sh setup
./04-scripts/manage-skills.sh add <path> [--name <name>]
./04-scripts/manage-skills.sh add-custom <name>
./04-scripts/manage-skills.sh remove <name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh update-readme
```
