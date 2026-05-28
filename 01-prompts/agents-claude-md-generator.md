# AGENTS.md / CLAUDE.md 架构生成 Prompt

> 分析仓库结构，自动生成 AGENTS.md、根级 CLAUDE.md 及子目录 CLAUDE.md 治理文件。

---

## Prompt 内容

### 你的任务

分析当前仓库，生成以下治理文件：

1. **`AGENTS.md`** — 仓库级操作规则（结构、权威源、边界、优先级）
2. **根级 `CLAUDE.md`** — 架构决策的 WHY、常见陷阱、Agent 协作规则
3. **子目录 `CLAUDE.md`** — 每个需要独立所有权语义的目录一份

每个文件以代码块输出，标注文件路径（如 `` ```markdown <!-- path: AGENTS.md --> ``）。

---

### Phase 1：仓库分析

在生成任何文件之前，先完成以下分析并输出分析摘要：

#### 1.1 目录与文件扫描

- 列出前两层目录结构
- 阅读 README、现有 CLAUDE.md / AGENTS.md / .cursor/rules 等配置文件
- 阅读核心模块的入口文件，理解项目类型（应用 / 库 / 内容仓库 / monorepo）

#### 1.2 功能分层识别

回答以下问题（写入分析摘要）：

- 仓库有几个功能层？各层职责是什么？
- 层与层之间有什么数据流方向或依赖关系？
- 各层的「所有权语义」是什么？（谁写、谁读、内容是否稳定、修改是否需要审批）
- 是否有目录承担 scratch / 临时 / 生成 的角色？

#### 1.3 子目录 CLAUDE.md 判定

对每个一级目录判断是否需要独立 CLAUDE.md，标准：

- **需要**：该目录有「不同于根级的所有权语义」——例如：内容稳定度不同、修改需要不同级别的审批、读写规则有本质区别
- **不需要**：纯工具目录、临时目录、构建产物、或规则与根级无差异

---

### Phase 2：生成 AGENTS.md

按以下模板结构生成，每个 section 的内容必须针对当前仓库定制：

```markdown
# [仓库标题 — 一行定位]

[一段话描述仓库用途、技术栈、核心约束。]

## Repository Structure

| Directory | Layer | Purpose |
|-----------|-------|---------|
| `dir/` | LayerName | 一行描述 |

[为每个一级目录填写。如果仓库无明确分层，Layer 列可改为 Role 或 Type。]
[注明"各内容目录有自己的 CLAUDE.md"——如果确实生成了子目录 CLAUDE.md。]

## Source-of-Truth Rules

[列出每个内容目录的权威性。格式：]
[- `dir/` is the primary source for ...]
[- `dir/` is generated/derived content and must not be treated as authoritative]
[确保覆盖所有内容目录，无遗漏。]

## Working Rules

[3-6 条通用操作准则。示例方向：]
[- 事实准确性要求]
[- 编辑风格偏好（精简改动 vs 全面重写）]
[- 依赖管理 / 测试要求（如适用）]
[- 保持现有风格 / API 的要求（如适用）]

## Markdown Generation

[默认规则——大多数项目可直接使用，视需要调整：]

- Create Markdown files only when explicitly requested.
- Save generated Markdown under `agent-plan/` unless the user specifies a path.
- Name generated Markdown files as `YYYY-MM-DD_{purpose}.md`.
- Create `agent-plan/` if it does not exist.
- Exceptions: translations stay next to the source file; project files such as `CLAUDE.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md` stay at their conventional locations.

## Boundaries

**Always:**
[列出 Agent 必须始终遵守的行为，3-5 条]

**Ask First:**
[列出需要用户确认才能执行的操作，3-5 条]
[重点：创建/删除文件、修改核心配置、改变公共 API、跨层内容迁移]

**Never:**
[列出绝对禁止的操作，3-5 条]
[重点：捏造内容、绕过测试、泄露凭证、反向数据流]

## Instruction Priority

When instructions conflict, follow this order of precedence:

