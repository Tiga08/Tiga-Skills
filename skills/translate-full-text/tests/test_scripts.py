"""translate-full-text 脚本测试。

在 Tiga-Skills 根目录运行：python3 -m unittest discover -s skills/translate-full-text/tests -v

每个用例在临时目录里搭工作区，用子进程调用真实脚本。EPUB 用例需要 pandoc。

覆盖的失败方式：
1. 译文漏图、漏表、丢标题、丢段落、丢公式、丢脚注定义，检查没有报错
2. 译文留着整段英文或英文标题没译，检查没有报错
3. 代码块被改动、「保留」块（参考文献）被改动，检查没有报错
4. 原文块或译文里残留未识别的公式占位符，检查没有报错
5. 某块没有译文、图片链接指向不存在的文件、translation.md 不是最新拼接结果、缺翻译术语表，检查没有报错
6. 合法的改写（管道表格改成 HTML 表格、中文里夹英文术语和型号）被误报
7. 分块计划没从第 1 行开始或行号不递增，导致有内容漏出分块
8. 重新分块覆盖了已经校对过的原文块
9. 拼接后的 translation.md 残留页码标记
10. 发布时覆盖已有 translation.md（可能有阅读标注）、检查不通过也写入、复制了未引用的图片
11. EPUB 提取后图片没有统一改名、超过 1MB 的图没有压缩、表格丢失、混入 div/span 等 HTML 噪声；
   脚注被集中到全书末尾（会被切进 skip 块）；公式没有输出成 $$；工作区用相对路径时图片引用失效
12. 原版是中文时没有拒绝；重复提取覆盖了已有工作区
13. docling 提取稿里的软连字符、列表的「- · 」前缀、&amp; 没有清掉
14. 括号里的作者-年份引用串、只有算法名的标题被误报为未翻译；公式、图片、代码的顺序变了没报错
15. 校对时看不清公式：render.py 不能放大、不能切条，也不导出文字层
16. 脚注的引用和定义被切在两块里（长章拆块），单块检查误报，子 agent 无法交稿；
   拼接后的悬空脚注、译文丢掉的脚注引用没报错；各块并行校对时都把页底脚注编成 [^1]，拼接后重号没报错
17. 校对原文块时删掉了内容或图片，检查没有提醒；删页眉页脚这类少量删减被误提醒
"""

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

SOURCE = r"""<!-- page 1 -->

## YOLOv3: An Incremental Improvement

Joseph Redmon Ali Farhadi University of Washington

## Abstract

We present some updates to YOLO! We made a bunch of little design changes to make it better. We also trained this new network that's pretty swell.

## 1. Introduction

Sometimes you just kinda phone it in for a year, you know? I didn't do a whole lot of research this year.

![Image](images/fig-001.png)

Figure 1. We adapt this figure from the Focal Loss paper [9].

<!-- page 2 -->

## 2. The Deal

| Backbone | Top-1 | FPS |
|---|---|---|
| Darknet-19 [15] | 74.1 | 171 |
| Darknet-53 | 77.2 | 78 |

Table 1. Comparison of backbones.

The bounding box center is predicted as follows:

$$
b_x = \sigma(t_x) + c_x
$$

We use sum of squared error loss during training [^1].

[^1]: This footnote explains the loss used during training.

```python
def identity(x):
    return x  # unchanged
```

## References

- [1] Analogy. Wikipedia, Mar 2018.
- [2] M. Everingham, L. Van Gool, C. K. Williams, J. Winn, and A. Zisserman. The pascal visual object classes (voc) challenge. 2010.
"""

ZH_BODY = r"""## 摘要

我们对 YOLO 做了一些更新！我们做了一堆小的设计改动，让它变得更好。我们还训练了一个相当不错的新网络。

## 1. 引言

有时候你就是会敷衍地过完一年，你懂的？今年我没做多少研究。

![Image](images/fig-001.png)

图 1：本图改编自 Focal Loss 论文 [9]。

<!-- page 2 -->

## 2. 方案

| 骨干网络（backbone） | Top-1 | FPS |
|---|---|---|
| Darknet-19 [15] | 74.1 | 171 |
| Darknet-53 | 77.2 | 78 |

表 1：骨干网络对比。

边界框中心按下式预测：

$$
b_x = \sigma(t_x) + c_x
$$

训练时我们使用误差平方和损失[^1]，并用 Darknet-53 替换了 Darknet-19 作为骨干网络。

[^1]: 这条脚注说明训练时使用的损失。

```python
def identity(x):
    return x  # unchanged
```
"""

