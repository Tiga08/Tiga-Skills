"""检查通过后，把工作区的 translation.md 和它引用的图片写入条目目录。

用法：python3 publish.py <工作区> <条目目录>

条目目录里已有 translation.md 时拒绝写入（里面可能有阅读标注）。入口 README.md 由 agent 另写。
"""

import shutil
import sys
from pathlib import Path

from check import HTML_IMAGE, MD_IMAGE, check, image_errors, report


def publish(ws, entry):
    target = entry / "translation.md"
    if target.exists():
        print(f"{target} 已存在，不覆盖；先和用户确认怎么处理", file=sys.stderr)
        return 1
    errors, warnings = check(ws)
    if errors:
        report(errors, warnings)
        print("检查未通过，没有写入", file=sys.stderr)
        return 1
    text = (ws / "translation.md").read_text(encoding="utf-8")
    entry.mkdir(parents=True, exist_ok=True)
    refs = list(dict.fromkeys(MD_IMAGE.findall(text) + HTML_IMAGE.findall(text)))
    for ref in refs:
        (entry / ref).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ws / ref, entry / ref)
    target.write_text(text, encoding="utf-8")
    missing = image_errors(text, entry, "translation.md")
    if missing:
        print("\n".join(missing), file=sys.stderr)
        return 1
    print(f"已写入 {target} 和 {len(refs)} 张图片")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(publish(Path(sys.argv[1]), Path(sys.argv[2])))
