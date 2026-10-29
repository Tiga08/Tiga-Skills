# Tiga-Skills

个人 Agent Skills 库：自写 skill 与精选外部 skill 集中在 `skills/`，由 `skills.toml` 统一描述，通过符号链接提供给 Claude Code 与 Codex 的用户级和项目级目录。

## 快速开始

需要 Python 3.11.4+ 与 git。

```bash
git clone git@github.com:Tiga08/Tiga-Skills.git ~/Projects/Tiga/Skills
cd ~/Projects/Tiga/Skills
python3 skills/tiga-skills/scripts/skills.py install   # 建立链接
python3 skills/tiga-skills/scripts/skills.py check     # 检查
```

之后在任意 agent 会话中让 `tiga-skills` 处理增删、更新与发现。

## Skill 清单

由 `install` 根据 `skills.toml` 生成。

<!-- BEGIN SKILL LIST -->
| 名称 | 来源 | 安装位置 | 描述 |
| --- | --- | --- | --- |
| domain-modeling | `mattpocock/skills` @ `59db609` | 用户级 | 构建并打磨项目的领域模型，维护 GLOSSARY.md 与 ADR；grill-with-docs 的依赖。 |
| grill-with-docs | `mattpocock/skills` @ `59db609` | 用户级 | 以追问方式打磨计划或设计，同时沉淀 ADR 与术语表；依赖 grilling 与 domain-modeling。 |
| grilling | `mattpocock/skills` @ `59db609` | 用户级 | 以设计树方式分轮追问计划、决策或想法，直到达成共同理解；grill-with-docs 的依赖。 |
| tiga-skills | 自写 | 用户级 | 管理本仓库：按清单安装用户级与项目级 skill，增删 skill，审查并采纳外部 skill 的上游更新，从关注列表发现新 skill。 |
| writing-for-agents | `mattpocock/skills` @ `59db609` | 用户级 | 编写供 Agent 读取的文档（skill、AGENTS.md、CLAUDE.md）的参考：上下文指针、信息层级、完成标准与精简。 |
<!-- END SKILL LIST -->

## 安装位置

| 目标 | 链接位置 |
| --- | --- |
| `user` | `~/.claude/skills/<name>`（Claude Code）、`~/.agents/skills/<name>`（Codex） |
| `project:<路径>` | `<路径>/.agents/skills/<name>`；缺失时创建 `<路径>/.claude/skills -> ../.agents/skills` |

## 外部 skill

外部 skill 以副本形式提交在 `skills/<name>/`，保留上游许可证，锁定的 commit 记录在 `skills.lock.json`。`update` 预览上游变化，确认后用 `update --apply` 采纳；本地改过的副本需要三方合并，流程见 `skills/tiga-skills/SKILL.md`。

## 测试

```bash
python3 -m unittest discover -s tests -v
```
