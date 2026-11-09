"""脚本共用：素材信息、时间换算、把 edit.json 展开成逐帧对齐的时间线。只依赖标准库。

目录约定（以一批素材为单位）：
  output/<批次>/work/clips.json            probe.py 产出
  output/<批次>/work/transcripts/<名>.json  transcribe.py 产出
  output/<批次>/<NN-短名>/edit.json         agent 写的剪辑清单（一个发布包一个目录）
"""

import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

FPS = 30                  # 时间线帧率
WIDTH, HEIGHT = 1080, 1920
PAD_BEFORE = 0.08         # 口播片段起点前留的余量（秒）
PAD_AFTER = 0.12          # 口播片段终点后留的余量（秒）
MAX_PAUSE = 0.4           # 相邻保留句之间超过这个长度的停顿会被剪掉
PUNCH_IN = 1.12           # 没被空镜盖住的跳剪：之后的片段在 1.0 和这个倍数之间切换
COVER_MARGIN = 3          # 空镜要在跳剪点前后各多盖住几帧才算“盖住”
CAPTION_MAX_CHARS = 14    # 每条字幕最多字数（含合并短句时加的空格）
CAPTION_HOLD = 0.15       # 字幕在最后一个字之后多停留的秒数
AUDIO_RATE = 48000
# HLG HDR → SDR Rec.709。本机 ffmpeg 没有 zscale/libplacebo，用 colorspace 按 BT.2020 伽马近似转换，iPhone HLG 素材实测颜色正常
TO_SDR = "format=yuv420p10le,colorspace=all=bt709:itrc=bt2020-10:iprimaries=bt2020:ispace=bt2020ncl:format=yuv420p"


def sdr(clip):
    """HDR 素材在滤镜链开头要加的转换（带结尾逗号）；SDR 素材返回空串。"""
    return TO_SDR + "," if clip.get("hdr") else ""


