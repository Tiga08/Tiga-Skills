"""把原版 PDF 或 EPUB 提取成工作区里的 source.md 和 images/。

用法：python3 extract.py <原版文件> <工作区>

- EPUB：pandoc 转 GFM（公式输出成 $$，脚注放在所属章节末尾），经 epub.lua 去掉 HTML 噪声。
- PDF：docling（运行本脚本的 python3 要装有 docling），开启标题层级推断，图片按 2 倍分辨率裁切；
  每页开头插入 <!-- page N --> 标记，方便对照 PDF 校对。不开公式识别：它让 15 页的论文从 20 秒变成 35 分钟，
  识别结果还常混进乱码；公式只留占位符 <!-- formula-not-decoded -->，校对时对照原页写成 LaTeX。
- 图片按出现顺序改名为 images/fig-NNN.<扩展名>；超过 1MB 的位图用 sips 转成质量 85 的 JPEG（变小才替换）。
  有本地图片找不到时报错退出，不写 source.md。
- 原版以中文为主时拒绝，退出码 2：中文原版不需要翻译，出版社译本不能入库。
- 工作区已有 source.md 时拒绝，避免覆盖校对过的内容。

输出：source.md、images/、outline.txt（每个标题的行号和所在页）、extract.json（格式、页数、元数据、结构统计）。
PDF 的元数据含文件自带的标题、作者，以及前 5 页文字层里的 arXiv 号、DOI、ISBN。
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote

from check import CJK, HEADING, WORD, parse

SCRIPTS = Path(__file__).resolve().parent
MAX_IMAGE = 1_000_000
RASTER = {".png", ".jpg", ".tif", ".tiff", ".bmp"}
IMAGE_REF = re.compile(r"(!\[[^\]]*\]\()(<[^>]+>|[^)\s]+)((?:\s+\"[^\"]*\")?\))|(<img\b[^>]*\bsrc=\")([^\"]+)(\")")
PAGE = re.compile(r"^<!-- page (\d+) -->$")


def epub_metadata(src):
    ns = {
        "c": "urn:oasis:names:tc:opendocument:xmlns:container",
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    with zipfile.ZipFile(src) as z:
        opf = ET.fromstring(z.read("META-INF/container.xml")).find(".//c:rootfile", ns).get("full-path")
        meta = ET.fromstring(z.read(opf)).find("opf:metadata", ns)

    def values(tag):
        return [e.text.strip() for e in meta.findall(f"dc:{tag}", ns) if e.text and e.text.strip()]

    one = lambda tag: (values(tag) or [None])[0]
    return {
        "title": one("title"),
        "creators": values("creator"),
        "identifiers": values("identifier"),
        "language": one("language"),
        "date": one("date"),
        "publisher": one("publisher"),
    }


def from_epub(src, raw):
    md = raw / "book.md"
    subprocess.run(
        ["pandoc", str(src), "-f", "epub", "-t", "gfm-tex_math_gfm", "--wrap=none", "--reference-location=section",
         f"--lua-filter={SCRIPTS / 'epub.lua'}", f"--extract-media={raw / 'media'}", "-o", str(md)],
        check=True,
    )
    return md.read_text(encoding="utf-8"), raw, epub_metadata(src), None


def pdf_metadata(src):
    """PDF 自带的标题、作者，以及前 5 页文字层里出现的 arXiv 号、DOI、ISBN（docling 会丢掉页边文字）。"""
    import pypdfium2

    doc = pypdfium2.PdfDocument(src)
    meta = doc.get_metadata_dict()
    text = "\n".join(doc[i].get_textpage().get_text_range() for i in range(min(5, len(doc))))
    ids = re.findall(r"arXiv:\d{4}\.\d{4,5}(?:v\d+)?|\b10\.\d{4,9}/[^\s\"<>]+|ISBN[-:\s]*[\dX][\dX-]{8,16}", text)
    return {"title": meta.get("Title") or None, "author": meta.get("Author") or None, "identifiers": list(dict.fromkeys(ids))}


def from_pdf(src, raw):
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import HeadingHierarchyOptions, PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling_core.types.doc import ImageRefMode
    except ImportError:
        sys.exit("PDF 提取需要 docling：用装有 docling 的 python3 运行本脚本")
    options = PdfPipelineOptions(
        heading_hierarchy_options=HeadingHierarchyOptions(enabled=True),
        generate_picture_images=True,
        images_scale=2,
    )
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
    doc = converter.convert(src).document
    parts = []
    for page in sorted(doc.pages):
        md = raw / f"page-{page:04d}.md"
        doc.save_as_markdown(md, artifacts_dir=Path("artifacts"), image_mode=ImageRefMode.REFERENCED, page_no=page)
        parts.append(f"<!-- page {page} -->\n\n{md.read_text(encoding='utf-8').strip()}\n")
    return "\n".join(parts), raw, pdf_metadata(src), len(doc.pages)


def clean(text):
    """清掉提取稿里确定性的杂质：软连字符、docling 列表项的「- · 」前缀、&amp; 实体。"""
    text = text.replace("\u00ad", "").replace("&amp;", "&")
    return re.sub(r"^(\s*)- · ", r"\1- ", text, flags=re.M)


def normalize_images(text, base, images):
    """按出现顺序复制、改名、必要时压缩图片，并改写引用；返回 (新文本, 找不到的引用)。"""
    images.mkdir()
    renamed, missing = {}, []

    def target(ref):
        if re.match(r"[a-z][a-z0-9+.-]*:", ref, re.I):  # 网络图片或 data URI，原样保留
            return ref
        path = Path(unquote(ref.strip("<>")))
        path = path if path.is_absolute() else base / path
        if path in renamed:
            return renamed[path]
        if not path.is_file():
            missing.append(ref)
            return ref
        ext = path.suffix.lower().replace(".jpeg", ".jpg")
        dest = images / f"fig-{len(renamed) + 1:03d}{ext}"
        shutil.copy2(path, dest)
        if ext in RASTER and dest.stat().st_size > MAX_IMAGE:
            jpg = dest.with_name(dest.stem + ".tmp.jpg")
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", str(dest), "--out", str(jpg)],
                           check=True, capture_output=True)
            if jpg.stat().st_size < dest.stat().st_size:
                dest.unlink()
                dest = jpg.rename(dest.with_suffix(".jpg"))
            else:
                jpg.unlink()
        renamed[path] = f"images/{dest.name}"
        return renamed[path]

    def sub(m):
        if m.group(1):
            return m.group(1) + target(m.group(2)) + m.group(3)
        return m.group(4) + target(m.group(5)) + m.group(6)

    return IMAGE_REF.sub(sub, text), missing


def outline(text):
    rows, page = [], None
    for n, line in enumerate(text.splitlines(), 1):
        m = PAGE.match(line)
        if m:
            page = m.group(1)
        elif HEADING.match(line):
            rows.append(f"{n}\t{'p' + page if page else '-'}\t{line}")
    return "\n".join(rows) + "\n"


def main(src, ws):
    if (ws / "source.md").exists():
        print(f"{ws / 'source.md'} 已存在（可能已校对），不重新提取；确需重来时先手动删除工作区", file=sys.stderr)
        return 1
    kind = src.suffix.lower().lstrip(".")
    if kind not in ("pdf", "epub"):
        print(f"只支持 PDF 和 EPUB：{src}", file=sys.stderr)
        return 1
    ws.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ws) as tmp:
        raw = Path(tmp).resolve()
        text, base, metadata, pages = (from_pdf if kind == "pdf" else from_epub)(src, raw)
        text = clean(text)
        cjk, words = len(CJK.findall(text)), len(WORD.findall(text))
        if cjk > words:
            print(f"原版以中文为主（中文字符 {cjk}，英文词 {words}），不需要翻译；出版社译本也不能入库", file=sys.stderr)
            return 2
        text, missing = normalize_images(text, base, ws / "images")
        if missing:
            shutil.rmtree(ws / "images")
            print("找不到这些图片，提取不完整：" + "、".join(missing), file=sys.stderr)
            return 1
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    (ws / "source.md").write_text(text, encoding="utf-8")
    (ws / "outline.txt").write_text(outline(text), encoding="utf-8")
    doc = parse(text)
    stats = {
        "lines": text.count("\n"),
        "words": words,
        "headings": len(doc.headings),
        "images": len(doc.images),
        "tables": doc.tables,
        "formulas": len(doc.formulas),
        "formula_placeholders": doc.placeholders,
        "code_blocks": len(doc.code),
    }
    info = {"source": str(src), "format": kind, "pages": pages, "metadata": metadata, "stats": stats}
    (ws / "extract.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已提取 {src.name}（{kind.upper()}{f'，{pages} 页' if pages else ''}）→ {ws / 'source.md'}，共 {stats['lines']} 行")
    print(f"英文词 {words}；标题 {stats['headings']}；图片 {stats['images']}；表格 {stats['tables']}；"
          f"独立公式 {stats['formulas']}（未识别占位符 {stats['formula_placeholders']}）；代码块 {stats['code_blocks']}")
    if metadata:
        print("元数据：" + json.dumps(metadata, ensure_ascii=False))
    print(f"标题大纲：{ws / 'outline.txt'}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]).expanduser().resolve(), Path(sys.argv[2])))
