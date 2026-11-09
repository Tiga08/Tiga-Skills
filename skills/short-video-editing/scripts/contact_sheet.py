# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""为每条素材生成联系表：按间隔抽帧拼成图，图块上标出时间点，供挑镜头。

间隔为时长的 1/16，限制在 1–5 秒；长素材每 48 帧拆成一张（<名>.jpg、<名>-2.jpg…）。HDR 素材转成 SDR 再出图。

用法：uv run contact_sheet.py output/<批次>/work/clips.json output/<批次>/work/sheets
"""

import sys
import tempfile
from pathlib import Path

from PIL import Image

from common import ffmpeg, load_json, sdr
from imaging import grid, label

PER_SHEET = 48
MAX_STEP = 5.0


def tile_size(c):
    if c["height"] > c["width"]:
        return 216, 384, 6
    if c["width"] > c["height"]:
        return 384, 216, 4
    return 288, 288, 5


def sheets(c, out_dir):
    step = min(max(1.0, c["duration"] / 16), MAX_STEP)
    n = max(1, int(c["duration"] / step))
    w, h, cols = tile_size(c)
    with tempfile.TemporaryDirectory() as tmp:
        # 一次解码抽出所有帧；videotoolbox 硬解对 4K HEVC 快很多，不支持时 ffmpeg 自动回退软解
        ffmpeg("-hwaccel", "videotoolbox", "-i", c["path"], "-vf", f"{sdr(c)}fps=1/{step:.4f},scale={w}:{h}",
               "-frames:v", n, f"{tmp}/%04d.png")
        files = sorted(Path(tmp).glob("*.png"))
        tiles = [label(Image.open(f).convert("RGB"), f"{i * step:.1f}s") for i, f in enumerate(files)]
    flags = "  HDR→SDR" if c["hdr"] else ""
    stem = Path(c["name"]).stem
    chunks = [tiles[i:i + PER_SHEET] for i in range(0, len(tiles), PER_SHEET)]
    paths = []
    for k, chunk in enumerate(chunks, 1):
        part = f"  第 {k}/{len(chunks)} 张" if len(chunks) > 1 else ""
        header = f"{c['name']}  {c['duration']:.1f}s  {c['width']}x{c['height']}  每 {step:.1f}s 一帧{flags}{part}"
        path = out_dir / (f"{stem}.jpg" if k == 1 else f"{stem}-{k}.jpg")
        grid(chunk, cols, header).save(path, quality=85)
        paths.append(path)
    return paths


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    clips = load_json(sys.argv[1])["clips"]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for c in clips:
        for path in sheets(c, out):
            print(path)


if __name__ == "__main__":
    main()
