# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["funasr>=1.2", "torch", "torchaudio", "modelscope", "opencc-python-reimplemented"]
# ///
"""中文口播转写：FunASR paraformer-zh（带 VAD 与标点），输出逐字时间戳。

按标点断句，句内超过 MAX_PAUSE 的停顿处再切开，每句一个 id（u1、u2…），供 edit.json 的 talk.keep 引用。
同时写一份 .txt 摘要给人和 agent 阅读。首次运行会下载约 2GB 模型到 ~/.cache/modelscope。

用法：uv run transcribe.py <视频或音频> output/<批次>/work/transcripts/<素材名>.json
"""

import io
import sys
import tempfile
import time
import unicodedata
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from common import MAX_PAUSE, ffmpeg, write_json

ENGINE = "funasr/paraformer-zh"


def tokenize(text):
    """把句子拆成 [字或英文词, 其后的标点]，与 FunASR 的逐字时间戳一一对应。"""
    toks, in_word = [], False
    for ch in text:
        word_char = ch.isascii() and ch.isalnum()
        if unicodedata.category(ch).startswith("P"):
            if toks:
                toks[-1][1] += ch
        elif ch.isspace():
            pass
        elif word_char and in_word:
            toks[-1][0] += ch
        else:
            toks.append([ch, ""])
        in_word = word_char
    return toks


def units_from(sentences, t2s):
    units = []
    for s in sentences:
        toks = tokenize(s["text"])
        ts = s["timestamp"]
        if len(toks) != len(ts):  # 罕见：对不上时在句子起止之间均分
            step = (s["end"] - s["start"]) / max(len(toks), 1)
            ts = [[s["start"] + i * step, s["start"] + (i + 1) * step] for i in range(len(toks))]
        chars = [{"c": t2s.convert(c), "p": p, "start": a / 1000, "end": b / 1000} for (c, p), (a, b) in zip(toks, ts)]
        cur = []
        for ch in chars:
            if cur and ch["start"] - cur[-1]["end"] > MAX_PAUSE:
                units.append(cur)
                cur = []
            cur.append(ch)
        if cur:
            units.append(cur)
    return [{"id": f"u{i}", "start": u[0]["start"], "end": u[-1]["end"],
             "text": "".join(c["c"] + c["p"] for c in u), "chars": u} for i, u in enumerate(units, 1)]


def summary(name, units):
    lines = [f"# {name} 转写（{ENGINE}），超过 {MAX_PAUSE}s 的停顿单独标出"]
    for prev, u in zip([None] + units, units):
        if prev and u["start"] - prev["end"] > MAX_PAUSE:
            lines.append(f"      ⋯ 停顿 {u['start'] - prev['end']:.2f}s")
        lines.append(f"{u['id']:<5} {u['start']:6.2f}–{u['end']:6.2f}  {u['text']}")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    media, out = Path(sys.argv[1]), Path(sys.argv[2])
    if not media.is_file():
        sys.exit(f"错误：找不到 {media}")

    from opencc import OpenCC

    t = time.time()
    noise = io.StringIO()  # FunASR 与 modelscope 的日志、进度条很长：先收住，出错时再打印
    with tempfile.TemporaryDirectory() as tmp, redirect_stdout(noise), redirect_stderr(noise):
        wav = Path(tmp) / "a.wav"
        ffmpeg("-i", media, "-vn", "-ar", 16000, "-ac", 1, wav)
        try:
            from funasr import AutoModel
            model = AutoModel(model="paraformer-zh", vad_model="fsmn-vad", punc_model="ct-punc", device="cpu",
                              disable_update=True, disable_pbar=True, disable_log=True)
            res = model.generate(input=str(wav), sentence_timestamp=True, disable_pbar=True)[0]
        except Exception:
            sys.__stderr__.write(noise.getvalue())
            raise
    units = units_from(res.get("sentence_info", []), OpenCC("t2s"))
    write_json(out, {"clip": media.name, "engine": ENGINE, "units": units})
    out.with_suffix(".txt").write_text(summary(media.name, units), encoding="utf-8")
    print(f"{media.name}：{len(units)} 句，用时 {time.time() - t:.1f}s → {out}")


if __name__ == "__main__":
    main()