ZH_REFS = """## 参考文献

- [1] Analogy. Wikipedia, Mar 2018.
- [2] M. Everingham, L. Van Gool, C. K. Williams, J. Winn, and A. Zisserman. The pascal visual object classes (voc) challenge. 2010.
"""

HEADER = "# YOLOv3：渐进式改进\n\nYOLOv3: An Incremental Improvement｜约瑟夫·雷德蒙（Joseph Redmon）、阿里·法哈迪（Ali Farhadi）\n"
TERMS = "## 翻译术语表\n\n| 原文 | 译法 | 说明 |\n|---|---|---|\n| backbone | 骨干网络 | |\n"

HTML_TABLE = """<table>
<tr><th>骨干网络（backbone）</th><th>Top-1</th><th>FPS</th></tr>
<tr><td>Darknet-19 [15]</td><td>74.1</td><td>171</td></tr>
<tr><td>Darknet-53</td><td>77.2</td><td>78</td></tr>
</table>"""

PIPE_TABLE = """| 骨干网络（backbone） | Top-1 | FPS |
|---|---|---|
| Darknet-19 [15] | 74.1 | 171 |
| Darknet-53 | 77.2 | 78 |"""

FORMULA = "$$\nb_x = \\sigma(t_x) + c_x\n$$"


