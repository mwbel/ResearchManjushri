#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_SOURCES = ROOT / "raw" / "sources"
WIKI = ROOT / "wiki"
DOMAINS = WIKI / "domains"

KNOWN_DOMAIN_LABELS = {
    "general": "通用",
    "llm-wiki": "LLM Wiki",
    "math": "数学",
    "physics": "物理",
    "tibetan-astronomy-calendar": "西藏天文历算",
    "modern-astronomy": "现代天文学",
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


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    cleaned = value.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    items = []
    for item in cleaned.split(","):
        normalized = item.strip().strip("\"'")
        if normalized:
            items.append(normalized)
    return items


def rel_link(from_dir: Path, target: Path) -> str:
    return Path(os.path.relpath(target, from_dir)).as_posix()


def table_cell(value: str) -> str:
    cleaned = value.replace("\n", " ").replace("|", "\\|").strip()
    return cleaned or "未登记"


def title_for(path: Path, meta: dict[str, str]) -> str:
    return meta.get("title") or path.stem


def discovered_domains() -> list[str]:
    domains = set(KNOWN_DOMAIN_LABELS)
    if RAW_SOURCES.exists():
        for path in RAW_SOURCES.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                domains.add(path.name)
    return sorted(domains)


def raw_source_files(domain_slug: str) -> list[Path]:
    root = RAW_SOURCES / domain_slug
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.name.lower() != "readme.md" and not path.name.startswith(".")
    )


def label_from_sources(domain_slug: str, sources: list[Path] | None = None) -> str | None:
    source_paths = sources if sources is not None else raw_source_files(domain_slug)
    for path in source_paths:
        label = parse_frontmatter(path).get("domain_label", "").strip()
        if label:
            return label
    return None


def label_from_existing_domain_page(domain_slug: str) -> str | None:
    target = DOMAINS / f"{domain_slug}.md"
    if not target.exists():
        return None
    title = parse_frontmatter(target).get("title", "").strip()
    suffix = " Knowledge Network"
    if title.endswith(suffix):
        return title[: -len(suffix)]
    return title or None


def domain_label_for(domain_slug: str, sources: list[Path] | None = None) -> str:
    return (
        KNOWN_DOMAIN_LABELS.get(domain_slug)
        or label_from_sources(domain_slug, sources)
        or label_from_existing_domain_page(domain_slug)
        or domain_slug
    )


def wiki_files() -> list[Path]:
    return sorted(
        path
        for path in WIKI.rglob("*.md")
        if path.parent != DOMAINS
        and path.name not in {"index.md", "log.md"}
        and not path.name.startswith(".")
    )


def page_matches_domain(path: Path, meta: dict[str, str], domain_slug: str) -> bool:
    tags = parse_list(meta.get("tags"))
    if domain_slug in tags:
        return True

    source_refs = parse_list(meta.get("sources"))
    source_prefix = f"raw/sources/{domain_slug}/"
    if any(ref == f"raw/sources/{domain_slug}" or source_prefix in ref for ref in source_refs):
        return True

    if path.parent.name == "concepts" and path.stem == domain_slug:
        return True

    return False


def source_location(meta: dict[str, str]) -> str:
    source_url = meta.get("source_url", "").strip()
    local_path = meta.get("local_path", "").strip()
    if source_url:
        return f"[web]({source_url})"
    if local_path:
        return f"`{local_path}`"
    return "未登记"


def mermaid_label(text: str, limit: int = 34) -> str:
    compact = " ".join(text.replace('"', "'").split())
    if len(compact) > limit:
        compact = compact[: limit - 1].rstrip() + "…"
    return compact


def concept_relation_rows(pages: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    pattern = re.compile(r"^-\s+`([^`]+)`\s+--(.+?)-->\s+`([^`]+)`(?:\s+\((.+)\))?")
    seen = set()
    for path in pages:
        if parse_frontmatter(path).get("type") != "concept":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line.strip())
            if not match:
                continue
            source, relation, target, evidence = match.groups()
            key = (source, relation, target)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "source": source,
                    "relation": relation,
                    "target": target,
                    "evidence": evidence or "",
                    "page": str(path.relative_to(ROOT)),
                }
            )
    return rows


