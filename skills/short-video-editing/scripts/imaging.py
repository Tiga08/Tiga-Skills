"""出图共用：抽帧、按比例填充裁切、拼图与文字标注。依赖 Pillow，调用方需在脚本头声明 pillow。"""

import subprocess
import tempfile
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import TO_SDR, fail, ffmpeg

LABEL_FONT = "Noto Sans CJK SC"


@cache
def font_file(family, face="Regular"):
    p = subprocess.run(["fc-match", "-f", "%{file}", f"{family}:style={face}"], capture_output=True, text=True)
    path = p.stdout.strip()
    if p.returncode != 0 or not path:
        fail(f"找不到字体 {family} {face}（fc-match）")
    if family.split()[0].lower() not in Path(path).name.lower():
        fail(f"系统没有安装字体 {family} {face}，fc-match 退回了 {path}")
    return path


def font(size, family=LABEL_FONT, face="Regular"):
    return ImageFont.truetype(font_file(family, face), size)


def grab(path, t, out=None, hdr=False):
    """抽取 t 秒处的一帧（按旋转元数据摆正），返回 PIL 图像。HDR 素材传 hdr=True，转成 SDR 再出图，否则发灰。"""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "f.png"
        vf = ["-vf", TO_SDR] if hdr else []
        ffmpeg("-ss", f"{max(t, 0):.4f}", "-i", path, *vf, "-frames:v", "1", "-update", "1", png)
        if not png.is_file():
            fail(f"{path} 在 {t:.2f}s 处抽不到画面")
        img = Image.open(png).convert("RGB")
        img.load()
    if out:
        img.save(out)
    return img


def fill(img, w, h, zoom=1.0):
    """等比缩放铺满 w×h 后居中裁切（与时间线的“填充”一致），可再放大 zoom 倍。"""
    scale = max(w / img.width, h / img.height) * zoom
    img = img.resize((max(w, round(img.width * scale)), max(h, round(img.height * scale))), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def label(img, text, size=18, where="bottom"):
    """在图块上加一条半透明底色的标注。"""
    d = ImageDraw.Draw(img, "RGBA")
    f = font(size)
    lines = text.split("\n")
    lh = size + 6
    h = lh * len(lines) + 6
    y0 = img.height - h if where == "bottom" else 0
    d.rectangle((0, y0, img.width, y0 + h), fill=(0, 0, 0, 160))
    for i, line in enumerate(lines):
        d.text((6, y0 + 3 + i * lh), line, font=f, fill=(255, 255, 255))
    return img


def grid(tiles, cols, header=None, gap=6, bg=(24, 24, 24)):
    """把等大的图块拼成网格，可带一行标题。"""
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    head = 48 if header else 0
    sheet = Image.new("RGB", (cols * w + (cols + 1) * gap, head + rows * h + (rows + 1) * gap), bg)
    if header:
        ImageDraw.Draw(sheet).text((gap * 2, 10), header, font=font(24), fill=(240, 240, 240))
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet.paste(t, (gap + c * (w + gap), head + gap + r * (h + gap)))
    return sheet
