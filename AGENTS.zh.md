# Tiga-Skills: 集中式 Agent Skills 仓库

Tiga-Skills 通过扁平符号链接注册外部和自定义 Agent Skills，并将它们暴露给 Claude Code 和 Codex。仓库只存放内容与 Bash 脚本，没有应用代码、构建系统或运行时依赖。核心约束是：`02-agent-skills/` 是符号链接注册表，自定义技能源文件位于 `03-custom-skills/`，所有注册与移除一律经由 `./04-scripts/manage-skills.sh`。

## 结构

| 路径 | 用途 | 权属 |
| --- | --- | --- |
| `.agents/skills/` | 操作本仓库的项目级技能；`.claude/skills` 和 `.codex/skills` 都是指向它的符号链接，因此各 agent 共用同一份技能库 | primary |
| `02-agent-skills/` | 扁平注册表 —— 每个条目都是符号链接，绝无实体内容 | derived |
| `03-custom-skills/` | 上面所注册的自定义技能的源文件 | primary |
| `descriptions-zh.conf` | 生成 README 技能列表所依据的权威中文描述 | primary |
| `SKILLS-INDEX.md` | 指向 `~/Projects/AG-Tools/SKILLS-INDEX.md` 的符号链接，即 AG-Tools 全仓库技能索引 | derived |
| `SKILLS-REFS.md` | 指向 `~/Projects/AG-Tools/SKILLS-REFS.md` 的符号链接，即下游引用清单 | derived |

表中只列用途或权属无法一望而知的路径，其余目录本身即可说明自己。已注册技能的成品清单见 `README.md`。仓库只维护根目录的治理文件 —— 除非用户要求，不要创建子目录 `CLAUDE.md`。

## 命令

```bash
./04-scripts/manage-skills.sh setup                      # 配置用户级符号链接
./04-scripts/manage-skills.sh add <path> [--name <name>] # 注册外部技能
./04-scripts/manage-skills.sh add-custom <name>          # 注册来自 03-custom-skills/ 的技能
./04-scripts/manage-skills.sh remove <name>
./04-scripts/manage-skills.sh list
./04-scripts/manage-skills.sh check                      # 检查符号链接与 frontmatter 健康状态
./04-scripts/manage-skills.sh update-readme              # 重新生成 README 技能列表
```

对于 `$HOME` 下的路径，`add` 会写入用户可移植的相对符号链接（如 `../../../AG-Tools/...`），前提是本仓库位于 `~/Projects/Tiga/Skills`、AG-Tools 位于 `~/Projects/AG-Tools`。

## 边界

**始终：**

- 在源位置编辑技能：操作本仓库的项目级技能在 `.agents/skills/<name>/`，注册表技能在 `03-custom-skills/<name>/`，外部技能在其各自的上游仓库。
- 注册、移除和用户级链接配置一律走 `./04-scripts/manage-skills.sh` —— 手工改动链接会让注册状态、用户级发现和 README 元数据彼此脱节。
- 让 `descriptions-zh.conf` 与各技能的实际行为保持一致；其中 `<name>.description` 是 README 技能表描述列的来源，`<name>.arguments` 则是技能缺少 `argument-hint` frontmatter 时参数列的兜底（外部技能的源文件不可编辑）。
- 任何注册、移除或 `descriptions-zh.conf` 变更之后，先运行 `update-readme`，再运行 `check`。
- 修改任何 shell 脚本后运行 `bash -n` —— 本仓库没有测试套件。

**先询问：**

- 创建或删除技能、prompt、脚本。
- 注册、移除或重命名技能。
- 从外部上游仓库拉取或注册内容 —— 先查看其状态。

**绝不：**

- 修改经由 `02-agent-skills/` 符号链接抵达的外部技能源文件；那些内容属于上游仓库。
- 手工在 `02-agent-skills/` 下创建或删除符号链接，绕过 `manage-skills.sh`。
- 手工编辑 README 中 `<!-- BEGIN SKILL LIST -->` 与 `<!-- END SKILL LIST -->` 之间的区块。
- 编造技能名称、来源或描述。