def png(path, width, height, noisy=False):
    """写一张 RGB PNG；noisy 时用随机像素，压缩后仍然很大。"""
    row = width * 3
    raw = b"".join(b"\x00" + (os.urandom(row) if noisy else b"\x80" * row) for _ in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def run(script, *args, cwd=None):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout + p.stderr


class Workspace(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ws = self.tmp / "ws"

    def build(self, body=ZH_BODY, refs=ZH_REFS, header=HEADER, terms=TERMS, source=SOURCE, join=True):
        """搭一个论文工作区：写原文和分块计划、分块、写译文、拼接。"""
        ws = self.ws
        (ws / "images").mkdir(parents=True)
        png(ws / "images" / "fig-001.png", 4, 4)
        (ws / "source.md").write_text(source, encoding="utf-8")
        lines = source.splitlines()
        abstract = lines.index("## Abstract") + 1
        references = lines.index("## References") + 1
        (ws / "chunks.txt").write_text(
            f"1 skip 标题与作者（由题头代替）\n{abstract} translate 正文\n{references} keep 参考文献\n",
            encoding="utf-8",
        )
        code, out = run("chunks.py", "split", ws)
        self.assertEqual(code, 0, out)
        (ws / "chunks" / "002.zh.md").write_text(body, encoding="utf-8")
        (ws / "chunks" / "003.zh.md").write_text(refs, encoding="utf-8")
        (ws / "header.md").write_text(header, encoding="utf-8")
        (ws / "terms.md").write_text(terms, encoding="utf-8")
        if join:
            code, out = run("chunks.py", "join", ws)
            self.assertEqual(code, 0, out)
        return ws

    def check_fails(self, keyword, *args, **build_kwargs):
        ws = self.build(**build_kwargs)
        code, out = run("check.py", ws, *args)
        self.assertEqual(code, 1, out)
        self.assertIn(keyword, out)
        return out


class CheckTest(Workspace):
    def test_good_translation_passes(self):
        ws = self.build()
        code, out = run("check.py", ws)
        self.assertEqual(code, 0, out)

    def test_html_table_counts_as_table(self):
        ws = self.build(body=ZH_BODY.replace(PIPE_TABLE, HTML_TABLE))
        code, out = run("check.py", ws)
        self.assertEqual(code, 0, out)

    def test_missing_image(self):
        self.check_fails("图片", body=ZH_BODY.replace("![Image](images/fig-001.png)\n\n", ""))

    def test_missing_table(self):
        self.check_fails("表格", body=ZH_BODY.replace(PIPE_TABLE, "骨干网络对比见下文。"))

    def test_missing_heading(self):
        self.check_fails("标题", body=ZH_BODY.replace("## 2. 方案", "2. 方案"))

    def test_dropped_paragraph(self):
        self.check_fails("段落", body=ZH_BODY.replace("边界框中心按下式预测：\n\n", ""))

    def test_untranslated_paragraph(self):
        english = "Sometimes you just kinda phone it in for a year, you know? I didn't do a whole lot of research this year."
        self.check_fails("未翻译", body=ZH_BODY.replace("有时候你就是会敷衍地过完一年，你懂的？今年我没做多少研究。", english))

    def test_untranslated_heading(self):
        self.check_fails("未翻译", body=ZH_BODY.replace("## 2. 方案", "## 2. The Deal"))

    def test_missing_formula(self):
        self.check_fails("公式", body=ZH_BODY.replace(FORMULA, "见公式。"))

    def test_formula_placeholder_left_in_translation(self):
        self.check_fails("占位符", body=ZH_BODY.replace(FORMULA, "<!-- formula-not-decoded -->"))

    def test_formula_placeholder_left_in_source_chunk(self):
        source = SOURCE.replace(FORMULA, "<!-- formula-not-decoded -->")
        self.check_fails("占位符", source=source)

    def test_code_block_changed(self):
        self.check_fails("代码", body=ZH_BODY.replace("# unchanged", "# 原样返回"))

    def test_footnote_without_definition(self):
        self.check_fails("脚注", body=ZH_BODY.replace("[^1]: 这条脚注说明训练时使用的损失。\n\n", ""))

    def test_keep_chunk_modified(self):
        self.check_fails("保留", refs=ZH_REFS.replace("Analogy. Wikipedia", "类比。维基百科"))

    def test_keep_chunk_heading_untranslated(self):
        self.check_fails("未翻译", refs=ZH_REFS.replace("## 参考文献", "## References"))

    def test_missing_chunk_translation(self):
        ws = self.build()
        (ws / "chunks" / "002.zh.md").unlink()
        code, out = run("check.py", ws)
        self.assertEqual(code, 1, out)
        self.assertIn("002", out)

    def test_broken_image_link(self):
        ws = self.build()
        (ws / "images" / "fig-001.png").unlink()
        code, out = run("check.py", ws)
        self.assertEqual(code, 1, out)
        self.assertIn("不存在", out)

    def test_stale_translation(self):
        ws = self.build()
        zh = ws / "chunks" / "002.zh.md"
        zh.write_text(zh.read_text(encoding="utf-8").replace("相当不错", "很棒"), encoding="utf-8")
        code, out = run("check.py", ws)
        self.assertEqual(code, 1, out)
        self.assertIn("重新拼接", out)

    def test_missing_terms_section(self):
        self.check_fails("翻译术语表", terms="| 原文 | 译法 |\n|---|---|\n| backbone | 骨干网络 |\n")

    def test_single_chunk_mode_ignores_unassembled_parts(self):
        ws = self.build(join=False)
        (ws / "header.md").unlink()
        (ws / "chunks" / "003.zh.md").unlink()
        code, out = run("check.py", ws, "--chunk", "002")
        self.assertEqual(code, 0, out)

    def test_join_strips_page_markers(self):
        ws = self.build()
        text = (ws / "translation.md").read_text(encoding="utf-8")
        self.assertNotIn("<!-- page", text)
        self.assertTrue(text.startswith("# YOLOv3：渐进式改进"))
        self.assertIn("## 翻译术语表", text)


class CheckMiniTest(Workspace):
    """单块的小工作区，用来测误报和顺序。"""

    def mini(self, src, zh, original=None):
        """original 是提取出来的原文；不给时与校对后的原文块相同。"""
        ws = self.ws
        (ws / "chunks").mkdir(parents=True, exist_ok=True)
        (ws / "source.md").write_text(original or src, encoding="utf-8")
        (ws / "chunks.txt").write_text("1 translate 正文\n", encoding="utf-8")
        (ws / "chunks" / "001.src.md").write_text(src, encoding="utf-8")
        (ws / "chunks" / "001.zh.md").write_text(zh, encoding="utf-8")
        return run("check.py", ws, "--chunk", "001")

    def two_chunks(self, src1, src2, zh1, zh2):
        """两个 translate 块的工作区，拼接后返回整体检查的结果。"""
        ws = self.ws
        (ws / "chunks").mkdir(parents=True)
        (ws / "source.md").write_text(src1 + src2, encoding="utf-8")
        (ws / "chunks.txt").write_text(f"1 translate 上\n{src1.count(chr(10)) + 1} translate 下\n", encoding="utf-8")
        for num, src, zh in (("001", src1, zh1), ("002", src2, zh2)):
            (ws / "chunks" / f"{num}.src.md").write_text(src, encoding="utf-8")
            (ws / "chunks" / f"{num}.zh.md").write_text(zh, encoding="utf-8")
        (ws / "header.md").write_text(HEADER, encoding="utf-8")
        (ws / "terms.md").write_text(TERMS, encoding="utf-8")
        code, out = run("chunks.py", "join", ws)
        self.assertEqual(code, 0, out)
        return run("check.py", ws)

    def test_footnote_split_across_chunks_passes(self):
        src1, zh1 = "Loss is squared error [^1].\n\n", "损失是平方误差[^1]。\n\n"
        src2, zh2 = "More text here.\n\n[^1]: Explains the loss.\n", "更多文字。\n\n[^1]: 解释损失。\n"
        code, out = self.mini(src1, zh1)
        self.assertEqual(code, 0, out)
        shutil.rmtree(self.ws)
        code, out = self.two_chunks(src1, src2, zh1, zh2)
        self.assertEqual(code, 0, out)

    def test_dangling_footnote_after_join(self):
        code, out = self.two_chunks("Loss is squared error [^1].\n\n", "More text here.\n", "损失是平方误差[^1]。\n\n", "更多文字。\n")
        self.assertEqual(code, 1, out)
        self.assertIn("只有引用没有定义", out)

    def test_duplicate_footnote_ids_after_join(self):
        code, out = self.two_chunks(
            "Loss is squared error [^1].\n\n[^1]: Explains the loss.\n\n", "Goals matter [^1].\n\n[^1]: Explains goals.\n",
            "损失是平方误差[^1]。\n\n[^1]: 解释损失。\n\n", "目标很重要[^1]。\n\n[^1]: 解释目标。\n",
        )
        self.assertEqual(code, 1, out)
        self.assertIn("重复", out)

    def test_chunk_prefixed_footnote_ids_pass(self):
        code, out = self.two_chunks(
            "Loss is squared error [^001-1].\n\n[^001-1]: Explains the loss.\n\n", "Goals matter [^002-1].\n\n[^002-1]: Explains goals.\n",
            "损失是平方误差[^001-1]。\n\n[^001-1]: 解释损失。\n\n", "目标很重要[^002-1]。\n\n[^002-1]: 解释目标。\n",
        )
        self.assertEqual(code, 0, out)

    def test_dropped_footnote_reference(self):
        code, out = self.mini("Loss is squared error [^1].\n", "损失是平方误差。\n")
        self.assertEqual(code, 1, out)
        self.assertIn("脚注", out)

    PROOFREAD = "## Goals\n\n" + "Users have goals and designers must understand them well. " * 10 + "\n\n![Image](images/fig-001.png)\n\nAbout Face 17\n"

    def proofread(self, corrected):
        zh = "## 目标\n\n" + "用户有目标。" * 10 + "\n"
        if "![Image]" in corrected:
            zh += "\n![Image](images/fig-001.png)\n"
        if "About Face 17" in corrected:
            zh += "\nAbout Face 17\n"
        (self.ws / "images").mkdir(parents=True)
        png(self.ws / "images" / "fig-001.png", 4, 4)
        code, out = self.mini(corrected, zh, original=self.PROOFREAD)
        self.assertEqual(code, 0, out)
        return out

    def test_proofreading_dropped_words_warns(self):
        out = self.proofread("## Goals\n\n" + "Users have goals and designers must understand them well. " * 5 + "\n\n![Image](images/fig-001.png)\n")
        self.assertIn("提醒", out)
        self.assertIn("词数", out)

    def test_proofreading_dropped_image_warns(self):
        out = self.proofread(self.PROOFREAD.replace("![Image](images/fig-001.png)\n\n", ""))
        self.assertIn("提醒", out)
        self.assertIn("images/fig-001.png", out)

    def test_proofreading_page_footer_removed_is_quiet(self):
        out = self.proofread(self.PROOFREAD.replace("\n\nAbout Face 17", ""))
        self.assertNotIn("提醒", out)

    def test_author_year_citations_are_not_untranslated(self):
        cites = "(Deng et al., 2013; Krizhevsky et al., 2012; Hinton & Salakhutdinov, 2006; Hinton et al., 2012a; Graves et al., 2013)"
        code, out = self.mini(f"SGD has many success stories {cites}.\n", f"SGD 有很多成功案例 {cites}。\n")
        self.assertEqual(code, 0, out)

    def test_name_only_heading_is_not_untranslated(self):
        code, out = self.mini("## 7.1 ADAMAX\n\nIn Adam, the update rule scales the gradients.\n", "## 7.1 AdaMax\n\n在 Adam 中，更新规则会缩放梯度。\n")
        self.assertEqual(code, 0, out)

    def test_formula_order_changed(self):
        src = "First:\n\n$$\na = 1\n$$\n\nThen:\n\n$$\nb = 2\n$$\n"
        zh = "先：\n\n$$\nb = 2\n$$\n\n然后：\n\n$$\na = 1\n$$\n"
        code, out = self.mini(src, zh)
        self.assertEqual(code, 1, out)
        self.assertIn("顺序", out)


class SplitTest(Workspace):
    def prepare(self, plan):
        self.ws.mkdir()
        (self.ws / "source.md").write_text(SOURCE, encoding="utf-8")
        (self.ws / "chunks.txt").write_text(plan, encoding="utf-8")

    def test_plan_must_start_at_line_1(self):
        self.prepare("7 translate 正文\n")
        code, out = run("chunks.py", "split", self.ws)
        self.assertEqual(code, 1, out)

    def test_plan_lines_must_increase(self):
        self.prepare("1 translate 正文\n20 translate 第二部分\n10 keep 参考文献\n")
        code, out = run("chunks.py", "split", self.ws)
        self.assertEqual(code, 1, out)

    def test_split_covers_every_line(self):
        lines = SOURCE.splitlines()
        self.prepare(f"1 skip 标题\n{lines.index('## Abstract') + 1} translate 正文\n{lines.index('## References') + 1} keep 参考文献\n")
        code, out = run("chunks.py", "split", self.ws)
        self.assertEqual(code, 0, out)
        parts = [(self.ws / "chunks" / name).read_text(encoding="utf-8") for name in ("001.skip.md", "002.src.md", "003.src.md")]
        self.assertEqual("".join(parts), SOURCE)

    def test_split_refuses_to_overwrite_corrected_chunks(self):
        self.prepare("1 translate 正文\n")
        self.assertEqual(run("chunks.py", "split", self.ws)[0], 0)
        src = self.ws / "chunks" / "001.src.md"
        src.write_text("校对过的原文", encoding="utf-8")
        code, out = run("chunks.py", "split", self.ws)
        self.assertEqual(code, 1, out)
        self.assertEqual(src.read_text(encoding="utf-8"), "校对过的原文")


class PublishTest(Workspace):
    def test_publish_copies_translation_and_referenced_images(self):
        ws = self.build()
        png(ws / "images" / "fig-002.png", 4, 4)
        entry = self.tmp / "repo" / "ai" / "papers" / "2018-yolov3"
        code, out = run("publish.py", ws, entry)
        self.assertEqual(code, 0, out)
        self.assertEqual((entry / "translation.md").read_text(encoding="utf-8"), (ws / "translation.md").read_text(encoding="utf-8"))
        self.assertTrue((entry / "images" / "fig-001.png").is_file())
        self.assertFalse((entry / "images" / "fig-002.png").exists())

    def test_publish_refuses_existing_translation(self):
        ws = self.build()
        entry = self.tmp / "entry"
        entry.mkdir()
        (entry / "translation.md").write_text("**读者的标注**", encoding="utf-8")
        code, out = run("publish.py", ws, entry)
        self.assertEqual(code, 1, out)
        self.assertEqual((entry / "translation.md").read_text(encoding="utf-8"), "**读者的标注**")

    def test_publish_refuses_when_check_fails(self):
        ws = self.build(body=ZH_BODY.replace("## 2. 方案", "2. 方案"))
        entry = self.tmp / "entry"
        code, out = run("publish.py", ws, entry)
        self.assertEqual(code, 1, out)
        self.assertFalse((entry / "translation.md").exists())


class RenderTest(Workspace):
    def test_render_scale_split_and_text(self):
        try:
            import pypdfium2
        except ImportError:
            self.skipTest("需要 pypdfium2（随 docling 安装）")
        pdf = pypdfium2.PdfDocument.new()
        pdf.new_page(200, 300)
        pdf.new_page(200, 300)
        pdf.save(str(self.tmp / "doc.pdf"))
        code, out = run("render.py", self.tmp / "doc.pdf", self.ws, "2", "--scale", "2", "--split", "2")
        self.assertEqual(code, 0, out)
        pages = self.ws / "pages"
        self.assertEqual(sorted(p.name for p in pages.iterdir()), ["p-0002-1.png", "p-0002-2.png", "p-0002.txt"])


@unittest.skipUnless(shutil.which("pandoc"), "需要 pandoc")
class ExtractEpubTest(Workspace):
    def epub(self, markdown, lang="en"):
        src = self.tmp / "book-src"
        src.mkdir(exist_ok=True)
        png(src / "small.png", 8, 8)
        png(src / "big.png", 800, 600, noisy=True)
        (src / "book.md").write_text(markdown, encoding="utf-8")
        out = self.tmp / "book.epub"
        subprocess.run(
            ["pandoc", "book.md", "-o", str(out), "--mathml", "--metadata", "title=Test Book", "--metadata", "author=Jane Doe", "--metadata", f"lang={lang}"],
            cwd=src,
            check=True,
        )
        return out

    BOOK = """# Chapter One

The first chapter explains why small images matter for every reader of this book.

![A small figure](small.png){width=50%}

| Term | Meaning |
|------|---------|
| vessel | where experience accumulates |

A sentence with a footnote.[^n]

[^n]: The footnote text lives at the end of the chapter.

# Chapter Two

The second chapter shows a large photograph that should be compressed before it enters git.

$$
S = \\frac{a}{b} \\times 100
$$

![A big photo](big.png)
"""

    def test_extract_epub(self):
        code, out = run("extract.py", self.epub(self.BOOK), self.ws)
        self.assertEqual(code, 0, out)
        text = (self.ws / "source.md").read_text(encoding="utf-8")
        self.assertIn("](images/fig-001.png)", text)
        self.assertIn("](images/fig-002.jpg)", text)
        self.assertLess((self.ws / "images" / "fig-002.jpg").stat().st_size, 1_000_000)
        self.assertTrue((self.ws / "images" / "fig-001.png").is_file())
        self.assertIn("|---", text.replace(" ", ""))
        self.assertIn("[^1]", text)
        self.assertIn("# Chapter One", text)
        for noise in ("<div", "<span", "{#", "width="):
            self.assertNotIn(noise, text)
        self.assertIn("$$", text)
        self.assertNotIn("``` math", text)
        self.assertLess(text.index("[^1]:"), text.index("# Chapter Two"), "脚注定义应留在所属章节末尾")
        meta = json.loads((self.ws / "extract.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["format"], "epub")
        self.assertEqual(meta["metadata"]["title"], "Test Book")
        self.assertTrue((self.ws / "outline.txt").is_file())

    def test_extract_with_relative_workspace(self):
        code, out = run("extract.py", self.epub(self.BOOK), "ws", cwd=self.tmp)
        self.assertEqual(code, 0, out)
        text = (self.ws / "source.md").read_text(encoding="utf-8")
        self.assertIn("](images/fig-001.png)", text)
        self.assertTrue((self.ws / "images" / "fig-001.png").is_file())

    def test_extract_refuses_chinese_source(self):
        book = "# 第一章\n\n" + "这是一本中文书，已经不需要再翻译成中文了。" * 20 + "\n"
        code, out = run("extract.py", self.epub(book, lang="zh-CN"), self.ws)
        self.assertEqual(code, 2, out)
        self.assertIn("中文", out)
        self.assertFalse((self.ws / "source.md").exists())

    def test_extract_refuses_existing_workspace(self):
        book = self.epub(self.BOOK)
        self.assertEqual(run("extract.py", book, self.ws)[0], 0)
        source = self.ws / "source.md"
        source.write_text("校对过的原文", encoding="utf-8")
        code, out = run("extract.py", book, self.ws)
        self.assertEqual(code, 1, out)
        self.assertEqual(source.read_text(encoding="utf-8"), "校对过的原文")


class CleanTextTest(unittest.TestCase):
    """docling 提取稿里确定性的杂质，提取时直接清掉。"""

    def test_clean_docling_artifacts(self):
        sys.path.insert(0, str(SCRIPTS))
        from extract import clean

        raw = "- · first item\n  - · nested item\nsurface\u00adlevel and Hinton &amp; Salakhutdinov\n"
        self.assertEqual(clean(raw), "- first item\n  - nested item\nsurfacelevel and Hinton & Salakhutdinov\n")


if __name__ == "__main__":
    unittest.main()
