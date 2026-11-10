"""按分块计划切分原文、拼接译文。

用法：
  python3 chunks.py split <工作区>   按 chunks.txt 把 source.md 切成 chunks/NNN.src.md（skip 块写成 NNN.skip.md）
  python3 chunks.py join <工作区>    把 header.md、各块译文 chunks/NNN.zh.md、terms.md 拼成 translation.md

chunks.txt 每行一个块：<起始行号> <translate|keep|skip> <说明>。第一块从第 1 行开始，行号严格递增，
每块到下一块起始行的前一行为止，因此 source.md 的每一行都恰好属于一块。空行和 # 开头的行忽略。
"""

import re
import sys
from pathlib import Path

ACTIONS = ("translate", "keep", "skip")
PAGE_MARKER = re.compile(r"^<!-- page \d+ -->[ \t]*(?:\n[ \t]*)?(?:\n|$)", re.M)


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def load_plan(ws):
    """返回 [(编号, 起始行, 动作, 说明)]；计划不合法时退出。"""
    path = ws / "chunks.txt"
    if not path.is_file():
        fail(f"缺少分块计划 {path}")
    plan = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 2 or not parts[0].isdigit() or parts[1] not in ACTIONS:
            fail(f"chunks.txt 第 {n} 行格式应为「<起始行号> <translate|keep|skip> <说明>」：{line}")
        start = int(parts[0])
        if not plan and start != 1:
            fail("chunks.txt 的第一块必须从第 1 行开始，否则开头的内容不属于任何块")
        if plan and start <= plan[-1][1]:
            fail(f"chunks.txt 第 {n} 行的起始行号 {start} 没有大于上一块的 {plan[-1][1]}")
        plan.append((f"{len(plan) + 1:03d}", start, parts[1], parts[2] if len(parts) > 2 else ""))
    if not plan:
        fail("chunks.txt 里没有任何块")
    return plan


def split(ws):
    plan = load_plan(ws)
    lines = (ws / "source.md").read_text(encoding="utf-8").splitlines(keepends=True)
    if plan[-1][1] > len(lines):
        fail(f"最后一块的起始行 {plan[-1][1]} 超出了 source.md 的 {len(lines)} 行")
    out = ws / "chunks"
    if any(out.glob("*.src.md")) or any(out.glob("*.skip.md")):
        fail(f"{out} 里已有分块，可能含校对修改；确需重新分块时先手动删除 {out}")
    out.mkdir(exist_ok=True)
    starts = [start for _, start, _, _ in plan] + [len(lines) + 1]
    for (num, start, action, title), end in zip(plan, starts[1:]):
        suffix = "skip" if action == "skip" else "src"
        (out / f"{num}.{suffix}.md").write_text("".join(lines[start - 1 : end - 1]), encoding="utf-8")
        print(f"{num}.{suffix}.md  第 {start}–{end - 1} 行  {action}  {title}")


def join_text(ws):
    """返回拼接后的译文；缺少部件时返回 (None, 缺少的部件列表)。"""
    missing = [name for name in ("header.md", "terms.md") if not (ws / name).is_file()]
    parts = []
    for num, _, action, _ in load_plan(ws):
        if action == "skip":
            continue
        zh = ws / "chunks" / f"{num}.zh.md"
        if zh.is_file():
            parts.append(PAGE_MARKER.sub("", zh.read_text(encoding="utf-8")).strip())
        else:
            missing.append(f"chunks/{num}.zh.md")
    if missing:
        return None, missing
    head = (ws / "header.md").read_text(encoding="utf-8").strip()
    terms = (ws / "terms.md").read_text(encoding="utf-8").strip()
    return "\n\n".join([head, *parts, terms]) + "\n", []


def join(ws):
    text, missing = join_text(ws)
    if missing:
        fail("还不能拼接，缺少：" + "、".join(missing))
    (ws / "translation.md").write_text(text, encoding="utf-8")
    print(f"已拼接 {ws / 'translation.md'}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("split", "join"):
        fail(__doc__)
    {"split": split, "join": join}[sys.argv[1]](Path(sys.argv[2]))
