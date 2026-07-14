@AGENTS.md

# Tiga-Skills: Claude Code 操作指南

## 约束

- 将此仓库保持为内容与 Bash 管理仓库。除非用户明确要求，否则不要引入应用框架、构建系统或运行时依赖。
- 在各技能的权威位置进行编辑：仓库操作技能位于 `.agents/skills/`，自定义注册表技能位于 `03-custom-skills/`，外部技能位于其上游仓库。将 `02-agent-skills/` 视为派生状态。
- 使用 `./04-scripts/manage-skills.sh` 执行注册表和用户级链接操作。注册表或技能元数据变更后，先运行 `update-readme`，再运行 `check`。
- 提议同步外部上游前先检查其状态，并在拉取或注册上游变更前取得用户确认。
- 脚本应保持为 UTF-8 编码的可执行 Bash，遵循现有直接的命令风格，新增或修改的脚本注释使用简体中文。完成前对修改过的 shell 脚本运行 `bash -n`。

## 常见问题

1. **混淆三个技能位置。** `.agents/skills/` 存放仓库操作技能，`03-custom-skills/` 存放自定义注册表源文件，`02-agent-skills/` 仅存放扁平注册软链接。决定可安全编辑哪个源文件前，先解析注册表链接。

2. **绕过 `manage-skills.sh` 管理软链接。** 手动修改链接可能导致注册状态、用户级发现机制与 README 元数据不一致。使用管理脚本执行 `setup`、`add`、`add-custom` 和 `remove`。

3. **手动编辑生成的 README 技能表。** `BEGIN SKILL LIST` 与 `END SKILL LIST` 之间的部分派生自已注册链接和 `SKILL.md` 元数据。使用 `update-readme` 刷新，再用 `check` 验证链接健康状态。

4. **将 `.tiga/` 当作权威项目内容。** `.tiga/` 是用户本地文件的 git 忽略入口：Agent 生成的计划和草稿应放在 `.tiga/agent-res/markdown/`，个人计划应放在 `.tiga/Todo.md`，后续本地模块可与它们并列存放。只有在用户明确要求时，才将其中内容提升到正式项目目录。

5. **使用旧目录布局。** 当前仓库使用 `01-prompts/`、`02-agent-skills/`、`03-custom-skills/` 和 `04-scripts/`。不要重新引入已移除的目录，例如 `00-skill-index/`、`03-workflows/` 或 `05-custom-skills/`。

## 常用命令

```bash
./04-scripts/manage-skills.sh setup
./04-scripts/manage-skills.sh add <path> [--name <name>]
./04-scripts/manage-skills.sh add-custom <name>
./04-scripts/manage-skills.sh remove <name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh check
./04-scripts/manage-skills.sh update-readme
```