1. Explicit user instructions
2. Sub-directory `CLAUDE.md` rules for the layer being edited
3. Repository constraints in this file (`AGENTS.md`)
4. [第 4-6 级根据项目特点填写，示例：]
5. [Evidence in source-of-truth directories]
6. [Existing wording/style in source materials]
7. [Generated content in output directories]
```

---

### Phase 3：生成根级 CLAUDE.md

```markdown
@AGENTS.md

## Architecture Decisions

[为仓库中每个关键设计决策写一段，格式：]
[**决策名称：** 解释 WHY — 不是描述结构是什么，而是为什么这样设计。]
[至少覆盖：目录组织方式、分文件/分目录策略、如有子目录 CLAUDE.md 则解释为什么需要分层规则]

## Common Gotchas

[列举 3-5 个新手（包括 AI）容易踩的坑，格式：]
[1. **简短标题。** 展开说明为什么这是个坑，以及正确做法。]
[重点方向：层间边界混淆、权威源误用、隐式数据回流、规则继承遗漏]

## Agent Collaboration Rules

[根据仓库特点写 3-5 条 Agent 协作规则，覆盖：]
[- Plan mode 使用条件（什么时候必须用 plan mode）]
[- 子目录 CLAUDE.md 继承：Agent 操作子目录文件时必须读取并遵守该目录的 CLAUDE.md]
[- agent-plan 目录用途（如使用了 Markdown Generation 默认规则）]
[- 其他项目特有的协作约束]
```

---

### Phase 4：生成子目录 CLAUDE.md

对每个在 Phase 1.3 中判定为「需要」的目录，生成一份 CLAUDE.md：

```markdown
# [Layer Name] Layer Rules

[一段话描述该目录的职责和所有权语义。]

## File Structure

| File/Directory | Purpose |
|----------------|---------|
| `name` | 一行描述 |

[列出当前已有的文件/子目录。]

## Read Rules

[2-4 条该层内容的阅读/引用规则]
[重点：内容的权威性级别、引用时的注意事项]

## Write Rules

[3-5 条该层内容的修改规则]
[重点：该层特有的约束——什么不能编造、什么需要确认、修改顺序、格式要求]

## File Format Standards

[如果该目录下的文件有统一格式，为每种文件类型定义：]

### [File type name]

**Structure:**
[用代码块展示文件骨架]

**Constraints:**
[3-5 条格式约束]
```

---

### 质量检查

生成所有文件后，执行以下检查并报告结果：

- [ ] **无内容重复**：AGENTS.md 和 CLAUDE.md 之间没有描述同一件事的段落（AGENTS.md 说 WHAT/规则，CLAUDE.md 说 WHY/陷阱）
- [ ] **Source-of-Truth 完整性**：所有内容目录都在 Source-of-Truth Rules 中有对应条目
- [ ] **Boundaries 覆盖危险操作**：Never 段包含了该仓库最关键的禁止操作
- [ ] **子目录 Write Rules 特异性**：每个子目录 CLAUDE.md 的 Write Rules 包含至少一条根级规则中没有的、该层特有的约束
- [ ] **Instruction Priority 一致性**：子目录规则 > 根级规则的继承关系在 AGENTS.md 和 CLAUDE.md 中都有体现
- [ ] **无凭空发明**：所有规则都基于仓库实际结构和代码推导，没有套用不存在的模式

---

### 注意事项

- 先分析，后生成。Phase 1 的分析摘要是后续所有文件的基础，不要跳过。
- 如果仓库结构简单（如只有 `src/` + `tests/`），AGENTS.md 可以更精简，不需要强行填满每个 section。
- 子目录 CLAUDE.md 不是越多越好——只在所有权语义确实不同时才创建。
- Markdown Generation 规则是默认值，如果目标项目有自己的文件生成约定，替换即可。

## 使用示例

将此 Prompt 完整粘贴给 AI，在目标项目根目录下执行。AI 将按照 Phase 1-4 的顺序：

1. 分析仓库结构，输出分析摘要
2. 生成 `AGENTS.md`
3. 生成根级 `CLAUDE.md`
4. 按需生成子目录 `CLAUDE.md`
5. 执行质量检查并报告结果
