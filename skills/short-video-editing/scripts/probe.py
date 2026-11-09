# /// script
# requires-python = ">=3.11"
# ///
"""读取一批素材的技术信息，写入 clips.json，并提示需要注意的素材。

素材可以直接放在批次目录里，也可以按拍摄人分进一层子目录（如 footage/<批次>/doudou/），子目录名记在 folder 字段。
edit.json 只用文件名引用素材，所以整批里不能有同名文件。

用法：uv run probe.py footage/<批次> output/<批次>/work/clips.json
"""

import sys
from fractions import Fraction
from pathlib import Path

from common import FPS, ffprobe, write_json

VIDEO_EXT = {".mov", ".mp4", ".m4v"}
COMMON_FPS = [Fraction(24000, 1001), 24, 25, Fraction(30000, 1001), 30, 50, Fraction(60000, 1001), 60, 120, 240]


def frame_rate(stream):
    """取平均帧率并就近归到常见帧率（手机素材常是可变帧率）。"""
    for key in ("avg_frame_rate", "r_frame_rate"):
        raw = stream.get(key, "0/0")
        if raw not in ("0/0", "0/1"):
            fps = Fraction(raw)
            best = min(COMMON_FPS, key=lambda c: abs(Fraction(c) - fps))
            return Fraction(best) if abs(Fraction(best) - fps) / fps < 0.02 else fps
    return Fraction(FPS)


def probe(path, folder):
    info = ffprobe(path)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        return None
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    rotation = next((int(d["rotation"]) for d in video.get("side_data_list", []) if "rotation" in d), 0)
    w, h = video["width"], video["height"]
    if rotation % 180:
        w, h = h, w
    pix = video.get("pix_fmt", "")
    transfer = video.get("color_transfer", "")
    dovi = any("DOVI" in d.get("side_data_type", "") for d in video.get("side_data_list", []))
    timecode = video.get("tags", {}).get("timecode") or info["format"].get("tags", {}).get("timecode")
    for s in info["streams"]:
        timecode = timecode or s.get("tags", {}).get("timecode")
    fps = frame_rate(video)
    return {
        "name": path.name,
        "folder": folder,
        "path": str(path.resolve()),
        "duration": round(float(info["format"]["duration"]), 4),
        "width": w,
        "height": h,
        "rotation": rotation,
        "fps": str(fps),
        "codec": video["codec_name"],
        "bit_depth": 10 if ("10" in pix or pix == "p010le") else 8,
        "color_transfer": transfer,
        "hdr": transfer in ("arib-std-b67", "smpte2084") or dovi,
        "has_audio": audio is not None,
        "audio_channels": int(audio["channels"]) if audio else 0,
        "audio_rate": int(audio["sample_rate"]) if audio else 0,
        "timecode": timecode,
    }


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    if not folder.is_dir():
        sys.exit(f"错误：素材目录不存在 {folder}")
    def videos(d):
        return sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXT and not p.name.startswith("."))
    files = [(p, "") for p in videos(folder)]
    for sub in sorted(d for d in folder.iterdir() if d.is_dir() and not d.name.startswith(".")):
        files += [(p, sub.name) for p in videos(sub)]
    seen = {}
    for p, _ in files:
        seen.setdefault(p.name, []).append(p)
    dups = {n: ps for n, ps in seen.items() if len(ps) > 1}
    if dups:
        sys.exit("错误：素材重名，edit.json 无法区分，请先改名：\n" + "\n".join(
            f"  {n}：{'、'.join(str(p.relative_to(folder)) for p in ps)}" for n, ps in dups.items()))
    clips = [c for c in (probe(p, sub) for p, sub in files) if c]
    if not clips:
        sys.exit(f"错误：{folder} 里没有视频文件")
    write_json(out, {"footage": str(folder.resolve()), "clips": clips})

    for c in clips:
        notes = []
        if c["hdr"]:
            notes.append("HDR：脚本出图和成片会自动转成 SDR；提醒朋友拍摄时关闭 HDR 视频")
        if c["width"] > c["height"]:
            notes.append("横屏：时间线会居中裁成竖屏")
        if Fraction(c["fps"]) != FPS:
            notes.append(f"帧率 {float(Fraction(c['fps'])):.3f}（时间线 {FPS}fps）")
        if not c["has_audio"]:
            notes.append("没有音轨")
        print(f"{(c['folder'] + '/' if c['folder'] else '') + c['name']:<28} {c['duration']:7.2f}s  {c['width']}x{c['height']}  {c['codec']} {c['bit_depth']}bit"
              + (f"  ⚠ {'；'.join(notes)}" if notes else ""))
    print(f"共 {len(clips)} 条，写入 {out}")


if __name__ == "__main__":
    main()
