#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_SOURCES = ROOT / "raw" / "sources"
DOMAIN_ALIASES = {
    "general": ("general", "通用"),
    "通用": ("general", "通用"),
    "llm-wiki": ("llm-wiki", "LLM Wiki"),
    "math": ("math", "数学"),
    "数学": ("math", "数学"),
    "physics": ("physics", "物理"),
    "物理": ("physics", "物理"),
    "tibetan-astronomy-calendar": ("tibetan-astronomy-calendar", "西藏天文历算"),
    "西藏天文历算": ("tibetan-astronomy-calendar", "西藏天文历算"),
    "modern-astronomy": ("modern-astronomy", "现代天文学"),
    "现代天文学": ("modern-astronomy", "现代天文学"),
}


def slugify(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "untitled"


def resolve_domain(domain: str | None) -> tuple[str, str]:
    if not domain:
        return "general", "通用"
    normalized = domain.strip()
    if normalized in DOMAIN_ALIASES:
        return DOMAIN_ALIASES[normalized]
    return slugify(normalized), normalized


def parse_extra_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    tags: list[str] = []
    for tag in raw_tags.split(","):
        cleaned = slugify(tag)
        if cleaned and cleaned not in tags:
            tags.append(cleaned)
    return tags


def infer_source_type(kind: str, url: str | None, local_path: str | None) -> str:
    if url:
        return "web"
    if local_path:
        return "local"
    return kind


def build_content(
    title: str,
    kind: str,
    source_type: str,
    created: str,
    domain_slug: str,
    domain_label: str,
    status: str,
    source_url: str,
    local_path: str,
    author: str,
    published: str,
    tags: list[str],
) -> str:
    tag_list = ", ".join(tags)
    return f"""---
title: {title}
kind: {kind}
source_type: {source_type}
domain: {domain_slug}
domain_label: {domain_label}
status: {status}
source_url: {source_url}
local_path: {local_path}
author: {author}
published: {published}
created: {created}
tags: [{tag_list}]
---

# {title}

## Context

为什么要收录这份资料？它与当前 wiki 的哪条主线相关？
学科归属：{domain_label}

## Locator

- Source type: `{source_type}`
- URL: {source_url or "待补"}
- Local path: {local_path or "待补"}

## Original Content Or Extract

把原文、摘录、转写或清洗后的正文放在这里。

## Notes

可补充少量人工备注，但尽量不要破坏原始内容的可追溯性。

## Wiki Integration Checklist

- [ ] 是否需要新建或更新 source summary？
- [ ] 是否需要新建或更新 concept/entity 页面？
- [ ] 是否需要补充到 `wiki/domains/{domain_slug}.md` 的网络关系？
- [ ] 是否暴露出跨学科桥接点？
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a raw source markdown stub.")
    parser.add_argument("--title", required=True, help="Human-readable source title.")
    parser.add_argument("--kind", default="article", help="Source kind, e.g. article/podcast/note.")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Creation date in YYYY-MM-DD.")
    parser.add_argument("--status", default="inbox", help="Source status, e.g. inbox/active/archived.")
    parser.add_argument(
        "--domain",
        help="Domain folder, e.g. math, physics, tibetan-astronomy-calendar, modern-astronomy.",
    )
    parser.add_argument("--slug", help="Optional filename slug.")
    parser.add_argument("--url", default="", help="Original web article URL.")
    parser.add_argument("--local-path", default="", help="Absolute or stable local path for a local source file.")
    parser.add_argument("--author", default="", help="Author, editor, or source organization.")
    parser.add_argument("--published", default="", help="Published date or bibliographic year.")
    parser.add_argument("--tags", default="", help="Comma-separated extra tags.")
    args = parser.parse_args()

    year = args.date[:4]
    slug = args.slug or slugify(args.title)
    domain_slug, domain_label = resolve_domain(args.domain)
    extra_tags = parse_extra_tags(args.tags)
    tags = [domain_slug, *[tag for tag in extra_tags if tag != domain_slug]]
    source_type = infer_source_type(args.kind, args.url, args.local_path)
    target_dir = RAW_SOURCES / domain_slug / year
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{args.date}-{slug}.md"

    if target.exists():
        raise SystemExit(f"File already exists: {target}")

    target.write_text(
        build_content(
            args.title,
            args.kind,
            source_type,
            args.date,
            domain_slug,
            domain_label,
            args.status,
            args.url,
            args.local_path,
            args.author,
            args.published,
            tags,
        ),
        encoding="utf-8",
    )
    print(target.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
