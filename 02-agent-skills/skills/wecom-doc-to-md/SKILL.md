---
name: wecom-doc-to-md
description: >-
  Extract content and metadata from Enterprise WeChat (WeCom / 企微) document
  links and generate Markdown. Triggers on doc.weixin.qq.com or docs.qq.com
  URLs — even when the user pastes a link without explanation — or when the
  user asks to extract, convert, or summarize a WeCom / 企微文档.
agents:
  - claude
  - codex
---

# WeCom Doc to Markdown

Turn Enterprise WeChat / WeCom document links into Markdown artifacts while preserving access-control integrity.

## Core Rules

### Access Control

- Never bypass access controls, automate login, inspect browser cookies, or use local authenticated browser state unless the user explicitly provides an exported file or authorized content.
- Never fabricate document body text. If the body is not accessible, generate a status Markdown from verifiable metadata only.

### Output Rules

- Write user-facing summaries and generated Markdown in Simplified Chinese unless project instructions say otherwise.
- Do not mix public search results or same-title sources into the extraction unless the user explicitly asks for public-source supplementation. If requested, label public content separately from WeCom content.
- Follow the current project's `AGENTS.md`, `CLAUDE.md`, and local file placement rules before writing output.

## Inputs

One or more URLs matching:

- `https://doc.weixin.qq.com/...`
- `https://docs.qq.com/...`

Preserve the full URL including query parameters (`scode`, `k`, `docid`, `id`, etc.). Process each link independently — one Markdown file per document — unless the user asks for a combined file.

## Probe Workflow

### Step 1 — Run the probe script

```bash
python <path-to-this-skill>/scripts/probe-wecom-doc.py '<url>' --json
```

> The script lives inside this skill's directory. Use `find` or check the
> skill symlink to resolve the absolute path before running.

> If the command fails due to sandbox network restrictions, re-run with the
> required approval mechanism available in the current environment.

### Step 2 — Interpret the result

| `access_status` | Meaning | Next step |
|---|---|---|
| `readable` | Body content is directly accessible | Go to **Readable Document Template** |
| `permission_required` | Requires login or share permissions | Go to **Restricted Document Template** |
| `login_required` | Requires authenticated session | Go to **Restricted Document Template** |
| `unknown` | Probe could not determine status | Report uncertainty, include probe notes, go to **Restricted Document Template** |

### Step 3 — Generate Markdown

Choose the template matching the access status and write the output file.

## Markdown Output Path

Default (title available):

```text
agent-plan/YYYY-MM-DD_<sanitized-title>.md
```

Fallback (title unavailable):

```text
agent-plan/YYYY-MM-DD_wecom-doc-extraction.md
```

Use kebab-case for the filename suffix. For Chinese-only titles, choose a short descriptive English slug based on meaning, e.g. `self-renovation-carpentry-guide`.

## Readable Document Template

When the body is directly accessible, generate a complete Chinese Markdown file:

```markdown
# <document title>

## 来源与提取状态

- 企微文档链接：<url>
- 文档 ID：<doc_id or unknown>
- 文档标题：<title>
- 所属企业：<corp_name or unknown>
- 当前访问状态：可读取
- 内容来源：<WeCom 链接直接提取 / 用户提供的导出文件 / 其他经用户授权的来源>

## 核心结论

- <3-5 条关键要点，每条一句话概括>

## 详细内容

### <原文第一节标题>

<分节提取内容，保留原文标题层级结构>

### <原文第二节标题>

...

## 待办事项

- [ ] <从文档中提取的行动项>
- [ ] ...

> 如文档中无明确待办事项，注明"文档中未包含明确待办事项"。

## 待确认问题

- <需要用户确认或补充的内容>

> 如无待确认问题，注明"无待确认问题"。
```

## Restricted Document Template

When the body is not accessible, generate a Chinese Markdown file with only verifiable information:

```markdown
# <document title or "企微文档提取记录">

## 来源与提取状态

- 企微文档链接：<url>
- 文档 ID：<doc_id or unknown>
- 访问码：<scode/k or unknown>
- 文档标题：<title or unknown>
- 所属企业：<corp_name or unknown>
- 文件大小：<file_size or unknown>
- 当前访问状态：<access_status>

> 说明：当前环境无法读取企微正文。本文只记录可验证元数据和后续补全方式，不包含原文提取内容。

## 未能提取正文的原因

- <probe note or permission/login reason>

## 后续补全方式

1. 提供有权限账号导出的 Word、PDF、HTML 或纯文本内容。
2. 将企微文档权限调整为当前环境可访问后重新运行提取。
3. 如果允许使用公开资料补充，请明确说明"可使用公开来源补充"。
```

## Final Response

1. 输出的 Markdown 文件路径
2. 是否成功提取了企微文档正文
3. 实际执行的探测命令
4. 剩余限制（如权限要求、登录要求等）
