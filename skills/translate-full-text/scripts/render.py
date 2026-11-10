"""把 PDF 的指定页渲染成 PNG，并导出这几页的文字层，供校对时对照原页。

用法：python3 render.py <原版 PDF> <工作区> <页码范围，如 3 或 3-8> [--scale 1.5] [--split 1]

输出到 <工作区>/pages/：
- p-NNNN.png：整页图，用 Read 查看；
- --split N 时改为 p-NNNN-1.png … p-NNNN-N.png，把每页横切成 N 条。公式密的页配合 --scale 3 --split 3，才看得清上下标；
- p-NNNN.txt：该页的 PDF 文字层，重建公式、核对拼写时有用（docling 会丢掉页眉页边的文字）。

用到 pypdfium2，它随 docling 一起安装。
"""

import argparse
import sys
from pathlib import Path

import pypdfium2


def main():
    parser = argparse.ArgumentParser(description="渲染 PDF 原页并导出文字层")
    parser.add_argument("pdf")
    parser.add_argument("ws", type=Path)
    parser.add_argument("pages")
    parser.add_argument("--scale", type=float, default=1.5)
    parser.add_argument("--split", type=int, default=1)
    args = parser.parse_args()
    first, _, last = args.pages.partition("-")
    first, last = int(first), int(last or first)
    doc = pypdfium2.PdfDocument(args.pdf)
    if not 1 <= first <= last <= len(doc):
        print(f"页码范围 {args.pages} 超出了 1–{len(doc)}", file=sys.stderr)
        return 1
    out = args.ws / "pages"
    out.mkdir(parents=True, exist_ok=True)
    for n in range(first, last + 1):
        page = doc[n - 1]
        (out / f"p-{n:04d}.txt").write_text(page.get_textpage().get_text_range(), encoding="utf-8")
        image = page.render(scale=args.scale).to_pil()
        if args.split == 1:
            paths = [(out / f"p-{n:04d}.png", image)]
        else:
            step = image.height / args.split
            paths = [
                (out / f"p-{n:04d}-{i + 1}.png", image.crop((0, int(i * step), image.width, int((i + 1) * step))))
                for i in range(args.split)
            ]
        for path, part in paths:
            part.save(path)
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
