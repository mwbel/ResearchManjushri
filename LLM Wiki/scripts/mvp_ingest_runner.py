#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any

import auto_ingest as auto_ingest_lib
from mvp_ingest_artifacts import (
    ROOT,
    artifact_dir,
    root_relative,
    source_id_for_path,
    write_json_artifact,
    write_status,
    write_text_artifact,
)
from mvp_subagents import extract_concept_candidates, generate_source_summary, quality_check


RAW_SOURCES = ROOT / "raw" / "sources"
WIKI_SOURCES = ROOT / "wiki" / "sources"
PLACEHOLDER_MARKERS = (
    "为什么要收录这份资料？它与当前 wiki 的哪条主线相关？",
    "把原文、摘录、转写或清洗后的正文放在这里。",
    "可补充少量人工备注，但尽量不要破坏原始内容。",
    "可补充少量人工备注，但尽量不要破坏原始内容的可追溯性。",
)


def resolve_raw_source(source_path: str | Path) -> Path:
    path = Path(source_path).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if RAW_SOURCES.resolve() not in path.parents:
        raise ValueError(f"source_path must be under {RAW_SOURCES.relative_to(ROOT)}")
    return path


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    cleaned = value.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    items: list[str] = []
    for item in cleaned.split(","):
        normalized = item.strip().strip("\"'")
        if normalized and normalized not in items:
            items.append(normalized)
    return items


def domain_from_source(path: Path, meta: dict[str, str]) -> str:
    if meta.get("domain"):
        return meta["domain"]
    try:
        return path.relative_to(RAW_SOURCES).parts[0]
    except Exception:
        return "uncategorized"


def clean_fragment(text: str) -> str:
    cleaned = auto_ingest_lib.remove_placeholders(text or "")
    for marker in PLACEHOLDER_MARKERS:
        cleaned = cleaned.replace(marker, "")
    return cleaned.strip()


def clean_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?m)^---\s*$.*?^---\s*$", "", text, count=1, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return clean_fragment(text)


def metadata_from_source(path: Path, meta: dict[str, str], body: str, source_id: str) -> dict[str, Any]:
    sections = auto_ingest_lib.extract_sections(body)
    domain = domain_from_source(path, meta)
    candidate_concepts = [
        tag
        for tag in parse_list(meta.get("tags"))
        if tag and tag not in {"source", "web", "local", "paper", "article", "note", domain}
    ]
    return {
        "source_id": source_id,
        "source_path": path.relative_to(ROOT).as_posix(),
        "title": meta.get("title") or path.stem,
        "kind": meta.get("kind") or "source",
        "source_type": meta.get("source_type") or meta.get("kind") or "source",
        "domain": domain,
        "domain_label": meta.get("domain_label") or domain,
        "source_url": meta.get("source_url") or "",
        "local_path": meta.get("local_path") or "",
        "author": meta.get("author") or "",
        "published": meta.get("published") or "",
        "created": meta.get("created") or dt.date.today().isoformat(),
        "context": clean_fragment(sections.get("Context", "")),
        "original_content": clean_fragment(sections.get("Original Content Or Extract", "")),
        "notes": clean_fragment(sections.get("Notes", "")),
        "candidate_concepts": candidate_concepts,
    }


