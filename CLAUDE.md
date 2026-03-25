# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库用途

`tiga-skills` 是一个用于备份和管理个人 Claude Code Skills 的仓库。Skills 按插件名分组存放，`README.md` 由脚本自动生成，**勿手动编辑**。

## 常用命令

手动重新生成 README.md：
```bash
bash scripts/update-readme.sh
```

## 架构说明

### Skills 存放规范

```
skills/
  {plugin-name}/        # 插件名（如 superpowers、commit-commands）
    {skill-name}/       # skill 名（kebab-case）
      SKILL.md          # skill 主文档，必须包含 YAML frontmatter
```

每个 `SKILL.md` 必须有 YAML frontmatter，至少包含 `name` 和 `description`：
```yaml
---
name: skill-name
description: 一句话描述该 skill 的用途
---
```

### 自动化机制

`.claude/settings.json` 中配置了 PostToolUse hooks：
- **Write hook**：当写入 `skills/` 下的文件后，自动触发 `hook-skill-change.sh`
- **Bash hook**：当执行涉及 `skills/` 路径的 bash 命令（如删除）后，同样触发

`hook-skill-change.sh` 解析 hook 事件 JSON（从 stdin），检查操作是否与 `skills/` 相关，若是则调用 `update-readme.sh`。

`update-readme.py` 是核心脚本，扫描所有 `skills/*/*/SKILL.md`，解析 frontmatter，按插件分组生成 `README.md`。

### 与 Claude Code 插件系统的关系

Skills 在 Claude Code 中实际存储于：
```
~/.claude/plugins/cache/{publisher}/{plugin-name}/{version}/skills/{skill-name}/
```

此仓库作为独立备份，不直接被 Claude Code 加载。恢复时需手动复制到上述路径并在 `~/.claude/settings.json` 中启用对应插件。
