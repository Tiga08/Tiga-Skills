#!/usr/bin/env python3
"""Probe Enterprise WeChat / WeCom document links for accessible metadata.

This script intentionally does not bypass access controls. It only requests
public/anonymous pages and endpoints, then reports what can be verified.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)
MAX_READ_BYTES = 4 * 1024 * 1024
TIMEOUT_SECONDS = 15


def fetch_url(url: str, referer: str | None = None) -> dict[str, Any]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_READ_BYTES)
            return {
                "ok": True,
                "status": getattr(response, "status", None),
                "url": response.geturl(),
                "content_type": response.headers.get("Content-Type", ""),
                "body": decode_body(raw, response.headers.get_content_charset()),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_READ_BYTES)
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "content_type": exc.headers.get("Content-Type", "") if exc.headers else "",
            "body": decode_body(raw, exc.headers.get_content_charset() if exc.headers else None),
            "error": f"HTTP {exc.code}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "content_type": "",
            "body": "",
            "error": str(exc),
        }


def decode_body(raw: bytes, charset: str | None) -> str:
    for candidate in (charset, "utf-8", "gb18030"):
        if not candidate:
            continue
        try:
            return raw.decode(candidate, errors="replace")
        except LookupError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_doc_id(parsed_url: urllib.parse.ParseResult, query: dict[str, list[str]]) -> str | None:
    for key in ("docid", "id", "padid", "doc_id"):
        value = first_query_value(query, key)
        if value:
            return value

    path_parts = [part for part in parsed_url.path.split("/") if part]
    for part in path_parts:
        if re.match(r"^[A-Za-z0-9]+_[A-Za-z0-9_-]+$", part):
            return part
    return None


def first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    for actual_key, values in query.items():
        if actual_key.lower() == key.lower() and values:
            return values[0]
    return None


def parse_input_url(url: str) -> tuple[str | None, str | None]:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    doc_id = extract_doc_id(parsed, query)
    scode = first_query_value(query, "scode") or first_query_value(query, "k")
    return doc_id, scode


def parse_metadata(text: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    stripped = text.strip()

    if stripped.startswith("{") or stripped.startswith("["):
        try:
            collect_from_object(json.loads(stripped), metadata)
        except json.JSONDecodeError:
            pass

    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if title_match:
        title = clean_text(title_match.group(1))
        if title:
            metadata["title"] = title

    for marker in (
        "window.basicClientVars",
        "window.__INITIAL_STATE__",
        "__INITIAL_STATE__",
        "basicClientVars",
    ):
        obj = extract_json_assignment(text, marker)
        if obj is not None:
            collect_from_object(obj, metadata)

    collect_regex_metadata(text, metadata)
    return metadata


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_json_assignment(text: str, marker: str) -> Any | None:
    index = text.find(marker)
    if index == -1:
        return None

    brace_index = text.find("{", index)
    if brace_index == -1:
        return None

    try:
        obj, _ = json.JSONDecoder().raw_decode(text[brace_index:])
        return obj
    except json.JSONDecodeError:
        return None


def collect_regex_metadata(text: str, metadata: dict[str, Any]) -> None:
    string_keys = {
        "file_id": "doc_id",
        "doc_id": "doc_id",
        "docid": "doc_id",
        "padId": "doc_id",
        "file_name": "title",
        "fileName": "title",
        "padTitle": "title",
        "corp_name": "corp_name",
        "corpName": "corp_name",
        "errmsg": "errmsg",
        "message": "message",
    }
    number_keys = {
        "file_size": "file_size",
        "fileSize": "file_size",
        "retcode": "retcode",
        "blankPageType": "blank_page_type",
    }
    bool_keys = {
        "canRead": "can_read",
        "can_read": "can_read",
        "canExport": "can_export",
        "can_export": "can_export",
        "has_login": "has_login",
        "hasLogin": "has_login",
        "isLogin": "has_login",
        "is_login": "has_login",
    }

    for source_key, target_key in string_keys.items():
        match = re.search(rf'"{re.escape(source_key)}"\s*:\s*"((?:\\.|[^"\\])*)"', text)
        if match:
            set_metadata_value(metadata, target_key, unescape_json_string(match.group(1)))

    for source_key, target_key in number_keys.items():
        match = re.search(rf'"{re.escape(source_key)}"\s*:\s*(-?\d+)', text)
        if match:
            set_metadata_value(metadata, target_key, int(match.group(1)))

    for source_key, target_key in bool_keys.items():
        match = re.search(rf'"{re.escape(source_key)}"\s*:\s*(true|false)', text, flags=re.IGNORECASE)
        if match:
            set_metadata_value(metadata, target_key, match.group(1).lower() == "true")


def unescape_json_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value


def collect_from_object(obj: Any, metadata: dict[str, Any]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized = normalize_key(key)
            if normalized and is_scalar(value):
                set_metadata_value(metadata, normalized, value)
            collect_from_object(value, metadata)
    elif isinstance(obj, list):
        for item in obj:
            collect_from_object(item, metadata)


def normalize_key(key: str) -> str | None:
    mapping = {
        "file_id": "doc_id",
        "fileid": "doc_id",
        "doc_id": "doc_id",
        "docid": "doc_id",
        "padid": "doc_id",
        "id": None,
        "file_name": "title",
        "filename": "title",
        "filetitle": "title",
        "padtitle": "title",
        "title": "title",
        "corp_name": "corp_name",
        "corpname": "corp_name",
        "file_size": "file_size",
        "filesize": "file_size",
        "canread": "can_read",
        "can_read": "can_read",
        "canexport": "can_export",
        "can_export": "can_export",
        "has_login": "has_login",
        "haslogin": "has_login",
        "islogin": "has_login",
        "is_login": "has_login",
        "retcode": "retcode",
        "errmsg": "errmsg",
        "message": "message",
        "blankpagetype": "blank_page_type",
    }
    return mapping.get(key.replace("-", "_").lower())


def is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def set_metadata_value(metadata: dict[str, Any], key: str, value: Any) -> None:
    if value in ("", None):
        return
    if key == "title" and isinstance(value, str):
        value = clean_text(value)
        if not value or value.lower() in {"blankpage", "loading"}:
            return

    current = metadata.get(key)
    if current in ("", None):
        metadata[key] = value
        return

    if key == "title" and isinstance(value, str) and title_is_better(value, str(current)):
        metadata[key] = value


def title_is_better(candidate: str, current: str) -> bool:
    generic_titles = {
        "企业微信文档",
        "腾讯文档",
        "blankpage",
        "loading",
    }
    if current in generic_titles:
        return True
    return len(candidate) > len(current) and current in candidate


def build_apply_page_url(doc_id: str, scode: str | None) -> str:
    query = {
        "docid": doc_id,
        "doctype": "doc",
    }
    if scode:
        query["k"] = scode
    return "https://doc.weixin.qq.com/txdoc/apply_page?" + urllib.parse.urlencode(query)


def build_preload_url(doc_id: str, scode: str | None) -> str:
    query = {
        "command": "1",
        "id": doc_id,
    }
    if scode:
        query["scode"] = scode
    return "https://docs.qq.com/cgi/gateway/preload?" + urllib.parse.urlencode(query)


def build_opendoc_url(doc_id: str) -> str:
    query = {
        "id": doc_id,
        "normal": "1",
        "outformat": "1",
    }
    return "https://doc.weixin.qq.com/dop-api/opendoc?" + urllib.parse.urlencode(query)


def merge_metadata(result: dict[str, Any], metadata: dict[str, Any]) -> None:
    for key in ("doc_id", "title", "corp_name", "file_size", "can_read", "can_export"):
        if key in metadata:
            set_metadata_value(result, key, metadata[key])


def determine_access_status(result: dict[str, Any], all_metadata: list[dict[str, Any]]) -> str:
    if result.get("can_read") is True:
        return "readable"

    for metadata in all_metadata:
        if metadata.get("can_read") is False:
            return "permission_required"

    for metadata in all_metadata:
        message = " ".join(
            str(metadata.get(key, ""))
            for key in ("errmsg", "message", "retcode", "blank_page_type")
        ).lower()
        if "check userinfo failed" in message or "login" in message:
            return "login_required"
        if "blankpagetype" in message or "permission" in message or "forbid" in message:
            return "permission_required"

    for metadata in all_metadata:
        if metadata.get("has_login") is False:
            return "login_required"

    return "unknown"


def probe(url: str) -> dict[str, Any]:
    doc_id, scode = parse_input_url(url)
    result: dict[str, Any] = {
        "input_url": url,
        "doc_id": doc_id,
        "scode": scode,
        "title": None,
        "corp_name": None,
        "file_size": None,
        "access_status": "unknown",
        "can_read": None,
        "can_export": None,
        "notes": [],
        "error": None,
    }
    all_metadata: list[dict[str, Any]] = []

    original = fetch_url(url)
    result["notes"].append(format_fetch_note("original URL", original))
    if original["body"]:
        metadata = parse_metadata(original["body"])
        all_metadata.append(metadata)
        merge_metadata(result, metadata)

    if not result.get("doc_id"):
        result["error"] = "Unable to parse document id from URL or page metadata."
        result["access_status"] = determine_access_status(result, all_metadata)
        return result

    doc_id = str(result["doc_id"])

    apply_url = build_apply_page_url(doc_id, scode)
    apply_page = fetch_url(apply_url, referer=url)
    result["notes"].append(format_fetch_note("apply page", apply_page))
    if apply_page["body"]:
        metadata = parse_metadata(apply_page["body"])
        all_metadata.append(metadata)
        merge_metadata(result, metadata)

    preload_url = build_preload_url(doc_id, scode)
    preload = fetch_url(preload_url, referer=url)
    result["notes"].append(format_fetch_note("preload endpoint", preload))
    if preload["body"]:
        metadata = parse_metadata(preload["body"])
        all_metadata.append(metadata)
        merge_metadata(result, metadata)

    opendoc_url = build_opendoc_url(doc_id)
    opendoc = fetch_url(opendoc_url, referer=url)
    result["notes"].append(format_fetch_note("opendoc endpoint", opendoc))
    if opendoc["body"]:
        metadata = parse_metadata(opendoc["body"])
        all_metadata.append(metadata)
        merge_metadata(result, metadata)

    result["access_status"] = determine_access_status(result, all_metadata)
    if result["access_status"] != "readable" and not result["error"]:
        result["error"] = "Document body was not available through anonymous requests."

    return result


def format_fetch_note(label: str, response: dict[str, Any]) -> str:
    status = response.get("status")
    if response.get("ok"):
        return f"Fetched {label}: HTTP {status}"
    if status:
        return f"Failed to fetch {label}: HTTP {status}"
    return f"Failed to fetch {label}: {response.get('error')}"


def print_text(result: dict[str, Any]) -> None:
    labels = [
        ("Input URL", "input_url"),
        ("Document ID", "doc_id"),
        ("Access code", "scode"),
        ("Title", "title"),
        ("Corp name", "corp_name"),
        ("File size", "file_size"),
        ("Access status", "access_status"),
        ("Can read", "can_read"),
        ("Can export", "can_export"),
        ("Error", "error"),
    ]
    for label, key in labels:
        print(f"{label}: {result.get(key)}")
    print("Notes:")
    for note in result.get("notes", []):
        print(f"- {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe a WeCom / Enterprise WeChat document link for accessible metadata.",
    )
    parser.add_argument("url", help="doc.weixin.qq.com or docs.qq.com document URL")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output")
    args = parser.parse_args(argv)

    result = probe(args.url)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
