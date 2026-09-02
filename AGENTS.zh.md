# Tiga-Skills: 集中式 Agent Skills 仓库

Tiga-Skills 注册外部和自定义 Agent Skills，并将它们暴露给 Claude Code 和 Codex。仓库存放内容、Bash 和仅使用标准库的 Python 工具，不含应用代码、构建系统或需通过包管理器安装的运行时依赖。核心约束是：`03-skills/` 是统一技能目录（自定义技能为真实目录，外部技能为符号链接），所有注册与移除一律经由 `./02-scripts/manage-skills.sh`。

## 结构

| 路径 | 用途 | 权属 |
| --- | --- | --- |
| `.agents/skills/` | 操作本仓库的项目级技能；`.claude/skills` 和 `.codex/skills` 都是指向它的符号链接，因此各 agent 共用同一份技能库 | primary |
| `03-skills/` | 统一技能目录 —— 自定义技能为真实目录，外部技能为符号链接 | primary |
| `descriptions-zh.conf` | 生成 README 技能列表所依据的权威中文描述 | primary |
| `SKILLS-INDEX.md` | 指向 `~/Projects/AG-Tools/SKILLS-INDEX.md` 的符号链接，即 AG-Tools 全仓库技能索引 | derived |
| `SKILLS-REFS.md` | 指向 `~/Projects/AG-Tools/SKILLS-REFS.md` 的符号链接，即下游引用清单 | derived |

表中只列用途或权属无法一望而知的路径，其余目录本身即可说明自己。已注册技能的成品清单见 `README.md`。

## 命令

```bash
./02-scripts/manage-skills.sh setup                      # 配置用户级符号链接
./02-scripts/manage-skills.sh add <path> [--name <name>] # 注册外部技能
./02-scripts/manage-skills.sh remove <name>              # 移除外部技能符号链接
./02-scripts/manage-skills.sh list
./02-scripts/manage-skills.sh check                      # 检查技能目录与 frontmatter 健康状态
./02-scripts/manage-skills.sh update-readme              # 重新生成 README 技能列表
```

对于 `$HOME` 下的路径，`add` 会写入用户可移植的相对符号链接（如 `../../../AG-Tools/...`）；所需的 checkout 布局见根目录 `README.md`。

## 边界

**始终：**

- 在源位置编辑技能：操作本仓库的项目级技能在 `.agents/skills/<name>/`，自定义技能在 `03-skills/<name>/`，外部技能在其各自的上游仓库。
- 注册、移除和用户级链接配置一律走 `./02-scripts/manage-skills.sh` —— 手工改动链接会让注册状态、用户级发现和 README 元数据彼此脱节。
- 让 `descriptions-zh.conf` 与各技能的实际行为保持一致；其中 `<name>.description` 是 README 技能表描述列的来源，`<name>.arguments` 则是技能缺少 `argument-hint` frontmatter 时参数列的兜底（外部技能的源文件不可编辑）。
- 任何注册、移除或 `descriptions-zh.conf` 变更之后，先运行 `update-readme`，再运行 `check`。
- 保持 `02-scripts/*.sh` 为 UTF-8 编码的可执行 Bash，并沿用既有的直接命令风格；修改任何 shell 脚本后运行 `bash -n`。Skill 自带的 Python 辅助工具通过 `python3` 调用，并遵循其所属 `SKILL.md` 的规则；仓库没有统一测试套件。

**先询问：**

- 创建或删除技能、prompt、脚本。
- 注册、移除或重命名技能。
- 从外部上游仓库拉取或注册内容 —— 先查看其状态。
- 创建子目录 `CLAUDE.md`；除非用户要求更窄范围的文件，否则本仓库有意只在根目录维护治理文件。

**绝不：**

- 修改经由 `03-skills/` 符号链接抵达的外部技能源文件；那些内容属于上游仓库。
- 手工在 `03-skills/` 下创建或删除符号链接，绕过 `manage-skills.sh`。
- 手工编辑 README 中 `<!-- BEGIN SKILL LIST -->` 与 `<!-- END SKILL LIST -->` 之间的区块。
- 编造技能名称、来源或描述。
- 重新引入已淘汰的顶层布局，例如 `00-skill-index/`、`02-agent-skills/`、`03-workflows/` 或 `05-custom-skills/`。