def wrap(text, max_chars):
    """文字里写了换行就保留；否则超过每行字数时均分成多行。"""
    if "\n" in text or len(text) <= max_chars:
        return text
    n = -(-len(text) // max_chars)
    size = -(-len(text) // n)
    return "\n".join(text[i:i + size] for i in range(0, len(text), size))


def fail(msg):
    print(f"错误：{msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def ffprobe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        fail(f"ffprobe 读不了 {path}：{out.stderr.strip()}")
    return json.loads(out.stdout)


def ffmpeg(*args):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *map(str, args)], capture_output=True, text=True)
    if p.returncode != 0:
        fail(f"ffmpeg 失败：{p.stderr.strip()[-2000:]}")


def work_dir(pkg):
    return Path(pkg).resolve().parent / "work"


def load_clips(pkg):
    path = work_dir(pkg) / "clips.json"
    if not path.is_file():
        fail(f"缺少 {path}，先运行 probe.py")
    return {c["name"]: c for c in load_json(path)["clips"]}


def asset_start(clip):
    """素材自带时间码时，FCP 里素材的起点是时间码而不是 0。"""
    tc = clip.get("timecode")
    if not tc:
        return Fraction(0)
    h, m, s, f = (int(x) for x in tc.replace(";", ":").split(":"))
    fps = Fraction(clip["fps"])
    return Fraction(((h * 60 + m) * 60 + s) * round(fps) + f) / fps


def fcp_time(t):
    t = Fraction(t)
    return f"{t.numerator}s" if t.denominator == 1 else f"{t.numerator}/{t.denominator}s"


def _talk_ranges(pkg, edit, get_clip):
    """口播：按保留的句子生成主轨区间。相邻且停顿不超过 MAX_PAUSE 的句子连在一起，其余在停顿处剪开。"""
    talk = edit.get("talk") or fail("type 为 talking 时必须有 talk 字段")
    clip = get_clip(talk["clip"])
    tpath = work_dir(pkg) / "transcripts" / f"{Path(talk['clip']).stem}.json"
    if not tpath.is_file():
        fail(f"缺少 {tpath}，先对 {talk['clip']} 运行 transcribe.py")
    units = load_json(tpath)["units"]
    index = {u["id"]: i for i, u in enumerate(units)}
    unknown = [k for k in talk["keep"] if k not in index]
    if unknown:
        fail(f"talk.keep 里有转写稿中不存在的句子：{unknown}")
    groups = []
    for k in talk["keep"]:
        i = index[k]
        if groups and groups[-1][-1] == i - 1 and units[i]["start"] - units[i - 1]["end"] <= MAX_PAUSE:
            groups[-1].append(i)
        else:
            groups.append([i])
    ranges = []
    for g in groups:
        a = units[g[0]]["start"] - PAD_BEFORE
        if g[0] > 0:
            a = max(a, units[g[0] - 1]["end"])
        b = units[g[-1]]["end"] + PAD_AFTER
        if g[-1] + 1 < len(units):
            b = min(b, units[g[-1] + 1]["start"])
        ranges.append((talk["clip"], max(a, 0), min(b, clip["duration"]), [units[i] for i in g]))
    return ranges, units


def _caption_lines(units):
    """把句子切成字幕行：先按标点断成短句，再把相邻短句合并到不超过 CAPTION_MAX_CHARS。"""
    phrases = []
    for u in units:
        cur = []
        for ch in u["chars"]:
            cur.append(ch)
            if ch["p"]:
                phrases.append(cur)
                cur = []
        if cur:
            phrases.append(cur)

    def text(chs):
        return "".join(c["c"] for c in chs)

    lines, buf = [], []
    for ph in phrases:
        if len(text(ph)) > CAPTION_MAX_CHARS:
            if buf:
                lines.append(buf)
                buf = []
            k = math.ceil(len(text(ph)) / CAPTION_MAX_CHARS)
            size = math.ceil(len(ph) / k)
            lines.extend([ph[i:i + size]] for i in range(0, len(ph), size))
        elif buf and len(" ".join(text(p) for p in buf)) + 1 + len(text(ph)) <= CAPTION_MAX_CHARS:
            buf.append(ph)
        else:
            if buf:
                lines.append(buf)
            buf = [ph]
    if buf:
        lines.append(buf)
    return [(" ".join(text(p) for p in line), line[0][0]["start"], line[-1][-1]["end"]) for line in lines]


def expand(pkg):
    """读取 <pkg>/edit.json，返回逐帧对齐的时间线。帧号字段 _f0/_f1 是时间线上的帧，_in 是素材内的起点（秒，Fraction）。"""
    pkg = Path(pkg).resolve()
    epath = pkg / "edit.json"
    if not epath.is_file():
        fail(f"缺少 {epath}")
    edit = load_json(epath)
    clips = load_clips(pkg)

    def get_clip(name):
        return clips.get(name) or fail(f"edit.json 引用了不存在的素材 {name}（可用素材见 work/clips.json）")

    def source_in(clip, t):
        fps = Fraction(clip["fps"])
        return Fraction(round(Fraction(t) * fps)) / fps

    def check_range(clip, a, b, where):
        if not (0 <= a < b <= clip["duration"] + 0.05):
            fail(f"{where}：{clip['name']} 的区间 {a:.3f}–{b:.3f} 起止颠倒或超出素材时长 {clip['duration']:.3f}s")

    kind = edit.get("type")
    transcript = None
    if kind == "talking":
        ranges, transcript = _talk_ranges(pkg, edit, get_clip)
    elif kind == "montage":
        ranges = [(s["clip"], s["in"], s["out"], []) for s in edit.get("segments") or fail("montage 需要 segments")]
    else:
        fail("edit.json 的 type 必须是 talking 或 montage")

    main, f = [], 0
    for name, a, b, units in ranges:
        clip = get_clip(name)
        check_range(clip, a, b, "主轨片段")
        n = round((b - a) * FPS)
        if n < 1:
            fail(f"主轨片段 {name} {a:.3f}–{b:.3f} 不足一帧")
        main.append({"clip": name, "_in": source_in(clip, a), "_f0": f, "_f1": f + n, "units": units})
        f += n
    total = f

    overlays = []
    for o in edit.get("overlays", []):
        clip = get_clip(o["clip"])
        check_range(clip, o["in"], o["out"], "空镜覆盖")
        f0, n = round(o["at"] * FPS), round((o["out"] - o["in"]) * FPS)
        if f0 < 0 or f0 + n > total:
            fail(f"空镜覆盖 {o['clip']} 放在 {o['at']}s、长 {n / FPS:.2f}s，超出成片 {total / FPS:.2f}s")
        overlays.append({"clip": o["clip"], "_in": source_in(clip, o["in"]), "_f0": f0, "_f1": f0 + n})

    # 跳剪：同一素材前后两段不连续。被空镜盖住就不处理，否则切换推近倍数
    cuts, zoom = [], 1.0
    main[0]["zoom"] = zoom
    for prev, cur in zip(main, main[1:]):
        prev_end = prev["_in"] + Fraction(prev["_f1"] - prev["_f0"], FPS)
        if prev["clip"] == cur["clip"] and abs(prev_end - cur["_in"]) >= Fraction(1, FPS):
            covered = any(o["_f0"] <= cur["_f0"] - COVER_MARGIN and o["_f1"] >= cur["_f0"] + COVER_MARGIN
                          for o in overlays)
            cuts.append({"t": cur["_f0"] / FPS, "covered": covered})
            if not covered:
                zoom = PUNCH_IN if zoom == 1.0 else 1.0
        cur["zoom"] = zoom

    captions = []
    for m in main:
        def to_frame(t):
            return m["_f0"] + (Fraction(t) - m["_in"]) * FPS
        for text, a, b in _caption_lines(m["units"]):
            f0 = max(m["_f0"], round(to_frame(a)))
            f1 = min(m["_f1"], round(to_frame(b + CAPTION_HOLD)))
            captions.append({"text": text, "_f0": f0, "_f1": f1})
    for a, b in zip(captions, captions[1:]):
        a["_f1"] = min(a["_f1"], b["_f0"])
    captions = [c for c in captions if c["_f1"] > c["_f0"]]

    texts = []
    for t in edit.get("texts", []):
        style = t.get("style", "headline")
        f0, f1 = round(t["start"] * FPS), round(t["end"] * FPS)
        if style not in ("headline", "caption"):
            fail(f"texts 的 style 只能是 headline 或 caption：{t}")
        if not 0 <= f0 < f1 <= total:
            fail(f"文字 “{t['text']}” 的时间 {t['start']}–{t['end']} 超出成片 {total / FPS:.2f}s")
        texts.append({"text": t["text"], "style": style, "_f0": f0, "_f1": f1})

    return {"title": edit.get("title", pkg.name), "type": kind, "fps": FPS, "duration": total / FPS,
            "_frames": total, "main": main, "overlays": overlays, "captions": captions, "texts": texts,
            "cuts": cuts, "cover": edit.get("cover"), "_transcript": transcript,
            "_keep": (edit.get("talk") or {}).get("keep", [])}


def compose(tl, clips, w, h):
    """把时间线拼成 ffmpeg 的输入参数和 filter_complex：主轨按顺序拼接（连同现场声），空镜只取画面按时间叠加，
    HDR 素材先转 SDR。返回 (inputs, graph, 视频输出标签, 音频输出标签)；调用方可继续往 graph 里追加。"""
    inputs, graph = [], []

    def add_input(item):
        c = clips[item["clip"]]
        n = item["_f1"] - item["_f0"]
        idx = sum(1 for a in inputs if a == "-i")
        inputs.extend(["-ss", f"{float(item['_in']):.4f}", "-t", f"{n / FPS + 0.5:.4f}", "-i", c["path"]])
        return idx, n, c

    def video(idx, n, c, zoom, out):
        z = f",scale=iw*{zoom}:ih*{zoom},crop={w}:{h}" if zoom != 1.0 else ""
        graph.append(f"[{idx}:v]{sdr(c)}fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}{z},"
                     f"setsar=1,format=yuv420p,trim=end_frame={n},setpts=PTS-STARTPTS[{out}]")

    concat = []
    for i, m in enumerate(tl["main"]):
        idx, n, c = add_input(m)
        video(idx, n, c, m["zoom"], f"v{i}")
        samples = round(Fraction(n, FPS) * AUDIO_RATE)
        src = f"[{idx}:a]" if c["has_audio"] else f"anullsrc=r={AUDIO_RATE}:cl=stereo,"
        graph.append(f"{src}aresample={AUDIO_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo,apad,"
                     f"atrim=end_sample={samples},asetpts=N/SR/TB[a{i}]")
        concat.append(f"[v{i}][a{i}]")
    graph.append(f"{''.join(concat)}concat=n={len(concat)}:v=1:a=1[base0][aout]")

    last = "base0"
    for j, o in enumerate(tl["overlays"]):
        idx, n, c = add_input(o)
        video(idx, n, c, 1.0, f"o{j}")
        t0 = o["_f0"] / FPS
        graph.append(f"[o{j}]setpts=PTS+{t0:.4f}/TB[os{j}]")
        graph.append(f"[{last}][os{j}]overlay=eof_action=pass:enable='between(t,{t0:.4f},{o['_f1'] / FPS - 0.001:.4f})'"
                     f"[base{j + 1}]")
        last = f"base{j + 1}"
    return inputs, graph, last, "aout"


def public(tl):
    """时间线转成可写入 timeline.json 的普通数值。"""
    def item(x):
        out = {k: v for k, v in x.items() if not k.startswith("_") and k != "units"}
        out["t0"], out["t1"] = round(x["_f0"] / FPS, 4), round(x["_f1"] / FPS, 4)
        if "_in" in x:
            out["in"] = round(float(x["_in"]), 4)
            out["out"] = round(float(x["_in"] + Fraction(x["_f1"] - x["_f0"], FPS)), 4)
        if x.get("units"):
            out["units"] = [u["id"] for u in x["units"]]
        return out
    return {"title": tl["title"], "type": tl["type"], "fps": FPS, "width": WIDTH, "height": HEIGHT,
            "duration": round(tl["duration"], 4),
            **{k: [item(x) for x in tl[k]] for k in ("main", "overlays", "captions", "texts")},
            "cuts": tl["cuts"], "cover": tl["cover"]}


def describe(tl):
    """timeline.txt：给人和 agent 看的时间线摘要。"""
    p = public(tl)
    lines = [f"{p['title']}（{p['type']}，{p['duration']:.2f}s，{WIDTH}x{HEIGHT}@{FPS}）", "", "主轨："]
    for i, m in enumerate(p["main"], 1):
        zoom = f"  推近 {m['zoom']}" if m["zoom"] != 1.0 else ""
        units = f"  {' '.join(m['units'])}" if m.get("units") else ""
        lines.append(f"  #{i:<2} {m['t0']:6.2f}–{m['t1']:6.2f}  {m['clip']}  {m['in']:.2f}–{m['out']:.2f}{zoom}{units}")
    if p["cuts"]:
        lines += ["", "跳剪："]
        lines += [f"  {c['t']:6.2f}s  {'已被空镜盖住' if c['covered'] else '未盖住 → 推近切换'}" for c in p["cuts"]]
    if p["overlays"]:
        lines += ["", "空镜覆盖（只用画面）："]
        lines += [f"  {o['t0']:6.2f}–{o['t1']:6.2f}  {o['clip']}  {o['in']:.2f}–{o['out']:.2f}" for o in p["overlays"]]
    if p["captions"]:
        lines += ["", "字幕："]
        lines += [f"  {c['t0']:6.2f}–{c['t1']:6.2f}  {c['text']}" for c in p["captions"]]
    if p["texts"]:
        lines += ["", "文字："]
        lines += [f"  {t['t0']:6.2f}–{t['t1']:6.2f}  [{t['style']}] {t['text']}" for t in p["texts"]]
    if tl["_transcript"]:
        keep = set(tl["_keep"])
        lines += ["", "口播删改稿（~~删除线~~ 为剪掉的句子）："]
        lines += ["  " + " ".join(f"{u['text']}" if u["id"] in keep else f"~~{u['text']}~~"
                                for u in tl["_transcript"])]
    return "\n".join(lines) + "\n"
