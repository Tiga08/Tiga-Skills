"""逐块比对校对后的原文与译文，找出漏译和结构损坏；有错误时以非零退出。

用法：
  python3 check.py <工作区>               检查所有块和拼接好的 translation.md
  python3 check.py <工作区> --chunk NNN   只检查一块（子 agent 交稿前自查）

每块比对：标题、段落、图片、表格、公式、代码块、脚注一一对应，图片、公式、代码块的顺序也一致；译文里没有整段英文和英文标题；
keep 块除标题外与原文逐行一致；原文块和译文里都没有未识别的公式占位符。
整体检查：每块都有译文；header.md 以 H1 开头；terms.md 有「## 翻译术语表」；
translation.md 是最新拼接结果；它引用的图片都存在。
"""

import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from chunks import join_text, load_plan

PLACEHOLDER = "<!-- formula-not-decoded -->"
FENCE = re.compile(r"^(```|~~~)")
DISPLAY_MATH = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
HEADING = re.compile(r"^#{1,6}\s+(.*\S)")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc=\"([^\"]+)\"")
FOOTNOTE_DEF = re.compile(r"^\[\^([^\]]+)\]:", re.M)
FOOTNOTE_REF = re.compile(r"\[\^([^\]]+)\](?!:)")
CJK = re.compile(r"[　-〿㐀-䶿一-鿿＀-￯]")
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
ENGLISH_RUN = 8  # 连续这么多个英文词、中间没有中文，就算没译

# 判断英文残留前先去掉的内容：行内代码、行内公式、图片、链接地址、网址、脚注和文献引用、书名号里的原名、HTML 标签
NOISE = [
    re.compile(r"`[^`]*`"),
    re.compile(r"(?<!\$)\$[^$\n]+\$(?!\$)|\\\(.+?\\\)"),
    MD_IMAGE,
    re.compile(r"\]\([^)]*\)"),
    re.compile(r"https?://\S+"),
    FOOTNOTE_REF,
    re.compile(r"\[[\d,\s–-]+\]"),
    re.compile(r"[（(][^()（）]*\b(?:1[5-9]|20)\d{2}[a-z]?\b[^()（）]*[)）]"),
    re.compile(r"《[^》]*》"),
    re.compile(r"<[^>]+>"),
]


@dataclass
class Doc:
    headings: list = field(default_factory=list)
    blocks: int = 0
    images: list = field(default_factory=list)
    tables: int = 0
    formulas: list = field(default_factory=list)
    code: list = field(default_factory=list)
    placeholders: int = 0
    footnote_defs: list = field(default_factory=list)
    footnote_refs: set = field(default_factory=set)
    units: list = field(default_factory=list)  # 需要检查英文残留的文字单元：段落、表格单元格
    lines: list = field(default_factory=list)  # 去掉标题和注释后的非空行，用于 keep 块逐行比对


def parse(text):
    doc = Doc(placeholders=text.count(PLACEHOLDER))
    body, code = [], []
    for line in text.splitlines():
        if code:
            code.append(line)
            if FENCE.match(line.strip()) and line.strip().startswith(code[0].strip()[:3]):
                doc.code.append("\n".join(code))
                code = []
            continue
        if FENCE.match(line.strip()):
            code = [line]
            body.append("\x00CODE\x00")
            continue
        body.append(line)
    if code:  # 没闭合的代码块也算进去，方便比对
        doc.code.append("\n".join(code))
    rest = "\n".join(body)

    def take_math(m):
        doc.formulas.append(" ".join((m.group(1) or m.group(2)).split()))
        return "\x00MATH\x00"

    rest = COMMENT.sub("", DISPLAY_MATH.sub(take_math, rest))
    doc.footnote_defs = FOOTNOTE_DEF.findall(rest)
    doc.footnote_refs = set(FOOTNOTE_REF.findall(rest))
    for block in re.split(r"\n[ \t]*\n", rest):
        if not block.strip():
            continue
        doc.blocks += 1
        lines = block.strip().splitlines()
        doc.images += MD_IMAGE.findall(block) + HTML_IMAGE.findall(block)
        doc.tables += sum(1 for line in lines if TABLE_RULE.match(line)) + block.count("<table")
        for line in lines:
            m = HEADING.match(line)
            if m:
                doc.headings.append(m.group(1))
            elif "\x00" not in line:
                doc.lines.append(line.rstrip())
        if any(TABLE_RULE.match(line) for line in lines):
            doc.units += [cell for line in lines for cell in line.split("|")]
        elif "<table" in block:
            doc.units += re.split(r"<[^>]+>", block)
        else:
            doc.units.append(" ".join(line for line in lines if not HEADING.match(line)))
    return doc


def english_run(text):
    """返回文字里最长的一段连续英文（中间没有中文）的词数和这段内容。"""
    for pattern in NOISE:
        text = pattern.sub(" ", text)
    best = (0, "")
    for segment in CJK.split(text):
        words = WORD.findall(segment)
        if len(words) > best[0]:
            best = (len(words), segment.strip())
    return best


def heading_untranslated(title, src_titles):
    """没有中文，并且有两个以上不带数字的英文词，或者与原文标题一字不差（如 References）。
    型号（YOLOv3、Darknet-53）和只有一个名称的标题（AdaMax）不算。"""
    if CJK.search(title):
        return False
    words = [t for t in title.split() if re.fullmatch(r"[A-Za-z][A-Za-z'’-]+[.,:;!?]?", t)]
    return len(words) >= 2 or (bool(words) and title in src_titles)


