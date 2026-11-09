---
name: short-video-editing
description: Turn a batch of raw phone footage (素材) into vertical short-video publish packages — a ready-to-post final.mp4, Final Cut Pro project (FCPXML), captions, covers, per-platform copy — or write a shot list (拍摄清单) for the next shoot. Use when editing/剪辑 footage under footage/, making 短视频, or planning a shoot.
---

# 竖屏短视频剪辑

把 `footage/<批次>/` 的原片做成**发布包**：`final.mp4` 可以直接发布，想精修时用户把 FCPXML 导入 Final Cut Pro。你负责判断：挑镜头、删口播废话、排顺序、写方案和文案；确定性的工作交给 `scripts/`。

## 约定

- 在项目根目录运行。`S=.agents/skills/short-video-editing/scripts`，脚本一律 `uv run $S/<脚本>.py …`，用法写在各脚本的文件头。
- 目录（批次名形如 `2026-11-10_秋季新品`）：

  | 路径 | 内容 |
  | --- | --- |
  | `footage/<批次>/` | 原片，只读；可以按拍摄人分一层子目录（如 `doudou/`），整批不能重名；可选 `brief.md` 写朋友想表达什么 |
  | `output/<批次>/plan.md` | 剪辑方案，唯一的确认点 |
  | `output/<批次>/work/` | `clips.json`、`sheets/`（联系表）、`transcripts/` |
  | `output/<批次>/<NN-短名>/` | 一个发布包：`final.mp4`（成片）、`edit.json`、`project.fcpxml`、`subtitles.srt`、两张封面、`post.md`，以及自查用的 `timeline.txt`、`storyboard.jpg`、`preview.mp4`、`cuts.jpg` |
  | `brand/brand.md`、`brand/style.json` | 品牌规范与字幕/封面样式 |
  | `shot-lists/<批次>.md` | 拍摄清单 |

- 规格：竖屏 1080×1920、30fps、SDR Rec.709；混剪 15–30 秒，口播 30–60 秒。iPhone 的 HLG HDR 素材由脚本自动转成 SDR（联系表、分镜、预览、封面、成片都是），不用另行处理。
- 剪辑规则已由脚本实现，写方案时据此预期结果：
  - 口播：保留句之间超过 0.4 秒的停顿会被剪掉。
  - 跳剪：同一素材前后两段不连续就是跳剪。优先用同批空镜盖住；没盖住的，脚本会自动推近，在 1.0 和 1.12 倍之间切换。
  - 混剪：不卡点，保留现场声，音乐由用户发布时从平台曲库添加。
- `brand.md` 里标着“待提供”的信息（店名、地址、语气等）：文案里用通用说法代替，并在汇报里列出缺了哪些。

## 剪辑一批素材

1. **读素材**：运行 `probe.py footage/<批次> output/<批次>/work/clips.json`，再读 `brand/brand.md`、`brand/style.json` 和 `brief.md`（如果有）。
   完成标准：每条素材的警告（HDR、横屏、帧率、无音轨）都已记下；报素材重名时，请用户改名后重跑。
2. **看镜头**：运行 `contact_sheet.py output/<批次>/work/clips.json output/<批次>/work/sheets`，用 Read 逐张看联系表（长素材会拆成 `<名>-2.jpg` 等多张），每条素材记一行：拍的是什么、可用区间、毛病（虚焦、过曝、抖动、穿帮、可识别的顾客正脸）。
   App 二次导出的成片（`copy_*`、`export_*` 之类，带烧录字幕、贴纸或背景音乐）和聊天软件转存的低清件不当原片用，在方案里列出并建议请朋友补原片。
   完成标准：每条素材都有一行记录。
3. **转写口播**：对有人说话的素材运行 `transcribe.py footage/<批次>/<素材> output/<批次>/work/transcripts/<素材名去扩展名>.json`，再读同名 `.txt`。
   完成标准：每条口播素材都有转写稿。
4. **起草**：决定这批出几条视频，每条建一个发布包目录，按 [references/edit-json.md](references/edit-json.md) 写 `edit.json`。然后运行 `storyboard.py <包>`，读 `timeline.txt`，用 Read 看 `storyboard.jpg`，反复调整到满意。
   - 口播：`talk.keep` 里去掉重复、口误、语气词所在的句子。
   - 跳剪：按 `timeline.txt` 列出的时间点安排 `overlays`，用和那句话内容相关的空镜。
   完成标准：每条视频的时长在规格内，或者偏离的原因已写进方案。
5. **确认点**：按 [references/plan-template.md](references/plan-template.md) 写 `output/<批次>/plan.md`，请用户确认后停下。用户确认之前，不运行 build、preview、cover。
6. **出发布包**：用户确认后，先把反馈改进 `edit.json`，再对每个包依次做：
   1. 运行 `build.py <包> --style brand/style.json`。
   2. 运行 `preview.py <包>`，用 Read 看 `cuts.jpg`。如果切点切断了动作、停在眨眼上，或者空镜和说的话对不上，就回到 `edit.json` 调整。
   3. 运行 `cover.py <包> --style brand/style.json`，用 Read 看两张封面。
   4. 运行 `render.py <包> --style brand/style.json` 渲染 `final.mp4`，从中抽开头标题、结尾文字各一帧看，确认字没被裁、颜色正常。
   5. 按 [references/post-template.md](references/post-template.md) 写 `post.md`。
   6. 运行 `check.py <包>`。

   完成标准：每个包都有 `final.mp4`，`check.py` 通过，`cuts.jpg`、封面和成片抽帧都看过。
7. **汇报**，包括：
   - 每个发布包的路径、时长，以及 `check.py` 的提醒；
   - `final.mp4` 可以直接发布（不含音乐，发布时从平台曲库加）；想精修再导入 FCP。导入方式：FCP 里用「文件 › 导入 › XML…」选 `project.fcpxml`。工程直接引用 `footage/` 里的原片，所以原片不能移动、改名；
   - 可选的 FCP 精修（调色、调整标题），以及品牌信息缺了哪些。

## 出拍摄清单

用户说明主题，或给出想拍的内容时，按 [references/shot-list-template.md](references/shot-list-template.md) 写 `shot-lists/<YYYY-MM-DD_主题>.md`。
完成标准：清单里的镜头够剪出约定类型的视频（混剪至少 10 个镜头；口播写清讲哪几点），拍摄要求一条不少。
