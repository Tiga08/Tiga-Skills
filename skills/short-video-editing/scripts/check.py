# /// script
# requires-python = ">=3.11"
# ///
"""校验一个发布包是否齐全、合规；有问题时逐条列出并以非零退出。

检查：文件齐全；FCPXML 通过 FCP 自带 DTD 校验且引用的素材都在；SRT 时间轴有序；
封面尺寸；post.md 的小红书标题不超过 20 字、话题 5–8 个，抖音/视频号话题 3–5 个；时长是否在建议范围（只提醒）。

用法：uv run check.py output/<批次>/<NN-短名>
"""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote, urlparse

from common import ffprobe, load_json

FILES = ["edit.json", "project.fcpxml", "subtitles.srt", "cover-9x16.jpg", "cover-3x4.jpg", "post.md"]
COVERS = {"cover-9x16.jpg": (1080, 1920), "cover-3x4.jpg": (1080, 1440)}
DTD_DIR = Path("/Applications/Final Cut Pro.app/Contents/Frameworks/Interchange.framework/Versions/A/Resources")
DURATION = {"montage": (15, 30), "talking": (30, 60)}
SRT_TIME = re.compile(r"(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})")


def check_fcpxml(path, problems, warnings):
    root = ET.parse(path).getroot()
    dtd = DTD_DIR / f"FCPXMLv{root.get('version', '').replace('.', '_')}.dtd"
    if dtd.is_file():
        p = subprocess.run(["xmllint", "--noout", "--dtdvalid", dtd.as_uri(), str(path)], capture_output=True, text=True)
        if p.returncode != 0:
            problems.append(f"project.fcpxml 未通过 DTD 校验：{p.stderr.strip()[:800]}")
    else:
        warnings.append(f"找不到 {dtd.name}（未安装 Final Cut Pro？），跳过 DTD 校验")
    for rep in root.iter("media-rep"):
        src = unquote(urlparse(rep.get("src")).path)
        if not Path(src).is_file():
            problems.append(f"project.fcpxml 引用的素材不存在：{src}")
    return float(Fraction(root.find(".//sequence").get("duration").rstrip("s")))


def check_srt(path, kind, problems):
    blocks = [b for b in path.read_text(encoding="utf-8").strip().split("\n\n") if b.strip()]
    last_end = 0
    for i, b in enumerate(blocks, 1):
        lines = b.split("\n")
        m = SRT_TIME.fullmatch(lines[1]) if len(lines) >= 3 and lines[0] == str(i) else None
        if not m:
            problems.append(f"subtitles.srt 第 {i} 条格式不对：{b[:60]!r}")
            return
        v = [int(x) for x in m.groups()]
        start = ((v[0] * 60 + v[1]) * 60 + v[2]) * 1000 + v[3]
        end = ((v[4] * 60 + v[5]) * 60 + v[6]) * 1000 + v[7]
        if not last_end <= start < end:
            problems.append(f"subtitles.srt 第 {i} 条时间重叠或颠倒")
        last_end = end
    if kind == "talking" and not blocks:
        problems.append("口播视频的 subtitles.srt 为空")


def visible_len(text):
    """按看到的字数计：去掉 emoji 变体选择符和零宽连接符。"""
    return len(re.sub("[️‍]", "", text))


def section(md, heading):
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", md, re.M | re.S)
    return m.group(1) if m else None


def field(body, name):
    m = re.search(rf"^{name}：(.*?)(?=^\S+：|\Z)", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def check_post(path, problems):
    md = path.read_text(encoding="utf-8")
    rules = {"小红书": (20, (5, 8), True), "抖音 / 视频号": (None, (3, 5), False)}
    for heading, (max_title, (lo, hi), need_body) in rules.items():
        body = section(md, heading)
        if body is None:
            problems.append(f"post.md 缺少「## {heading}」一节")
            continue
        title = field(body, "标题")
        if not title:
            problems.append(f"post.md「{heading}」缺少标题")
        elif max_title and visible_len(title) > max_title:
            problems.append(f"post.md「{heading}」标题 {visible_len(title)} 字，超过 {max_title} 字：{title}")
        if need_body and not field(body, "正文"):
            problems.append(f"post.md「{heading}」缺少正文")
        tags = re.findall(r"#[^\s#]+", field(body, "话题"))
        if not lo <= len(tags) <= hi:
            problems.append(f"post.md「{heading}」话题 {len(tags)} 个，应为 {lo}–{hi} 个")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pkg = Path(sys.argv[1])
    problems, warnings = [], []
    missing = [f for f in FILES if not (pkg / f).is_file()]
    problems += [f"缺少 {f}" for f in missing]
    kind = load_json(pkg / "edit.json").get("type") if "edit.json" not in missing else None
    duration = check_fcpxml(pkg / "project.fcpxml", problems, warnings) if "project.fcpxml" not in missing else 0
    if "subtitles.srt" not in missing:
        check_srt(pkg / "subtitles.srt", kind, problems)
    for name, expected in COVERS.items():
        if name not in missing:
            s = ffprobe(pkg / name)["streams"][0]
            if (s["width"], s["height"]) != expected:
                problems.append(f"{name} 尺寸 {s['width']}x{s['height']}，应为 {expected[0]}x{expected[1]}")
    if "post.md" not in missing:
        check_post(pkg / "post.md", problems)
    if kind in DURATION and duration:
        lo, hi = DURATION[kind]
        if not lo <= duration <= hi:
            warnings.append(f"时长 {duration:.1f}s，不在{'混剪' if kind == 'montage' else '口播'}建议的 {lo}–{hi}s 内")

    for w in warnings:
        print(f"提醒：{w}")
    if problems:
        for p in problems:
            print(f"问题：{p}")
        sys.exit(1)
    print(f"发布包检查通过：{pkg}")


if __name__ == "__main__":
    main()
