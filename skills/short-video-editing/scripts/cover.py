# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""按 edit.json 的 cover（素材、时间点、标题）生成两张封面：cover-9x16.jpg（1080x1920）与 cover-3x4.jpg（1080x1440）。

9:16 封面的标题放在中间 3:4 区域内，抖音主页网格按 3:4 裁切时也不会切掉字。

用法：uv run cover.py output/<批次>/<NN-短名> --style brand/style.json
"""

import argparse
import unicodedata
from pathlib import Path

from PIL import ImageDraw

from common import expand, fail, load_clips, load_json
from imaging import fill, font, grab

SIZES = {"cover-9x16.jpg": (1080, 1920, 0.36), "cover-3x4.jpg": (1080, 1440, 0.40)}  # 宽、高、标题中心的纵向位置
MAX_TEXT_W = 920


def plain(title):
    """去掉 emoji 等符号：封面字体没有这些字形，会画成方框。"""
    return "".join(ch for ch in title if ch == "\n" or unicodedata.category(ch) not in ("So", "Sk", "Cf", "Mn", "Cs")
                   and ord(ch) < 0x1F000).strip()


def lines_of(title, max_chars):
    """标题里写了换行就按它断；否则超过每行字数时均分。"""
    if "\n" in title:
        return [l.strip() for l in title.split("\n") if l.strip()]
    if len(title) <= max_chars:
        return [title]
    n = -(-len(title) // max_chars)
    size = -(-len(title) // n)
    return [title[i:i + size] for i in range(0, len(title), size)]


def render(frame, w, h, y_ratio, title, style):
    s = style["cover"]
    img = fill(frame, w, h)
    d = ImageDraw.Draw(img)
    lines = lines_of(title, s["maxChars"])
    size = 160
    while True:
        f = font(size, style["font"], s["fontFace"])
        stroke = max(4, size // 14)
        widths = [d.textbbox((0, 0), l, font=f, stroke_width=stroke)[2] for l in lines]
        if max(widths) <= MAX_TEXT_W or size <= 60:
            break
        size -= 6
    line_h = round(size * 1.18)
    top = round(h * y_ratio - line_h * len(lines) / 2)
    for i, (line, lw) in enumerate(zip(lines, widths)):
        d.text(((w - lw) // 2, top + i * line_h), line, font=f, fill=s["color"],
               stroke_width=stroke, stroke_fill=s["strokeColor"])
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--style", required=True)
    args = ap.parse_args()
    pkg = Path(args.package).resolve()
    tl = expand(pkg)
    cover = tl["cover"] or fail("edit.json 缺少 cover：{\"clip\": 素材名, \"t\": 秒, \"title\": 封面标题}")
    clips = load_clips(pkg)
    if cover["clip"] not in clips:
        fail(f"cover 引用了不存在的素材 {cover['clip']}")
    style = load_json(args.style)
    c = clips[cover["clip"]]
    frame = grab(c["path"], cover["t"], hdr=c["hdr"])
    title = plain(cover.get("title") or tl["title"])
    for name, (w, h, y) in SIZES.items():
        render(frame, w, h, y, title, style).save(pkg / name, quality=92)
        print(pkg / name)


if __name__ == "__main__":
    main()
