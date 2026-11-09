# /// script
# requires-python = ">=3.11"
# ///
"""根据 edit.json 生成 Final Cut Pro 工程 project.fcpxml（FCPXML 1.13）和 subtitles.srt。

主轨是口播或混剪片段（铺满竖屏，跳剪处按需推近）；空镜覆盖放在第 1 层且只用画面；
字幕放第 2 层、标题文字放第 3 层，都是可在 FCP 里直接改的“基本字幕”。

用法：uv run build.py output/<批次>/<NN-短名> --style brand/style.json
"""

import argparse
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

from common import FPS, HEIGHT, WIDTH, asset_start, describe, expand, fcp_time, load_clips, load_json, public, wrap, write_json

BASIC_TITLE = ".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"
POSITION_KEY = "9999/999166631/999166633/1/100/101"
COLOR_SPACE = {"arib-std-b67": "9-18-9 (Rec. 2020 HLG)", "smpte2084": "9-16-9 (Rec. 2020 PQ)"}


def rgba(hex_color):
    h = hex_color.lstrip("#")
    return " ".join(f"{int(h[i:i + 2], 16) / 255:.4g}" for i in (0, 2, 4)) + " 1"


class Project:
    def __init__(self, tl, clips, style):
        self.tl, self.clips, self.style = tl, clips, style
        self.root = ET.Element("fcpxml", version="1.13")
        self.resources = ET.SubElement(self.root, "resources")
        self.ids = 0
        self.assets = {}
        self.styles = 0
        self.seq_fmt = self.add_format(WIDTH, HEIGHT, Fraction(FPS), "1-1-1 (Rec. 709)")
        self.title_effect = self.next_id()
        ET.SubElement(self.resources, "effect", id=self.title_effect, name="Basic Title", uid=BASIC_TITLE)

    def next_id(self):
        self.ids += 1
        return f"r{self.ids}"

    def add_format(self, w, h, fps, color_space):
        fid = self.next_id()
        ET.SubElement(self.resources, "format", id=fid, frameDuration=fcp_time(1 / Fraction(fps)),
                      width=str(w), height=str(h), colorSpace=color_space)
        return fid

    def asset(self, name):
        """每条素材一个 asset，引用原片路径，不复制文件。"""
        if name in self.assets:
            return self.assets[name]
        c = self.clips[name]
        fps = Fraction(c["fps"])
        fmt = self.add_format(c["width"], c["height"], fps, COLOR_SPACE.get(c["color_transfer"], "1-1-1 (Rec. 709)"))
        aid = self.next_id()
        attrs = {"id": aid, "name": Path(name).stem, "start": fcp_time(asset_start(c)),
                 "duration": fcp_time(Fraction(round(Fraction(c["duration"]) * fps)) / fps),
                 "hasVideo": "1", "format": fmt, "videoSources": "1"}
        if c["has_audio"]:
            attrs |= {"hasAudio": "1", "audioSources": "1", "audioChannels": str(c["audio_channels"]),
                      "audioRate": str(c["audio_rate"])}
        el = ET.SubElement(self.resources, "asset", attrs)
        ET.SubElement(el, "media-rep", kind="original-media", src=Path(c["path"]).as_uri())
        self.assets[name] = aid
        return aid

    def source_start(self, item):
        return asset_start(self.clips[item["clip"]]) + item["_in"]

    def clip_el(self, parent, item, offset, **extra):
        el = ET.SubElement(parent, "asset-clip", ref=self.asset(item["clip"]), offset=fcp_time(offset),
                           name=Path(item["clip"]).stem, start=fcp_time(self.source_start(item)),
                           duration=fcp_time(Fraction(item["_f1"] - item["_f0"], FPS)), tcFormat="NDF", **extra)
        ET.SubElement(el, "adjust-conform", type="fill")
        if item.get("zoom", 1.0) != 1.0:
            ET.SubElement(el, "adjust-transform", scale=f"{item['zoom']} {item['zoom']}")
        return el

    def title_el(self, parent, text, kind, offset, frames, lane):
        s = self.style[kind]
        el = ET.SubElement(parent, "title", ref=self.title_effect, lane=str(lane), offset=fcp_time(offset),
                           name="字幕" if kind == "caption" else "标题", duration=fcp_time(Fraction(frames, FPS)))
        x, y = s["position"]
        ET.SubElement(el, "param", name="Position", key=POSITION_KEY, value=f"{x} {y}")
        self.styles += 1
        sid = f"ts{self.styles}"
        body = ET.SubElement(el, "text")
        ET.SubElement(body, "text-style", ref=sid).text = wrap(text, s["maxChars"]) if "maxChars" in s else text
        definition = ET.SubElement(el, "text-style-def", id=sid)
        # FCP 与 Core Text 一致：描边宽度为负表示“填充 + 描边”，为正则只剩空心描边
        ET.SubElement(definition, "text-style", font=self.style["font"], fontSize=str(s["fontSize"]),
                      fontFace=s["fontFace"], fontColor=rgba(s["color"]), strokeColor=rgba(s["strokeColor"]),
                      strokeWidth=str(-abs(s["strokeWidth"])), alignment="center")

    def build(self, event_name, project_name):
        tl = self.tl
        event = ET.SubElement(self.root, "event", name=event_name)
        project = ET.SubElement(event, "project", name=project_name)
        seq = ET.SubElement(project, "sequence", format=self.seq_fmt, duration=fcp_time(Fraction(tl["_frames"], FPS)),
                            tcStart="0s", tcFormat="NDF", audioLayout="stereo", audioRate="48k")
        spine = ET.SubElement(seq, "spine")
        spine_els = [self.clip_el(spine, m, Fraction(m["_f0"], FPS)) for m in tl["main"]]

        def anchor(f0):
            """连接片段挂在它起点所在的主轨片段上，offset 用该片段的素材时间表示。"""
            for m, el in zip(tl["main"], spine_els):
                if m["_f0"] <= f0 < m["_f1"]:
                    return el, self.source_start(m) + Fraction(f0 - m["_f0"], FPS)
            raise AssertionError(f0)

        for o in tl["overlays"]:
            parent, offset = anchor(o["_f0"])
            self.clip_el(parent, o, offset, lane="1", srcEnable="video")
        for c in tl["captions"]:
            parent, offset = anchor(c["_f0"])
            self.title_el(parent, c["text"], "caption", offset, c["_f1"] - c["_f0"], 2)
        for t in tl["texts"]:
            parent, offset = anchor(t["_f0"])
            self.title_el(parent, t["text"], t["style"], offset, t["_f1"] - t["_f0"], 3)
        ET.indent(self.root)
        for body in self.root.iter("text"):  # <text> 是混合内容，缩进空白会变成标题里的字
            body.text = None
            for child in body:
                child.tail = None
        return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n' + ET.tostring(self.root, encoding="unicode") + "\n"


def srt(captions):
    def ts(f):
        ms = round(f * 1000 / FPS)
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    return "".join(f"{i}\n{ts(c['_f0'])} --> {ts(c['_f1'])}\n{c['text']}\n\n" for i, c in enumerate(captions, 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--style", required=True)
    args = ap.parse_args()
    pkg = Path(args.package).resolve()
    tl = expand(pkg)
    write_json(pkg / "timeline.json", public(tl))
    (pkg / "timeline.txt").write_text(describe(tl), encoding="utf-8")
    xml = Project(tl, load_clips(pkg), load_json(args.style)).build(pkg.parent.name, f"{pkg.name} {tl['title']}")
    (pkg / "project.fcpxml").write_text(xml, encoding="utf-8")
    (pkg / "subtitles.srt").write_text(srt(tl["captions"]), encoding="utf-8")
    print(f"{pkg / 'project.fcpxml'}：{len(tl['main'])} 段主轨，{len(tl['overlays'])} 段空镜覆盖，"
          f"{len(tl['captions'])} 条字幕，{len(tl['texts'])} 条文字，时长 {tl['duration']:.2f}s")


if __name__ == "__main__":
    main()
