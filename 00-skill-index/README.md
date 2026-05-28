# 能力索引

所有 Prompt、Skill、工作流和脚本的统一索引。

## Prompts

| 名称 | 说明 | 路径 |
|------|------|------|
| agents-claude-md-generator | 分析仓库结构，生成 AGENTS.md / CLAUDE.md 治理文件 | `01-prompts/agents-claude-md-generator.md` |

## Agent Skills

| 名称 | 说明 | 上游仓库 |
|------|------|----------|
| baoyu-format-markdown | 格式化纯文本或 Markdown 文件，自动添加 frontmatter、标题、摘要、层级标题、粗体、列表和代码块 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) |
| baoyu-markdown-to-html | 将 Markdown 转换为带样式的 HTML，支持微信兼容主题、代码高亮、数学公式、PlantUML、脚注、提示框和外链转底部引用 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) |
| baoyu-url-to-markdown | 通过 baoyu-fetch CLI（Chrome CDP + 站点适配器）抓取任意 URL 并转换为 Markdown，内置 X/Twitter、YouTube 字幕、Hacker News 等适配器 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) |

## 自定义 Skills

| 名称 | 说明 |
|------|------|
| md-to-zh | Translate English Markdown files into Simplified Chinese (.zh.md) |
| sync-upstream | Sync imported skills from upstream GitHub repositories — check for updates, pull changes, and refresh local copies |

## 工作流

| 名称 | 说明 | 路径 |
|------|------|------|
| — | 暂无 | — |

## 脚本

| 名称 | 说明 | 路径 |
|------|------|------|
| link-skills.sh | 将 Skills 逐个链接到本机 agent 配置目录 | `04-scripts/link-skills.sh` |
| manage-skills.sh | 管理外部 Skill 的导入、移除、查询和更新 | `04-scripts/manage-skills.sh` |
| sync-index.sh | 同步自定义 Skills 到能力索引 | `04-scripts/sync-index.sh` |
| sync-upstream.sh | 从上游 GitHub 仓库同步已导入的 Skills | `04-scripts/sync-upstream.sh` |
