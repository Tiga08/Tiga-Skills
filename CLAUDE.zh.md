@AGENTS.md

## 约束

- 脚本保持为 UTF-8 编码的可执行 Bash，沿用既有的直接命令风格。

## 常见陷阱

1. **默认 `02-agent-skills/` 里的条目属于本仓库。** 有的链接指向 `03-custom-skills/`，有的指向外部 AG-Tools fork，条目名本身看不出是哪一种。动手改之前，先把链接解析到真实目标。

2. **把 `.tiga/` 当作项目内容。** 该目录被 git 忽略，从来不是权威内容；个人计划放在 `.tiga/Todo.md`。只有用户明确要求时，才把其中内容提升到正式目录。

3. **沿用旧的目录布局。** 当前布局是 `01-prompts/`、`02-agent-skills/`、`03-custom-skills/`、`04-scripts/`。不要重新引入已移除的目录，例如 `00-skill-index/`、`03-workflows/`、`05-custom-skills/`。
