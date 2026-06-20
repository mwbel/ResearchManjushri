#!/usr/bin/env python3

from __future__ import annotations

import re
from collections import Counter
from typing import Any


WECHAT_BLOCK_MARKERS = (
    "环境异常",
    "请完成验证",
    "微信公众平台",
    "当前环境存在异常",
    "请在微信客户端打开",
    "访问频率过高",
    "完成验证后即可继续访问",
    "去验证",
)

STOPWORDS = {
    "source",
    "source type",
    "local path",
    "url",
    "http",
    "https",
    "www",
    "article",
    "paper",
    "note",
    "the",
    "and",
    "for",
    "on",
    "with",
    "that",
    "this",
    "from",
    "into",
    "about",
    "we",
    "our",
    "they",
    "their",
    "experiments",
    "experiment",
    "sciverse",
    "我们",
    "这个",
    "这种",
    "一个",
    "以及",
    "可以",
    "需要",
    "资料",
    "文章",
    "摘要",
    "当前知识网络",
    "用于补强当前知识网络",
}

KNOWN_TYPES = {
    "Transformer": "method",
    "Attention": "method",
    "attention mechanism": "method",
    "attention mechanisms": "method",
    "LLM": "concept",
    "AI": "concept",
    "Agent": "concept",
    "大语言模型": "concept",
    "语言模型": "concept",
    "注意力机制": "method",
    "人工智能": "concept",
    "世界模型": "concept",
}

CHINESE_TERM_PATTERN = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9+-]{2,24}"
    r"(?:机制|模型|算法|方法|理论|主义|问题|知识|智能|系统|网络|框架|概念)"
)
ENGLISH_TERM_PATTERN = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9+-]{1,}|[A-Z]{2,})(?:[- ][A-Z][A-Za-z0-9+-]{1,}){0,3}\b"
)


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_markdown(value: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", value)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    return text


def split_sentences(text: str) -> list[str]:
    plain = compact_spaces(strip_markdown(text))
    chunks = re.split(r"(?<=[。！？.!?])\s+|[；;]\s*", plain)
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) >= 8]


def truncate(text: str, limit: int = 180) -> str:
    cleaned = compact_spaces(strip_markdown(text))
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def first_nonempty(*values: object) -> str:
    for value in values:
        cleaned = compact_spaces(value)
        if cleaned:
            return cleaned
    return ""


def contains_block_marker(text: str) -> bool:
    return any(marker in text for marker in WECHAT_BLOCK_MARKERS)


def key_sentences(text: str, limit: int = 5) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        cleaned = compact_spaces(strip_markdown(text))
        return [truncate(cleaned, 220)] if cleaned else []
    selected: list[str] = []
    for sentence in sentences:
        if contains_block_marker(sentence):
            continue
        if sentence not in selected:
            selected.append(truncate(sentence, 220))
        if len(selected) >= limit:
            break
    return selected


def generate_source_summary(clean_text: str, metadata: dict[str, Any]) -> dict[str, Any]:
    title = first_nonempty(metadata.get("title"), metadata.get("source_id"), "未命名资料")
    source_type = first_nonempty(metadata.get("source_type"), metadata.get("kind"), "source")
    points = key_sentences(clean_text, 5)
    lead = points[0] if points else f"《{title}》已进入资料库，但当前正文不足，需人工补充。"
    short_summary = " ".join(points[:3]) if points else lead
    quotes = [
        {"quote": item, "reason": "该摘录可支撑资料的主要观点或后续概念候选。"}
        for item in points[:3]
    ]
    context = first_nonempty(metadata.get("context"), metadata.get("notes"))

    return {
        "title": title,
        "source_type": source_type,
        "one_sentence_summary": lead,
        "short_summary": short_summary,
        "key_points": points[:5],
        "important_quotes": quotes,
        "why_saved": context or f"这篇资料可补强「{metadata.get('domain') or '当前'}」知识网络中的资料证据。",
        "next_actions": [
            "人工确认摘要是否覆盖原文主旨。",
            "从候选概念中挑选值得沉淀为正式概念页的条目。",
        ],
    }


def normalize_term(term: str) -> str:
    return compact_spaces(term).strip(" ：:，,。！？!?；;（）()「」『』[]【】“”\"'")


