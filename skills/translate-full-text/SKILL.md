---
name: translate-full-text
description: 把外文原版书或论文（PDF、EPUB）完整译成中文 Markdown 译文，保留图片、表格、公式和脚注，写入知识库条目。
argument-hint: <原版文件路径> [只试译的章节]
disable-model-invocation: true
---

# 全文翻译

把一本外文原版书或一篇论文完整译成中文，作为**译文**附在该书的读书笔记或该论文的论文笔记条目下。用语（译文、原版、出版社译本、翻译术语表）以仓库的 `GLOSSARY.md` 为准，条目和目录规则以 `AGENTS.md` 为准。你负责判断：分块、校对原文、翻译、统一术语；切分、拼接、检查、写入交给 `scripts/`。

## 约定

- 在仓库根目录运行。`S=.agents/skills/translate-full-text/scripts`，脚本一律用 `python3 $S/<脚本>.py …` 运行，PATH 上的 `python3` 要装有 docling（本机是 conda 环境 `files`）。各脚本的用法写在文件头。
- 工作区 `W=.tiga/translations/<slug>/`，`slug` 就是条目目录名：书用英文 kebab-case 书名，论文用 `年份-短名`。`.tiga/` 已被 git 忽略，原版内容只放在工作区里。

  | 路径 | 内容 |
  | --- | --- |
  | `source.md`、`images/`、`outline.txt`、`extract.json` | `extract.py` 的输出 |
  | `pages/` | 校对时渲染的 PDF 原页 |
  | `plan.md` | 计划：类型、条目目录、README 信息、版式写法、本书特有约定、试译块号 |
  | `chunks.txt` | 分块计划 |
  | `chunks/NNN.src.md` | 原文块，校对时直接修改 |
  | `chunks/NNN.zh.md` | 译文块 |
  | `chunks/NNN.terms.md` | 子 agent 提议的新术语 |
  | `header.md`、`terms.md` | 题头、翻译术语表 |
  | `translation.md`、`check.log` | 拼接结果、最近一次检查的输出 |

- 中断后从工作区里已有的文件接着做：先读 `plan.md`；`--chunk` 检查通过的块不重译，没通过的接着译。
- 翻译约定见 [references/translation-rules.md](references/translation-rules.md)。主会话和每个子 agent 都按它翻译。

## 流程

1. **提取**：运行 `python3 $S/extract.py <原版> $W`。PDF 每页约 2 秒，700 页的书约 20 分钟；超过 100 页时用 `caffeinate -i` 包住，并把输出写进 `$W/extract.log`。
   退出码 2 表示原版是中文，把原因告诉用户后停止。
   完成标准：`source.md` 已生成，提取统计已读过。
2. **定计划**：读 `extract.json`、`outline.txt` 和 `source.md` 的开头，把以下内容写进 `$W/plan.md`（分块计划单独写在 `chunks.txt`）：
   - 类型：书，对应读书笔记；论文，对应论文笔记。
   - 条目目录：按 `AGENTS.md`「目录」一节，定为 `领域/主题/[子主题/]books|papers/<slug>/`。拿不准归类时，在计划里列出候选。
   - 入口 README 要填的信息：书名或论文标题、作者、年份或版本、`source`（ISBN、DOI 或 arXiv URL）。这些只从原版的文本和元数据里找，找不到的写「缺失」，不联网查。
   - 分块计划 `$W/chunks.txt`，格式见 `chunks.py` 文件头：
     - 参考文献和书目用 `keep`；版权页、索引、带页码的目录页，以及由题头代替的标题和作者块用 `skip`；前言、致谢、附录和尾注都用 `translate`。
     - 论文不按章拆，只按上面的动作分段。
     - 书按章分块，每块原文不超过约 6000 个英文词，章太长就在节标题处再切。
   - 子 agent 数：书的每个 `translate` 块派一个子 agent，同时最多跑 4 个。论文由主会话自己译。
   - 书的版式写法：先看几页有代表性的原页，再定全书统一的写法。要定的有：原书各级标题分别对应几级 `#`（按字号、颜色区分）、章号和部分号怎么写，以及原书特有的版式元素（提示框、原则框、引文框等）怎么写。各子 agent 并行工作，看不到彼此的决定，只能从 `plan.md` 读到同一套写法。
   - 本书特有约定：用户确认计划时、看过试译稿后提的修改意见，都记在这一节。
   - 条目目录里已有 `translation.md` 时，在计划里标出来。这种情况下不会覆盖，由用户决定怎么处理。

   **确认点**：把 `plan.md` 和 `chunks.txt` 交给用户确认，确认后才继续。用户只要求试译某几章时，把对应的块号记进 `plan.md`。
   完成标准：用户确认了计划，修改意见已写回 `plan.md`。
