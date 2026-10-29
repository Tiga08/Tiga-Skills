---
name: tiga-skills
description: Manage the Tiga-Skills library at ~/Projects/Tiga/Skills — install user- and project-level skill links from skills.toml, add or remove skills, review and adopt upstream updates of vendored external skills, and discover new skills from the watch list. Use when the user wants to add, remove, install, update, check, or find skills, or install a skill into a project.
---

# Tiga-Skills 管理

仓库位于 `~/Projects/Tiga/Skills`，以下命令都在仓库根目录执行。

- `skills.toml`：唯一权威来源，记录有哪些 skill、装到哪里、外部 skill 的来源。
- `skills/<name>/`：每个 skill 的实际文件；外部 skill 是锁定版本的副本。
- `skills.lock.json`：外部 skill 锁定的上游 commit，由脚本写入。

确定性操作一律交给脚本：

```bash
python3 skills/tiga-skills/scripts/skills.py install           # 按清单创建、修复、清理链接，刷新 README 清单
python3 skills/tiga-skills/scripts/skills.py check             # 只读检查，有问题时退出码为 1
python3 skills/tiga-skills/scripts/skills.py update [name...]  # 预览外部 skill 的上游变化
python3 skills/tiga-skills/scripts/skills.py update [name...] --apply
```

安装位置：`user` 链接到 `~/.claude/skills/<name>`（Claude Code）与 `~/.agents/skills/<name>`（Codex）；`project:<路径>` 链接到 `<路径>/.agents/skills/<name>`，缺失时创建 `<路径>/.claude/skills -> ../.agents/skills`。脚本只改动指向本仓库 `skills/` 的链接，目标位置被其他内容占用时报错并跳过。

每个流程结束前运行 `check`，把结果如实告诉用户。

## 新增自写 skill

1. 在 `skills/<name>/` 写 `SKILL.md`，`name` 与目录名一致。
2. 在 `skills.toml` 添加 `[skills.<name>]`，填写 `zh` 与 `targets`。
3. 运行 `install`、`check`。

## 引入外部 skill

1. 找到上游仓库与 skill 目录，阅读它的 `SKILL.md` 与仓库许可证。确认它自包含：不引用目录之外的文件；若它调用其他 skill（例如 "Call the Skill tool with ..."），把依赖一并引入并告诉用户。
2. 在 `skills.toml` 添加条目：`upstream = { repo = "<git URL>", path = "<仓库内目录>" }`。
3. 运行 `update <name>` 预览，再运行 `update <name> --apply` 引入。目录内没有许可证时，脚本会复制仓库根目录的许可证。
4. 运行 `install`、`check`。

## 安装到项目

在条目的 `targets` 中加入 `"project:~/Projects/<项目>"`，运行 `install`。项目里生成的是相对链接，只在本机有效；是否在该项目仓库中提交这些链接，先问用户。

## 移除 skill

删除 `skills.toml` 中的条目、`skills/<name>/` 目录，以及 `skills.lock.json` 中的同名项（如有），再运行 `install` 清理链接。若有其他 skill 依赖它，先告诉用户。

## 审查上游更新

1. 运行 `update`（不带 `--apply`），阅读每个 skill 的 diff。
2. 逐个向用户概括：行为有何变化；是否新增脚本、外部命令、网络访问或权限要求；是否新增对其他 skill 的依赖；给出是否采纳的建议。
3. 用户同意后运行 `update <name> --apply`，再运行 `install`（刷新 README 中的 commit）与 `check`。

本地改过的外部 skill 会被 `--apply` 拒绝，此时做三方合并。上游缓存位于 `.tiga/cache/` 下以仓库 URL 命名的目录：

- 基线：`git -C <缓存目录> show <锁定 commit>:<path>/<文件>`
- 上游：`git -C <缓存目录> show origin/HEAD:<path>/<文件>`
- 本地：`skills/<name>/` 中的当前文件

把上游变化合入本地文件并保留本地修改，然后把 `skills.lock.json` 中该项改为 `git -C <缓存目录> rev-parse origin/HEAD` 的结果，最后运行 `update <name>` 确认显示「已是最新」。

## 发现新 skill

1. 从 `skills.toml` 的 `[watch].repos` 选候选仓库；用户另给的仓库同样适用。
2. 浅克隆到 `.tiga/cache/discover/`：`git clone --depth 1 --filter=blob:none <url> .tiga/cache/discover/<仓库名>`。
3. 检索其中各 `SKILL.md` 的 `name` 与 `description`，按用户需求推荐少量候选，说明用途、依赖、是否自包含、与已有 skill 是否重叠。
4. 用户选定后，按「引入外部 skill」处理。