def is_noise_term(term: str) -> bool:
    normalized = normalize_term(term)
    lowered = normalized.lower()
    if not normalized or lowered in STOPWORDS:
        return True
    if len(normalized) < 2 or len(normalized) > 32:
        return True
    if normalized.startswith(("这个", "这种", "以及", "如果", "或者", "但是", "所以", "用于")):
        return True
    if "当前知识网络" in normalized or "Sciverse" in normalized:
        return True
    if "http" in lowered or lowered in {"source", "url"}:
        return True
    return False


def evidence_for_term(term: str, sentences: list[str]) -> str:
    for sentence in sentences:
        if term in sentence:
            return truncate(sentence, 220)
    return ""


def title_terms(title: str) -> list[str]:
    terms: list[str] = []
    for known in KNOWN_TYPES:
        if known in title and known not in terms:
            terms.append(known)
    for part in re.split(r"[\s,，:：/｜|《》【】()（）]+", title):
        cleaned = normalize_term(part)
        if cleaned in KNOWN_TYPES and cleaned not in terms:
            terms.append(cleaned)
    return terms


def candidate_terms(clean_text: str, metadata: dict[str, Any]) -> list[str]:
    title = str(metadata.get("title") or "")
    sentences = split_sentences(clean_text)
    terms: list[str] = []

    def add(term: str) -> None:
        cleaned = normalize_term(term)
        dedupe_key = cleaned.lower().rstrip("s")
        if not is_noise_term(cleaned) and not any(existing.lower().rstrip("s") == dedupe_key for existing in terms):
            terms.append(cleaned)

    for term in title_terms(title):
        add(term)
    for term in metadata.get("candidate_concepts") or []:
        add(str(term))
    for term in KNOWN_TYPES:
        if term in clean_text or term.lower() in clean_text.lower():
            add(term)
    for term in CHINESE_TERM_PATTERN.findall(clean_text):
        add(term)
    for term in ENGLISH_TERM_PATTERN.findall(f"{title} {clean_text}"):
        add(term)

    if len(terms) < 5:
        words = re.findall(r"[A-Za-z][A-Za-z0-9+-]{2,}|[\u4e00-\u9fff]{2,8}", clean_text)
        for word, _ in Counter(word for word in words if not is_noise_term(word)).most_common(20):
            add(word)
            if len(terms) >= 10:
                break

    return terms[:10]


def extract_concept_candidates(clean_text: str, metadata: dict[str, Any]) -> dict[str, Any]:
    sentences = split_sentences(clean_text)
    candidates: list[dict[str, Any]] = []
    for term in candidate_terms(clean_text, metadata):
        evidence = evidence_for_term(term, sentences)
        if not evidence:
            continue
        candidate_type = KNOWN_TYPES.get(term, "concept")
        candidates.append(
            {
                "name": term,
                "aliases": [],
                "type": candidate_type,
                "definition_draft": f"{term} 是从资料《{metadata.get('title') or '未命名资料'}》中抽取的候选概念，需要人工确认定义边界。",
                "evidence_quote": evidence,
                "confidence": 0.72 if term in KNOWN_TYPES else 0.6,
            }
        )
        if len(candidates) >= 10:
            break
    return {"concept_candidates": candidates}


def quality_check(
    clean_text: str,
    summary: dict[str, Any],
    concepts: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    issues: list[str] = []
    risk_level = "low"
    text = compact_spaces(clean_text)
    if not text:
        issues.append("正文为空。")
        risk_level = "high"
    elif len(text) < 80:
        issues.append("正文过短，摘要和候选概念可能不可靠。")
        risk_level = "medium"
    if contains_block_marker(text):
        issues.append("正文疑似微信风控页、验证页或环境异常页。")
        risk_level = "high"
    if not compact_spaces(summary.get("one_sentence_summary")):
        issues.append("一句话摘要为空。")
        risk_level = "high"
    for index, candidate in enumerate(concepts.get("concept_candidates") or [], start=1):
        if not compact_spaces(candidate.get("evidence_quote")):
            issues.append(f"第 {index} 个候选概念缺少 evidence_quote。")
            risk_level = "medium" if risk_level == "low" else risk_level

    needs_review = bool(issues)
    return {
        "pass": not needs_review,
        "risk_level": risk_level,
        "needs_human_review": needs_review,
        "issues": issues,
    }
