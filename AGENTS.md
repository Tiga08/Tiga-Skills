# Tiga-Skills

个人 Agent Skills 库：自写 skill 与精选外部 skill 的唯一来源，通过符号链接提供给 Claude Code 与 Codex。

## 结构

| 路径 | 用途 |
| --- | --- |
| `skills.toml` | 清单，唯一权威来源：有哪些 skill、装到哪里、外部 skill 的来源 |
| `skills.lock.json` | 外部 skill 锁定的上游 commit，由脚本写入 |
| `skills/<name>/` | 每个 skill 的实际文件；外部 skill 是锁定版本的副本 |
| `skills/tiga-skills/` | 管理本仓库的 skill，`scripts/skills.py` 是唯一的管理脚本 |
| `tests/` | 管理脚本的端到端测试 |
| `.tiga/` | 被 Git 忽略：安装记录、上游缓存与本地文件 |

## 命令

```bash
python3 skills/tiga-skills/scripts/skills.py install|check
python3 skills/tiga-skills/scripts/skills.py update [name...] [--apply]
python3 -m unittest discover -s tests -v
```

具体流程见 `skills/tiga-skills/SKILL.md`。

## 边界

**始终：**

- 增删 skill 或改变安装位置时，先改 `skills.toml`，再运行 `install`；结束前运行 `check`。
- 外部 skill 的更新先预览 diff、向用户说明变化，确认后再 `--apply`。
- 修改 `skills.py` 时先补端到端测试，再改实现，并跑完整测试。

**先询问：**

- 引入、移除 skill，或改变安装位置。
- 修改外部 skill 的本地副本（之后的更新需要三方合并）。
- 在其他项目仓库中提交 skill 链接的变化。

**绝不：**

- 手工创建或删除 `~/.claude/skills`、`~/.agents/skills` 与项目 `.agents/skills` 中指向本仓库的链接。
- 手工编辑 README 中 `<!-- BEGIN SKILL LIST -->` 与 `<!-- END SKILL LIST -->` 之间的内容。
- 手工修改 `skills.lock.json`，三方合并完成后更新 commit 除外。
- 捏造 skill 名称、来源、commit 或描述。
