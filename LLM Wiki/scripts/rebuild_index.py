#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
INDEX = WIKI / "00-meta" / "index.md"
FRONTMATTER_FIELDS = ("title", "type", "summary", "updated")
CATEGORY_ORDER = ("meta", "domain", "source", "concept", "entity", "analysis")
CATEGORY_TITLES = {
    "meta": "Meta Pages",
    "domain": "Domain Networks",
    "source": "Source Summaries",
    "concept": "Concepts",
    "entity": "Entities",
    "analysis": "Analyses",
    "other": "Other",
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def wiki_pages() -> list[Path]:
    return sorted(
        path
        for path in WIKI.rglob("*.md")
        if path != INDEX and path.name != "log.md"
    )


def build_entry(path: Path, meta: dict[str, str]) -> str:
    title = meta.get("title") or path.stem
    summary = meta.get("summary") or "No summary yet."
    updated = meta.get("updated") or "unknown"
    rel = Path(os.path.relpath(path, INDEX.parent))
    return f"- [{title}]({rel.as_posix()}) - {summary} (updated: {updated})"


def render() -> str:
    categories: dict[str, list[tuple[str, str]]] = {key: [] for key in CATEGORY_ORDER}
    categories["other"] = []

    for path in wiki_pages():
        meta = parse_frontmatter(path)
        category = meta.get("type", "other")
        category = category if category in categories else "other"
        sort_key = (meta.get("title") or path.stem).lower()
        categories[category].append((sort_key, build_entry(path, meta)))

    lines = [
        "---",
        "title: Wiki Index",
        "type: meta",
        "status: active",
        "created: 2026-04-07",
        f"updated: {dt.date.today().isoformat()}",
        "summary: 自动生成的 wiki 索引，按页面类型列出当前知识库内容。",
        "tags: [index, meta]",
        "sources: []",
        "---",
        "",
        "# Wiki Index",
        "",
        "这个文件由 `python3 scripts/rebuild_index.py` 自动生成。",
        "",
        "## Quick Links",
        "",
        "- [Home](./home.md)",
        "- [Inbox](./inbox.md)",
        "- [Log](./log.md)",
        "",
        f"Generated on: {dt.date.today().isoformat()}",
        "",
    ]

    for category in (*CATEGORY_ORDER, "other"):
        entries = sorted(categories[category], key=lambda item: item[0])
        if not entries:
            continue
        lines.append(f"## {CATEGORY_TITLES[category]}")
        lines.append("")
        lines.extend(entry for _, entry in entries)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    INDEX.write_text(render(), encoding="utf-8")
    print(INDEX.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