def extract_text(metadata: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    source_type = str(metadata.get("source_type") or "")
    original = str(metadata.get("original_content") or "")
    if source_type == "sciverse":
        original = auto_ingest_lib.clean_sciverse_original(original)

    parts = [
        str(metadata.get("context") or ""),
        original,
        str(metadata.get("notes") or ""),
    ]
    extraction = {"status": "skipped", "source": "raw_source", "info": {}}
    external_text = ""

    local_path = str(metadata.get("local_path") or "").strip()
    source_url = str(metadata.get("source_url") or "").strip()
    if local_path:
        external_text, status = auto_ingest_lib.read_local_text(local_path)
        extraction = {"status": status, "source": "local_path", "info": {"local_path": local_path}}
    elif source_url:
        if "mp.weixin.qq.com" in source_url:
            external_text, status, info = auto_ingest_lib.fetch_wechat_with_crawler(source_url)
            extraction = {"status": status, "source": "wechat_crawler", "info": info}
        if not external_text:
            external_text, status = auto_ingest_lib.fetch_web_text(source_url)
            extraction = {"status": status, "source": "web_fetch", "info": {"source_url": source_url}}

    if external_text:
        parts.append(external_text)

    raw_text = "\n\n".join(clean_fragment(part) for part in parts if clean_fragment(part))
    return raw_text, extraction


def quote_block(value: str) -> list[str]:
    return [f"> {line}" for line in value.splitlines() if line.strip()]


def render_wiki_source(
    metadata: dict[str, Any],
    source_id: str,
    summary: dict[str, Any],
    concepts: dict[str, Any],
) -> str:
    today = dt.date.today().isoformat()
    source_path = str(metadata.get("source_path") or "")
    title = str(summary.get("title") or metadata.get("title") or source_id)
    tags = ["source", str(metadata.get("domain") or "uncategorized"), "mvp-ingest"]
    summary_text = str(summary.get("one_sentence_summary") or "")

    lines = [
        "---",
        f"title: Source - {title}",
        "type: source",
        "status: active",
        f"created: {today}",
        f"updated: {today}",
        f"summary: {summary_text}",
        f"tags: [{', '.join(tag for tag in tags if tag)}]",
        f"sources: [{source_path}]",
        "---",
        "",
        f"# {title}",
        "",
        "## 来源信息",
        "",
        f"- Source ID: `{source_id}`",
        f"- Source Type: `{metadata.get('source_type') or ''}`",
        f"- Original Path: `{source_path}`",
        f"- URL: {metadata.get('source_url') or '无'}",
        f"- Created At: {metadata.get('created') or today}",
        "",
        "## 一句话摘要",
        "",
        summary_text or "待补：摘要为空。",
        "",
        "## 摘要",
        "",
        str(summary.get("short_summary") or summary_text or "待补：摘要为空。"),
        "",
        "## 核心要点",
        "",
    ]

    key_points = summary.get("key_points") or []
    if key_points:
        lines.extend(f"{index}. {item}" for index, item in enumerate(key_points, start=1))
    else:
        lines.append("1. 待补：未抽取到稳定要点。")

    lines.extend(["", "## 重要摘录", ""])
    quotes = summary.get("important_quotes") or []
    if quotes:
        for item in quotes:
            lines.extend(quote_block(str(item.get("quote") or "")))
            if item.get("reason"):
                lines.append(f"> 原因：{item['reason']}")
            lines.append("")
    else:
        lines.append("> 暂无可展示摘录。")

    lines.extend(["## 候选概念", ""])
    candidates = concepts.get("concept_candidates") or []
    if candidates:
        for candidate in candidates:
            lines.append(f"- {candidate.get('name')}: {candidate.get('definition_draft')}")
            lines.append(f"  - 证据：{candidate.get('evidence_quote')}")
    else:
        lines.append("- 暂无候选概念。")

    lines.extend(["", "## 下一步整理建议", ""])
    for action in summary.get("next_actions") or []:
        lines.append(f"- {action}")
    if not summary.get("next_actions"):
        lines.append("- 人工确认这份资料是否值得继续沉淀为概念页。")
    lines.extend(["", "## Sources", "", f"- `{source_path}`"])
    return "\n".join(lines).rstrip() + "\n"


def wiki_source_path(metadata: dict[str, Any], source_id: str) -> Path:
    domain = str(metadata.get("domain") or "uncategorized").strip() or "uncategorized"
    return WIKI_SOURCES / domain / f"{source_id}.md"


def write_wiki_source(
    metadata: dict[str, Any],
    source_id: str,
    summary: dict[str, Any],
    concepts: dict[str, Any],
    overwrite: bool,
) -> tuple[Path, bool]:
    target = wiki_source_path(metadata, source_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return target, False
    target.write_text(render_wiki_source(metadata, source_id, summary, concepts), encoding="utf-8")
    return target, True


def write_error(source_id: str, source_path: str, message: str, exc: BaseException | None = None) -> None:
    payload: dict[str, Any] = {
        "source_id": source_id,
        "source_path": source_path,
        "error": message,
        "created_at": dt.datetime.now().replace(microsecond=0).isoformat(),
    }
    if exc is not None:
        payload["exception_type"] = type(exc).__name__
        payload["traceback"] = traceback.format_exc()
    write_json_artifact(source_id, "error", payload)


def run_mvp_ingest(source_path: str, overwrite: bool = False) -> dict[str, Any]:
    raw_path = resolve_raw_source(source_path)
    source_rel = raw_path.relative_to(ROOT).as_posix()
    source_id = source_id_for_path(raw_path)
    artifact_rel = artifact_dir(source_id).relative_to(ROOT).as_posix()

    try:
        write_status(source_id, source_rel, "running", "READ_SOURCE")
        meta, body = auto_ingest_lib.parse_frontmatter_and_body(raw_path)
        metadata = metadata_from_source(raw_path, meta, body, source_id)

        write_status(source_id, source_rel, "running", "EXTRACT_TEXT")
        raw_text, extraction = extract_text(metadata)
        metadata["extraction"] = extraction
        write_text_artifact(source_id, "raw_text", raw_text)

        write_status(source_id, source_rel, "running", "CLEAN_TEXT")
        cleaned = clean_text(raw_text)
        write_text_artifact(source_id, "clean_text", cleaned)

        write_status(source_id, source_rel, "running", "SUMMARIZE")
        summary = generate_source_summary(cleaned, metadata)
        write_json_artifact(source_id, "source_summary", summary)

        write_status(source_id, source_rel, "running", "EXTRACT_CONCEPTS")
        concepts = extract_concept_candidates(cleaned, metadata)
        write_json_artifact(source_id, "concept_candidates", concepts)

        quality = quality_check(cleaned, summary, concepts, metadata)
        if quality.get("needs_human_review"):
            message = "; ".join(quality.get("issues") or ["需要人工审核"])
            write_error(source_id, source_rel, message)
            write_status(
                source_id,
                source_rel,
                "review_required",
                "REVIEW_REQUIRED",
                message,
                {"quality": quality, "wiki_source_path": ""},
            )
            return {
                "ok": False,
                "source_id": source_id,
                "status": "review_required",
                "current_step": "REVIEW_REQUIRED",
                "artifact_dir": artifact_rel,
                "error": message,
                "quality": quality,
            }

        write_status(source_id, source_rel, "running", "WRITE_WIKI_SOURCE")
        target, wrote_wiki = write_wiki_source(metadata, source_id, summary, concepts, overwrite)
        try:
            auto_ingest_lib.update_source_status(raw_path, "active")
        except Exception:
            pass
        result = {
            "ok": True,
            "source_id": source_id,
            "status": "completed",
            "current_step": "COMPLETED",
            "artifact_dir": artifact_rel,
            "wiki_source_path": target.relative_to(ROOT).as_posix(),
            "wrote_wiki_source": wrote_wiki,
        }
        write_status(
            source_id,
            source_rel,
            "completed",
            "COMPLETED",
            None,
            {"wiki_source_path": result["wiki_source_path"], "quality": quality},
        )
        return result
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        write_error(source_id, source_rel, message, exc)
        write_status(source_id, source_rel, "failed", "FAILED", message)
        return {
            "ok": False,
            "source_id": source_id,
            "status": "failed",
            "current_step": "FAILED",
            "artifact_dir": artifact_rel,
            "error": message,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the file-based MVP ingest pipeline for one raw source.")
    parser.add_argument("source_path", help="raw/sources/... source markdown path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MVP wiki source page")
    args = parser.parse_args()
    result = run_mvp_ingest(args.source_path, overwrite=args.overwrite)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