def render_concept_mermaid(relations: list[dict[str, str]]) -> list[str]:
    lines = ["```mermaid", "flowchart LR"]
    if not relations:
        lines.append('    Seed["等待概念关系抽取"]')
    for index, relation in enumerate(relations[:18], start=1):
        source_id = f"C{index}A"
        target_id = f"C{index}B"
        label = mermaid_label(relation["relation"], 16)
        lines.append(f'    {source_id}["{mermaid_label(relation["source"])}"] -- "{label}" --> {target_id}["{mermaid_label(relation["target"])}"]')
    lines.append("```")
    return lines


def relation_table(relations: list[dict[str, str]]) -> list[str]:
    rows = [
        "| Source Concept | Relation | Target Concept | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for relation in relations[:30]:
        evidence = relation["evidence"] or f"`{relation['page']}`"
        rows.append(
            "| "
            + " | ".join(
                [
                    table_cell(relation["source"]),
                    table_cell(relation["relation"]),
                    table_cell(relation["target"]),
                    table_cell(evidence),
                ]
            )
            + " |"
        )
    if len(rows) == 2:
        rows.append("| 待补 | 待补 | 待补 | 自动概念抽取后生成 |")
    return rows


def source_rows(domain_page: Path, sources: list[Path]) -> list[str]:
    rows = [
        "| Status | Kind | Title | Locator | Raw File |",
        "| --- | --- | --- | --- | --- |",
    ]
    for path in sources:
        meta = parse_frontmatter(path)
        title = title_for(path, meta)
        kind = meta.get("kind") or meta.get("source_type") or meta.get("type") or "source"
        status = meta.get("status") or "unknown"
        rel = rel_link(domain_page.parent, path)
        rows.append(
            "| "
            + " | ".join(
                [
                    table_cell(status),
                    table_cell(kind),
                    f"[{table_cell(title)}]({rel})",
                    source_location(meta),
                    f"`{table_cell(str(path.relative_to(ROOT)))}`",
                ]
            )
            + " |"
        )
    if len(rows) == 2:
        rows.append("| inbox | source | 暂无已登记资料 | 未登记 | `raw/sources/...` |")
    return rows


def wiki_rows(domain_page: Path, pages: list[Path]) -> list[str]:
    rows = [
        "| Type | Title | Summary | Wiki Page |",
        "| --- | --- | --- | --- |",
    ]
    for path in pages:
        meta = parse_frontmatter(path)
        page_type = meta.get("type") or "other"
        title = title_for(path, meta)
        summary = meta.get("summary") or "No summary yet."
        rel = rel_link(domain_page.parent, path)
        rows.append(
            "| "
            + " | ".join(
                [
                    table_cell(page_type),
                    f"[{table_cell(title)}]({rel})",
                    table_cell(summary),
                    f"`{table_cell(str(path.relative_to(ROOT)))}`",
                ]
            )
            + " |"
        )
    if len(rows) == 2:
        rows.append("| concept | 暂无页面 | 等待首批资料 ingest 后生成 | `wiki/...` |")
    return rows


def render_mermaid(domain_label: str, sources: list[Path], pages: list[Path]) -> list[str]:
    lines = [
        "```mermaid",
        "flowchart LR",
        f'    D["{mermaid_label(domain_label)}"]',
    ]
    for index, path in enumerate(sources[:8], start=1):
        meta = parse_frontmatter(path)
        lines.append(f'    R{index}["raw: {mermaid_label(title_for(path, meta))}"] --> D')
    for index, path in enumerate(pages[:12], start=1):
        meta = parse_frontmatter(path)
        page_type = meta.get("type") or "page"
        lines.append(f'    D --> W{index}["{page_type}: {mermaid_label(title_for(path, meta))}"]')
    if not sources and not pages:
        lines.append('    D --> Seed["等待首批资料"]')
    lines.append("```")
    return lines


def existing_created(target: Path) -> str:
    if not target.exists():
        return dt.date.today().isoformat()
    return parse_frontmatter(target).get("created") or dt.date.today().isoformat()


def render_domain(domain_slug: str) -> str:
    target = DOMAINS / f"{domain_slug}.md"
    created = existing_created(target)
    today = dt.date.today().isoformat()
    sources = raw_source_files(domain_slug)
    domain_label = domain_label_for(domain_slug, sources)
    pages = [
        path
        for path in wiki_files()
        if page_matches_domain(path, parse_frontmatter(path), domain_slug)
    ]
    relations = concept_relation_rows(pages)

    inbox_count = sum(1 for path in sources if parse_frontmatter(path).get("status") == "inbox")
    page_count = len(pages)

    lines = [
        "---",
        f"title: {domain_label} Knowledge Network",
        "type: domain",
        "status: active",
        f"created: {created}",
        f"updated: {today}",
        f"summary: {domain_label} 单学科知识网络入口，串联网页文章、本地资料、source summary、concept、analysis 与待办问题。",
        f"tags: [{domain_slug}, domain-network]",
        "sources: []",
        "---",
        "",
        f"# {domain_label} Knowledge Network",
        "",
        "这页是单学科知识网络的入口。它把原始资料、网页链接、本地资料位置、已沉淀的 wiki 页面和下一步待处理动作放在同一张可维护地图里。",
        "",
        "## Current Shape",
        "",
        f"- Registered raw sources: {len(sources)}",
        f"- Connected wiki pages: {page_count}",
        f"- Inbox sources waiting for ingest: {inbox_count}",
        f"- Generated on: {today}",
        "",
        "## How To Add Knowledge",
        "",
        f"- Web article: `python3 scripts/new_source.py --domain {domain_slug} --kind article --title \"标题\" --url \"https://...\"`",
        f"- Local file: `python3 scripts/new_source.py --domain {domain_slug} --kind paper --title \"标题\" --local-path \"/absolute/path/to/file.pdf\"`",
        "- After adding sources, run `python3 scripts/rebuild_domain_network.py` and then `python3 scripts/rebuild_index.py`.",
        "- When a source is important, create or update a `wiki/sources/...` source summary and connect it to concept/entity/analysis pages.",
        "",
        "## Knowledge Map",
        "",
        *render_mermaid(domain_label, sources, pages),
        "",
        "## Concept Graph",
        "",
        *render_concept_mermaid(relations),
        "",
        "## Concept Relations",
        "",
        *relation_table(relations),
        "",
        "## Source Intake",
        "",
        *source_rows(target, sources),
        "",
        "## Wiki Knowledge Layer",
        "",
        *wiki_rows(target, pages),
        "",
        "## Next Network Actions",
        "",
        "- Turn high-value `inbox` sources into source summaries.",
        "- Promote recurring terms, methods, people, texts, tools, or datasets into concept/entity pages.",
        "- Add explicit `Related` links between source summaries and concept pages, then rerun lint.",
        "- Mark cross-disciplinary bridge candidates in the related pages instead of duplicating content across domains.",
        "",
        "## Cross-Disciplinary Bridge Candidates",
        "",
        "- 待补：这个学科中哪些概念需要连接到其他学科？",
        "- 待补：哪些资料适合成为下一阶段跨学科 LLM Wiki 的桥接页面？",
    ]

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild generated domain knowledge network pages.")
    parser.add_argument("--domain", help="Only rebuild one domain slug.")
    args = parser.parse_args()

    DOMAINS.mkdir(parents=True, exist_ok=True)
    domains = [args.domain] if args.domain else discovered_domains()
    written: list[Path] = []
    for domain_slug in domains:
        target = DOMAINS / f"{domain_slug}.md"
        target.write_text(render_domain(domain_slug), encoding="utf-8")
        written.append(target)

    for path in written:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
