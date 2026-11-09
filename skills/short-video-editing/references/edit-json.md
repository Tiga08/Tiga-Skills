# edit.json：剪辑清单

每个发布包一份，放在 `output/<批次>/<NN-短名>/edit.json`。脚本从这里展开出逐帧对齐的时间线；字段错误时脚本会报出哪一项、为什么。时间都以秒为单位：`in`/`out`/`t` 是素材内的时间，`at`/`start`/`end` 是成片时间线上的时间。

## 通用字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | 是 | 视频标题，用作 FCP 工程名和封面的默认文字 |
| `type` | 是 | `montage`（氛围混剪）或 `talking`（口播） |
| `overlays` | 否 | 盖在主轨上的空镜，只用画面、不用声音：`{"clip", "in", "out", "at"}` |
| `texts` | 否 | 标题文字：`{"text", "start", "end", "style"}`，`style` 一般用 `headline`（顶部大字） |
| `cover` | 是 | 封面：`{"clip", "t", "title"}`，取 `clip` 在 `t` 秒处的画面，`title` 写封面字 |

`texts` 和 `cover.title` 超过每行字数（`style.json` 的 `maxChars`）时会按字数均分断行，可能把词拆开；用 `\n` 手动断在意群之间，如 `"每天只做50杯\n桂花拿铁"`。

`clip` 一律写素材文件名（如 `IMG_0103.MOV`），要和 `work/clips.json` 里的 `name` 一致。

## montage：氛围混剪

`segments` 按播放顺序列出主轨片段：`{"clip", "in", "out"}`。

- 每段 1.5–3 秒，动作完整：倒奶从开始到拉花成形，不要切在中途。
- 景别交替（全景 → 特写 → 中景），同一条素材不连着用两段。
- 开头 2 秒内放最抓眼的镜头（拉花、出杯、蒸汽），标题文字压在上面。

```json
{
  "title": "秋天的第一杯拿铁",
  "type": "montage",
  "segments": [
    {"clip": "IMG_0108.MOV", "in": 1.0, "out": 3.5},
    {"clip": "IMG_0103.MOV", "in": 1.5, "out": 5.0}
  ],
  "texts": [{"text": "秋天的第一杯拿铁", "start": 0, "end": 2.5, "style": "headline"}],
  "cover": {"clip": "IMG_0103.MOV", "t": 4.0, "title": "秋天的第一杯拿铁"}
}
```

## talking：口播

`talk` 指定口播素材和要保留的句子；主轨片段和字幕由脚本按转写稿生成，不写 `segments`。

- `talk.clip`：口播素材名，必须已经运行过 `transcribe.py`。
- `talk.keep`：要保留的句子 id（转写稿 `.txt` 里的 `u1`、`u2`…），按播放顺序排列。删掉的句子就是剪掉的内容：重复说的取说得最好的一遍；口误、“呃”“那个”所在的句子删掉；整句都在跑题的也删。删句粒度是一个短句，删掉后相邻短句会自动拼接。
- `overlays`：用来盖跳剪。`at` 取 `timeline.txt` 里跳剪时间点前约 0.5 秒，长度 1–1.5 秒，前后至少要盖过跳剪点 0.1 秒，才算盖住。空镜内容要和那句话对应，讲到豆子就配咖啡豆。

```json
{
  "title": "桂花拿铁上新",
  "type": "talking",
  "talk": {"clip": "IMG_0200.MOV", "keep": ["u1", "u2", "u3", "u6", "u7", "u8"]},
  "overlays": [{"clip": "IMG_0107.MOV", "in": 1.0, "out": 2.0, "at": 2.2}],
  "texts": [{"text": "桂花拿铁上新", "start": 0, "end": 2.5, "style": "headline"}],
  "cover": {"clip": "IMG_0200.MOV", "t": 2.0, "title": "桂花拿铁上新了"}
}
```

写完运行 `storyboard.py <包>`：`timeline.txt` 列出主轨、跳剪（是否已盖住）、字幕和删改稿，`storyboard.jpg` 是每段的代表帧。改了 `edit.json` 就重新运行。
