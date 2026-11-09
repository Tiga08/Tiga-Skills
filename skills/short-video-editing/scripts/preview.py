# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""按 edit.json 渲染低清预览 preview.mp4（540x960，不含字幕和标题），并输出切点对照图 cuts.jpg（每个切点前后各一帧）。

预览只用于自查剪辑点和声音是否连贯；成片用 render.py 渲染，或在 FCP 里精修导出。

用法：uv run preview.py output/<批次>/<NN-短名>
"""

import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image

from common import FPS, compose, expand, ffmpeg, load_clips
from imaging import grab, grid, label

W, H = 540, 960


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pkg = Path(sys.argv[1]).resolve()
    tl = expand(pkg)
    clips = load_clips(pkg)

    inputs, graph, vout, aout = compose(tl, clips, W, H)

    out = pkg / "preview.mp4"
    ffmpeg(*inputs, "-filter_complex", ";".join(graph), "-map", f"[{vout}]", "-map", f"[{aout}]",
           "-t", f"{tl['duration']:.4f}", "-r", FPS, "-c:v", "libx264", "-preset", "veryfast", "-crf", 26,
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out)

    # 切点对照：每个主轨切点取前 2 帧与后 1 帧
    pairs = []
    for i, m in enumerate(tl["main"][1:], 2):
        f = m["_f0"]
        before = grab(out, (f - 2) / FPS).resize((135, 240))
        after = grab(out, (f + 1) / FPS).resize((135, 240))
        pair = Image.new("RGB", (272, 240), (24, 24, 24))
        pair.paste(before, (0, 0))
        pair.paste(after, (137, 0))
        pairs.append(label(pair, f"#{i - 1}→#{i}  {f / FPS:.2f}s", size=14))
    if pairs:
        grid(pairs, min(len(pairs), 5), f"{tl['title']}  切点前后对照（左：切前，右：切后）").save(pkg / "cuts.jpg", quality=85)
    print(f"{out}（{tl['duration']:.2f}s）" + (f"，切点对照 {pkg / 'cuts.jpg'}" if pairs else ""))


if __name__ == "__main__":
    main()
