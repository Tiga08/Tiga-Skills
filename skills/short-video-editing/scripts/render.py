# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""按 edit.json 渲染可直接发布的成片 final.mp4：1080x1920、30fps、SDR Rec.709（HDR 素材自动转换），
H.264 + AAC，保留现场声，标题和字幕按 style.json 压进画面。不加音乐，发布时从平台曲库添加。

用法：uv run render.py output/<批次>/<NN-短名> --style brand/style.json
"""

import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from common import FPS, HEIGHT, WIDTH, compose, expand, ffmpeg, load_clips, load_json, wrap
from imaging import font

MAX_TEXT_W = WIDTH - 80
BT709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]


def text_layer(text, s, family):
    """一层透明的全画面文字图：position 是相对画面中心的偏移（y 向上为正），超宽时缩小字号。"""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(text, s["maxChars"]).split("\n") if "maxChars" in s else text.split("\n")
    size = s["fontSize"]
    while True:
        f = font(size, family, s["fontFace"])
        stroke = max(1, round(s["strokeWidth"] * size / s["fontSize"]))
        widths = [d.textbbox((0, 0), l, font=f, stroke_width=stroke)[2] for l in lines]
        if max(widths) <= MAX_TEXT_W or size <= 32:
            break
        size -= 4
    line_h = round(size * 1.2)
    cx, cy = WIDTH / 2 + s["position"][0], HEIGHT / 2 - s["position"][1]
    top = cy - line_h * len(lines) / 2
    for i, (line, lw) in enumerate(zip(lines, widths)):
        d.text((cx - lw / 2, top + i * line_h), line, font=f, fill=s["color"],
               stroke_width=stroke, stroke_fill=s["strokeColor"])
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--style", required=True)
    args = ap.parse_args()
    pkg = Path(args.package).resolve()
    style = load_json(args.style)
    tl = expand(pkg)
    inputs, graph, vout, aout = compose(tl, load_clips(pkg), WIDTH, HEIGHT)

    items = [(t["text"], t["style"], t["_f0"], t["_f1"]) for t in tl["texts"]]
    items += [(c["text"], "caption", c["_f0"], c["_f1"]) for c in tl["captions"]]
    with tempfile.TemporaryDirectory() as tmp:
        n_inputs = sum(1 for a in inputs if a == "-i")
        for k, (text, key, f0, f1) in enumerate(items):
            png = Path(tmp) / f"text{k}.png"
            text_layer(text, style[key], style["font"]).save(png)
            inputs += ["-i", png]
            graph.append(f"[{vout}][{n_inputs + k}:v]overlay=enable='between(t,{f0 / FPS:.4f},{f1 / FPS - 0.001:.4f})'"
                         f"[txt{k}]")
            vout = f"txt{k}"
        graph.append(f"[{vout}]format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709[vfinal]")
        out = pkg / "final.mp4"
        ffmpeg(*inputs, "-filter_complex", ";".join(graph), "-map", "[vfinal]", "-map", f"[{aout}]",
               "-t", f"{tl['duration']:.4f}", "-r", FPS, "-c:v", "libx264", "-preset", "slow", "-crf", 18,
               "-profile:v", "high", *BT709, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    print(f"{out}（{tl['duration']:.2f}s，{len(items)} 处文字）")


if __name__ == "__main__":
    main()
