#!/usr/bin/env python3
"""检查并刷新 Claude 与 Codex 官方 skill-creator 文档快照。"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SKILL_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = SKILL_ROOT / "references" / "official"
MANIFEST_PATH = SNAPSHOT_DIR / "sources.json"
SOURCES = (
    {
        "id": "claude-skill-creator",
        "product": "Claude Code",
        "source_url": "https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md",
        "raw_url": "https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md",
        "snapshot": "claude-skill-creator.md",
    },
    {
        "id": "codex-skill-creator",
        "product": "Codex",
        "source_url": "https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md",
        "raw_url": "https://raw.githubusercontent.com/openai/skills/main/skills/.system/skill-creator/SKILL.md",
        "snapshot": "codex-skill-creator.md",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(source: dict[str, str]) -> bytes:
    request = Request(
        source["raw_url"],
        headers={"User-Agent": "tiga-update-skills/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as urllib_error:
        # 某些代理会中断 Python TLS；curl 通常能复用主机代理配置。
        result = subprocess.run(
            [
                "curl",
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                "30",
                source["raw_url"],
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise URLError(
                f"urllib={urllib_error}; curl={detail or result.returncode}"
            ) from urllib_error
        data = result.stdout
    if not data.startswith(b"---"):
        raise ValueError(f"{source['id']} 返回内容不是预期的 SKILL.md")
    return data


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
    )
    try:
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def unified_diff(path: Path, local: bytes | None, remote: bytes) -> str:
    local_text = (local or b"").decode("utf-8", errors="replace").splitlines()
    remote_text = remote.decode("utf-8", errors="replace").splitlines()
    return "\n".join(
        difflib.unified_diff(
            local_text,
            remote_text,
            fromfile=str(path),
            tofile=f"{path} (remote)",
            lineterm="",
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查或刷新官方 skill-creator 文档快照。",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="只检查远端差异（默认）")
    mode.add_argument("--update", action="store_true", help="刷新本地快照和清单")
    parser.add_argument(
        "--diff",
        action="store_true",
        help="在检查时输出完整统一 diff",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.update and args.diff:
        print("ERROR: --diff 只能与 --check 一起使用", file=sys.stderr)
        return 2

    fetched: dict[str, bytes] = {}
    try:
        for source in SOURCES:
            fetched[source["id"]] = fetch(source)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        print(f"ERROR: 官方文档检查失败：{error}", file=sys.stderr)
        return 2

    rows: list[dict[str, object]] = []
    changed_count = 0
    for source in SOURCES:
        path = SNAPSHOT_DIR / source["snapshot"]
        local = path.read_bytes() if path.is_file() else None
        remote = fetched[source["id"]]
        changed = local != remote
        if changed:
            changed_count += 1
        status = "CHANGED" if changed else "UP_TO_DATE"
        local_hash = sha256(local) if local is not None else "missing"
        remote_hash = sha256(remote)
        print(
            f"{status} {source['id']} "
            f"local={local_hash} remote={remote_hash}"
        )
        if args.diff and changed:
            print(unified_diff(path, local, remote))
        rows.append(
            {
                **source,
                "sha256": remote_hash,
                "bytes": len(remote),
            }
        )

    manifest_missing = not MANIFEST_PATH.is_file()
    if not args.update:
        if manifest_missing:
            print(f"MISSING manifest={MANIFEST_PATH}")
        print(
            "SUMMARY "
            f"changed={changed_count} manifest_missing={str(manifest_missing).lower()}"
        )
        return 1 if changed_count or manifest_missing else 0

    if changed_count == 0 and not manifest_missing:
        print("SUMMARY changed=0 written=0")
        return 0

    for source in SOURCES:
        atomic_write(
            SNAPSHOT_DIR / source["snapshot"],
            fetched[source["id"]],
        )

    manifest = {
        "schema_version": 1,
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sources": rows,
    }
    atomic_write(
        MANIFEST_PATH,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(
        "SUMMARY "
        f"changed={changed_count} written={len(SOURCES) + 1}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
