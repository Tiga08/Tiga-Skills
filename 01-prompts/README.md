# Prompt 库

存放可复用的 Prompt 模板，用于各类 Agent 任务。

## 用途

- 标准化常用操作的 Prompt
- 提供经过验证的 Prompt 模板供快速调用
- 作为新 Prompt 的参考起点

## 文件规范

- 文件名：kebab-case，如 `code-review.md`
- 编码：UTF-8
- 格式：Markdown
- 每个文件包含一个独立的 Prompt

## 文件结构

```markdown
# Prompt 标题

> 一句话说明用途

## Prompt 内容

（正文）

## 使用示例

（可选）
```

## 登记

添加新 Prompt 后，请在 [00-skill-index](../00-skill-index/README.md) 中登记。
