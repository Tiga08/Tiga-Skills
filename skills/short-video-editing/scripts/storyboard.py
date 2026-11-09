# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""把 edit.json 展开成时间线，写出 timeline.json、timeline.txt 和分镜图 storyboard.jpg，供写剪辑方案和自查。

用法：uv run storyboard.py output/<批次>/<NN-短名>
"""

import sys
from fractions import Fraction
from pathlib import Path

from common import FPS, describe, expand, load_clips, public, write_json
from imaging import fill, grab, grid, label

TILE_W, TILE_H = 180, 320


def tile(clips, item, text):
    mid = item["_in"] + Fraction(item["_f1"] - item["_f0"], FPS) / 2
    c = clips[item["clip"]]
    img = fill(grab(c["path"], float(mid), hdr=c["hdr"]), TILE_W, TILE_H, item.get("zoom", 1.0))
    return label(img, text, size=14)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pkg = Path(sys.argv[1])
    tl = expand(pkg)
    write_json(pkg / "timeline.json", public(tl))
    (pkg / "timeline.txt").write_text(describe(tl), encoding="utf-8")

    clips = load_clips(pkg)
    tiles = []
    for i, m in enumerate(tl["main"], 1):
        zoom = f" 推近{m['zoom']}" if m["zoom"] != 1.0 else ""
        tiles.append(tile(clips, m, f"#{i} {m['_f0'] / FPS:.1f}–{m['_f1'] / FPS:.1f}s{zoom}\n{Path(m['clip']).stem}"))
    for o in tl["overlays"]:
        tiles.append(tile(clips, o, f"覆盖 {o['_f0'] / FPS:.1f}–{o['_f1'] / FPS:.1f}s\n{Path(o['clip']).stem}"))
    header = f"{tl['title']}  {tl['duration']:.1f}s  {len(tl['main'])} 段" + (
        f"  {len(tl['overlays'])} 段空镜覆盖" if tl["overlays"] else "")
    grid(tiles, min(len(tiles), 8), header).save(pkg / "storyboard.jpg", quality=85)
    print((pkg / "timeline.txt").read_text(encoding="utf-8"))
    print(f"分镜图：{pkg / 'storyboard.jpg'}")


if __name__ == "__main__":
    main()