def short(text, n=60):
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n] + "…"


def compare(label, src_text, zh_text, action, errors, warnings):
    src, zh = parse(src_text), parse(zh_text)
    if src.placeholders:
        errors.append(f"{label} 原文块里还有 {src.placeholders} 个未识别的公式占位符，先对照 PDF 在原文块里补成 LaTeX")
    if zh.placeholders:
        errors.append(f"{label} 译文里残留 {zh.placeholders} 个公式占位符")

    def count(name, a, b, hint=""):
        if b < a:
            errors.append(f"{label} {name}少了 {a - b} 个（原文 {a}，译文 {b}）{hint}")
        elif b > a:
            warnings.append(f"{label} {name}多了 {b - a} 个（原文 {a}，译文 {b}）")

    count("标题", len(src.headings), len(zh.headings))
    count("段落", src.blocks, zh.blocks, "，疑似漏译")
    count("表格", src.tables, zh.tables)
    count("脚注定义", len(src.footnote_defs), len(zh.footnote_defs))
    for name, a, b in (("图片", src.images, zh.images), ("公式", src.formulas, zh.formulas), ("代码块", src.code, zh.code)):
        for item in Counter(a) - Counter(b):
            errors.append(f"{label} {name}缺失或被改动：{short(item)}")
        for item in Counter(b) - Counter(a):
            (errors if name == "图片" else warnings).append(f"{label} 多出原文没有的{name}：{short(item)}")
        if Counter(a) == Counter(b) and a != b:
            errors.append(f"{label} {name}的顺序与原文不一致")
    for ref in sorted(zh.footnote_refs - set(zh.footnote_defs)):
        errors.append(f"{label} 脚注 [^{ref}] 只有引用没有定义")
    for ref in sorted(set(zh.footnote_defs) - zh.footnote_refs):
        errors.append(f"{label} 脚注 [^{ref}] 只有定义没有引用")
    for title in zh.headings:
        if heading_untranslated(title, set(src.headings)):
            errors.append(f"{label} 标题疑似未翻译：{short(title)}")
    if action == "keep":
        if src.lines != zh.lines:
            diff = next((i for i, (a, b) in enumerate(zip(src.lines, zh.lines)) if a != b), min(len(src.lines), len(zh.lines)))
            got = zh.lines[diff] if diff < len(zh.lines) else "（缺行）"
            errors.append(f"{label} 保留块应照抄原文、只译标题，第 {diff + 1} 个非空行有改动：{short(got)}")
        return
    for unit in zh.units:
        words, segment = english_run(unit)
        if words >= ENGLISH_RUN:
            errors.append(f"{label} 疑似未翻译的英文：{short(segment)}")


def image_errors(text, base, label):
    refs = MD_IMAGE.findall(text) + HTML_IMAGE.findall(text)
    return [f"{label} 引用的图片不存在：{ref}" for ref in dict.fromkeys(refs) if not (base / ref).is_file()]


def check(ws, only=None):
    """返回 (错误, 提醒)。"""
    errors, warnings = [], []
    chunks = ws / "chunks"
    for num, _, action, title in load_plan(ws):
        if action == "skip" or (only and num != only):
            continue
        src, zh = chunks / f"{num}.src.md", chunks / f"{num}.zh.md"
        if not src.is_file():
            errors.append(f"{num} 没有原文块 {src.name}，先运行 chunks.py split")
        elif not zh.is_file():
            errors.append(f"{num}（{title}）还没有译文 {zh.name}")
        else:
            zh_text = zh.read_text(encoding="utf-8")
            compare(num, src.read_text(encoding="utf-8"), zh_text, action, errors, warnings)
            if only:
                errors += image_errors(zh_text, ws, num)
    if only:
        return errors, warnings
    header = ws / "header.md"
    if not header.is_file() or not header.read_text(encoding="utf-8").lstrip().startswith("# "):
        errors.append("header.md 缺失，或没有以 H1 书名/标题开头")
    terms = ws / "terms.md"
    if not terms.is_file() or not re.search(r"^## 翻译术语表\s*$", terms.read_text(encoding="utf-8"), re.M):
        errors.append("terms.md 缺失，或没有「## 翻译术语表」标题")
    translation = ws / "translation.md"
    expected, _ = join_text(ws)
    if not translation.is_file():
        errors.append("还没有 translation.md，运行 chunks.py join 拼接")
    else:
        text = translation.read_text(encoding="utf-8")
        if expected is not None and text != expected:
            errors.append("translation.md 不是最新拼接结果，运行 chunks.py join 重新拼接")
        errors += image_errors(text, ws, "translation.md")
    return errors, warnings


def report(errors, warnings):
    for title, items in (("错误", errors), ("提醒", warnings)):
        if items:
            print(f"{title}：")
            print("\n".join(f"- {item}" for item in items))
    print(f"检查未通过：{len(errors)} 个错误" if errors else "检查通过")


if __name__ == "__main__":
    args = sys.argv[1:]
    only = None
    if len(args) == 3 and args[1] == "--chunk":
        only = args[2].zfill(3)
        args = args[:1]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    errors, warnings = check(Path(args[0]), only)
    report(errors, warnings)
    sys.exit(1 if errors else 0)