3. **分块**：运行 `python3 $S/chunks.py split $W`。
4. **定翻译术语表**：书读目录、前言和一个样章，论文读全文。把核心概念、人名和反复出现的专有名词写进 `$W/terms.md`，格式见翻译约定。
   完成标准：书的各章标题里的概念词、论文的方法名和核心概念都有定译。
5. **校对原文块**：按翻译约定的「校对原文块」一节，对照原版修正提取错误，直接改 `NNN.src.md`。论文由主会话校对；书由各子 agent 在翻译自己的块之前校对。
   完成标准：块里没有公式占位符，标题层级、段落、图片、表格和公式的顺序都与原版一致；`check.py` 对这一块给出的校对提醒（少了图片、少了词数）每条都有说明。
6. **翻译**：
   - `keep` 块（论文和书都一样）：`cp $W/chunks/NNN.src.md $W/chunks/NNN.zh.md`，主会话只把标题行译成中文。
   - 论文：主会话逐块翻译，写成 `NNN.zh.md`，每块都要让 `python3 $S/check.py $W --chunk NNN` 通过。内容长时分节写：先用 Write 写开头一节，后面的节逐节追加。
   - 书：按下面的「子 agent 任务」派发，子 agent 沿用主会话模型。`--chunk` 检查没通过的块，带着检查输出重新派发。全部通过后，把各 `NNN.terms.md` 的提议合并进 `terms.md`；同一个词有冲突的译法时，定下一个，再回到相关的块统一改过来。
   - 试译：只做 `plan.md` 里记的块，然后直接跳到第 9 步汇报，不拼接，也不写入条目。

   完成标准：每个 `translate`/`keep` 块都有 `NNN.zh.md`，并且各自的 `--chunk` 检查通过。
7. **统一和拼接**：
   - 对 `terms.md` 里的每个术语，列出它可能被译成的其他中文说法（近义词、旧译），用 Grep 在所有 `NNN.zh.md` 里查，有就统一。
   - 按翻译约定写 `$W/header.md`。
   - 运行 `python3 $S/chunks.py join $W`，再运行 `python3 $S/check.py $W | tee $W/check.log`。有错误就改对应的块，重新拼接再检查。提醒要逐条看，修掉或确认没问题。

   完成标准：检查通过，每条提醒都有结论。
8. **写入条目**：条目目录和 README 信息取自 `plan.md`。运行 `python3 $S/publish.py $W <条目目录>`。它会再检查一次，条目里已有 `translation.md` 时拒绝写入。然后写入口 `README.md`：
   - 按 `AGENTS.md`「条目」一节写 frontmatter 和该类型的最低要求；
   - 格式照现有条目：书参照 `humanities/art/books/the-creative-act/README.md`，论文参照 `ai/computer-vision/papers/2018-yolov3/README.md`。H1 写「中文名（原名）」，下面列作者，以及版本（书）或会议、期刊、年份（论文，译自 arXiv 时注明版本号），最后一行是 `- 译文：[translation.md](translation.md)（本人翻译）`；
   - 条目已有 README 时，只补上译文这一行。

   完成标准：条目目录里有 `README.md`、`translation.md` 和 `images/`（原文有图时），README 里的相对链接都指向存在的文件。
9. **汇报**：
   - 条目路径，或试译稿在工作区里的路径；
   - 规模：原文英文词数、译文字数，以及图片、表格、公式的数量；
   - `check.log` 的路径和重跑命令，以及每条提醒是怎么处理的；
   - 计划里标「缺失」的信息；
   - 没做的事，比如试译只做了哪几块。

   不提交 git。

## 子 agent 任务

派发时，提示里要写明：

- 工作区、脚本目录和翻译约定的绝对路径，块号 `NNN`，原版文件路径，以及这一块的页码范围；
- 先读翻译约定、`plan.md`（版式写法和本书特有约定）和 `terms.md`；
- 按翻译约定的「校对原文块」一节校对 `chunks/NNN.src.md`，再译成 `chunks/NNN.zh.md`。内容长时分节写入。
- 不改 `terms.md` 和其他块；新出现的术语写进 `chunks/NNN.terms.md`；
- 交稿前 `python3 <脚本目录>/check.py <工作区> --chunk NNN` 必须通过；
- 回报四项：检查结果、校对改了哪些地方（检查给出的校对提醒逐条说明：每张去掉的图片换成了什么，少掉的文字是什么）、新术语、拿不准的译法。
