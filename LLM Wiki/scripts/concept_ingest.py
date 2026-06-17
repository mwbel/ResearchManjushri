#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path

from new_source import slugify


ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
WIKI_CONCEPTS = WIKI / "concepts"
WIKI_SOURCES = WIKI / "sources"

STOPWORDS = {
    "Source",
    "Profile",
    "Kind",
    "Domain",
    "Local",
    "Extracted",
    "Notes",
    "Main",
    "Takeaways",
    "Candidate",
    "Concepts",
    "Links",
    "Sources",
    "URL",
    "HTML",
    "Extraction",
    "Ingest",
    "Raw",
    "file",
    "local",
    "paper",
    "article",
}

BAD_TERM_MARKERS = (
    "我们",
    "文章",
    "然后",
    "首先",
    "其次",
    "最终",
    "作为",
    "这种",
    "它",
    "而非",
    "当前",
    "需要",
)

KNOWN_TERMS = [
    "Transformer",
    "LLM",
    "AI",
    "BP",
    "泛BP",
    "注意力机制",
    "知识论",
    "归纳法",
    "不完全的归纳法",
    "大语言模型",
    "语言模型",
    "真信念且证成",
    "结构化的噪声引入",
    "Noise Leading In",
    "NLI",
    "休谟",
    "波普尔",
    "图灵",
    "知识",
    "智能",
]

CHINESE_TERM_PATTERN = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9+-]{2,24}"
    r"(?:机制|模型|算法|方法|理论|主义|问题|知识|智能|信念|证成|归纳法|知识论|语言模型)"
)

ENGLISH_TERM_PATTERN = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9+-]{1,}|[A-Z]{2,})(?:[- ][A-Z][A-Za-z0-9+-]{1,}){0,4}\b"
)

RELATION_HINTS = [
    ("缺乏", "缺乏"),
    ("不是", "不是"),
    ("依赖", "依赖"),
    ("属于", "属于"),
    ("构成", "构成"),
    ("产生", "产生"),
    ("导致", "导致"),
    ("揭示", "揭示"),
    ("指出", "指出"),
    ("建立在", "建立在"),
    ("承担", "承担"),
    ("视为", "被视为"),
    ("是", "是"),
]


def parse_frontmatter_and_body(path: Path) -> tuple[dict[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "\n".join(lines)

    data: dict[str, str] = {}
    end_index = 0
    for index, line in enumerate(lines[1:], start=1):
        stripped = line.strip()
        if stripped == "---":
            end_index = index
            break
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip()
    return data, "\n".join(lines[end_index + 1 :])


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


def extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "_intro"
    sections[current] = []
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def plain_text(markdown: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", markdown)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[。！？.!?])\s*|[；;]\s*", plain_text(text))
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) >= 6]


def title_without_prefix(title: str) -> str:
    return re.sub(r"^Source\s*-\s*", "", title).strip()


def candidate_terms(title: str, evidence: str, tags: list[str], domain_slug: str, domain_label: str) -> list[str]:
    terms: list[str] = []

    def add(term: str) -> None:
        cleaned = term.strip(" ：:，,。！？!?；;（）()「」『』[]【】“”\"'")
        if not cleaned or cleaned in STOPWORDS:
            return
        if cleaned not in KNOWN_TERMS and any(marker in cleaned for marker in BAD_TERM_MARKERS):
            return
        if cleaned not in KNOWN_TERMS and "的" in cleaned and len(cleaned) > 8:
            return
        if cleaned == domain_slug or cleaned == "source":
            return
        if len(cleaned) < 2:
            return
        if cleaned not in terms:
            terms.append(cleaned)

    for term in KNOWN_TERMS:
        if term in title or term in evidence:
            add(term)

    for term in CHINESE_TERM_PATTERN.findall(evidence):
        add(term)
    for term in ENGLISH_TERM_PATTERN.findall(f"{title} {evidence}"):
        add(term)

    for raw_part in re.split(r"[：:，,、/ -]+", title_without_prefix(title)):
        if "Transformer" in raw_part:
            add("Transformer")
        elif raw_part in KNOWN_TERMS:
            add(raw_part)

    for tag in tags:
        if tag not in {"source", domain_slug}:
            add(tag)
    add(domain_label)

    return terms[:24]


def relation_label(sentence: str) -> str:
    for hint, label in RELATION_HINTS:
        if hint in sentence:
            return label
    return "相关"


def extract_relations(terms: list[str], evidence: str) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    seen = set()
    for sentence in split_sentences(evidence):
        if "吗" in sentence or "？" in sentence or "?" in sentence:
            continue
        present = [term for term in terms if term in sentence]
        if len(present) < 2:
            continue
        source = present[0]
        label = relation_label(sentence)
        for target in present[1:4]:
            if source == target:
                continue
            key = (source, label, target)
            if key in seen:
                continue
            seen.add(key)
            relations.append(
                {
                    "source": source,
                    "relation": label,
                    "target": target,
                    "evidence": sentence[:180].rstrip(),
                }
            )
            if len(relations) >= 18:
                return relations
    return relations


def concept_sentences(term: str, evidence: str, limit: int = 3) -> list[str]:
    sentences: list[str] = []
    for sentence in split_sentences(evidence):
        if term not in sentence:
            continue
        if "吗" in sentence or "？" in sentence or "?" in sentence:
            continue
        cleaned = sentence.strip()
        if cleaned and cleaned not in sentences:
            sentences.append(cleaned)
        if len(sentences) >= limit:
            break
    return sentences


def concept_definition_lines(term: str, source_title: str, sentences: list[str], source_rel: str) -> list[str]:
    if not sentences:
        return [f"- `{term}` 是从资料《{source_title}》中抽取出的候选概念；当前缺少可直接支撑定义的摘录，需要人工补充。"]
    first = sentences[0]
    return [
        f"- 在资料《{source_title}》中，`{term}` 的当前工作性理解来自这条摘录：{first}",
        f"- 这个定义仍是 source-derived 草稿，需要回到 `{source_rel}` 与原文继续校正。",
    ]


def concept_evidence_lines(source_summary: Path, source_title: str, sentences: list[str]) -> list[str]:
    if not sentences:
        return [source_evidence_line(source_summary, source_title, "暂无与该概念直接匹配的摘录。")]
    return [source_evidence_line(source_summary, source_title, sentence) for sentence in sentences]


def rel_link(from_dir: Path, target: Path) -> str:
    return Path(os.path.relpath(target, from_dir)).as_posix()


def frontmatter_bounds(lines: list[str]) -> tuple[int, int] | None:
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return 0, index
    return None


def update_frontmatter_list(
    meta: dict[str, str],
    key: str,
    additions: list[str],
    removals: list[str] | None = None,
) -> str:
    values = parse_list(meta.get(key))
    for item in removals or []:
        values = [value for value in values if value != item]
    for item in additions:
        if item and item not in values:
            values.append(item)
    return f"[{', '.join(values)}]"


def update_existing_concept(
    path: Path,
    domain_slug: str,
    source_rel: str,
    definition_lines: list[str],
    evidence_lines: list[str],
    relation_lines: list[str],
    old_domain: str | None = None,
) -> None:
    meta, _ = parse_frontmatter_and_body(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() != "---":
        try:
            first_frontmatter = next(index for index, line in enumerate(lines) if line.strip() == "---")
            lines = lines[first_frontmatter:]
        except StopIteration:
            pass
    bounds = frontmatter_bounds(lines)
    today = dt.date.today().isoformat()

    if bounds:
        _, end = bounds
        updated_frontmatter = []
        saw_updated = False
        saw_tags = False
        saw_sources = False
        for index, line in enumerate(lines[: end + 1]):
            if line.startswith("updated:"):
                updated_frontmatter.append(f"updated: {today}")
                saw_updated = True
            elif line.startswith("tags:"):
                removals = [old_domain] if old_domain and old_domain != domain_slug else []
                updated_frontmatter.append(
                    f"tags: {update_frontmatter_list(meta, 'tags', [domain_slug, 'auto-concept'], removals)}"
                )
                saw_tags = True
            elif line.startswith("sources:"):
                updated_frontmatter.append(f"sources: {update_frontmatter_list(meta, 'sources', [source_rel])}")
                saw_sources = True
            elif line.strip() == "---":
                if index == end:
                    if not saw_updated:
                        updated_frontmatter.append(f"updated: {today}")
                    if not saw_tags:
                        updated_frontmatter.append(f"tags: [{domain_slug}, auto-concept]")
                    if not saw_sources:
                        updated_frontmatter.append(f"sources: [{source_rel}]")
                updated_frontmatter.append(line)
            else:
                updated_frontmatter.append(line)
        lines = [*updated_frontmatter, *lines[end + 1 :]]

    rejected_terms = [*BAD_TERM_MARKERS, "Transformer的输出是知识", "它缺乏知识", "而非知识"]
    existing_relation_lines: list[str] = []
    cleaned_lines: list[str] = []
    for line in lines:
        is_relation = line.startswith("- `") and "--" in line and "-->" in line
        is_rejected = is_relation and any(term in line for term in rejected_terms)
        is_weak_question_relation = is_relation and ("输出是知识吗" in line or "是知识吗" in line)
        if is_rejected or is_weak_question_relation:
            continue
        if is_relation:
            if line not in existing_relation_lines:
                existing_relation_lines.append(line)
            continue
        cleaned_lines.append(line)
    lines = cleaned_lines
    relation_lines = [*existing_relation_lines, *[line for line in relation_lines if line not in existing_relation_lines]]

    def replace_section(heading: str, section_lines: list[str], fallback_before: str | None = None) -> None:
        nonlocal lines
        section = [heading, "", *section_lines, ""]
        try:
            start = next(index for index, line in enumerate(lines) if line.strip() == heading)
            end = len(lines)
            for index in range(start + 1, len(lines)):
                if lines[index].startswith("## "):
                    end = index
                    break
            lines = [*lines[:start], *section, *lines[end:]]
        except StopIteration:
            if fallback_before:
                try:
                    insert_at = next(index for index, line in enumerate(lines) if line.strip() == fallback_before)
                except StopIteration:
                    insert_at = len(lines)
            else:
                insert_at = len(lines)
            lines = [*lines[:insert_at], *section, *lines[insert_at:]]

    replace_section("## Working Definition", definition_lines, "## Source-Derived Evidence")
    replace_section("## Source-Derived Evidence", evidence_lines, "## Source-Derived Relations")

    if relation_lines:
        unique_relations: list[str] = []
        for line in relation_lines:
            if line not in unique_relations:
                unique_relations.append(line)
        replace_section("## Source-Derived Relations", unique_relations, "## Open Questions")

    if old_domain and old_domain != domain_slug:
        old_domain_link = f"../domains/{old_domain}.md"
        lines = [line for line in lines if old_domain_link not in line]
    domain_link = f"- [{domain_slug} Knowledge Network](../domains/{domain_slug}.md)"
    if domain_link not in lines:
        try:
            related_index = next(index for index, line in enumerate(lines) if line.strip() == "## Related")
            insert_at = related_index + 1
            while insert_at < len(lines) and not lines[insert_at].strip():
                insert_at += 1
            lines.insert(insert_at, domain_link)
        except StopIteration:
            lines.extend(["", "## Related", "", domain_link])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def create_concept_page(
    path: Path,
    label: str,
    domain_slug: str,
    domain_label: str,
    source_rel: str,
    source_title: str,
    definition_lines: list[str],
    evidence_lines: list[str],
    relation_lines: list[str],
) -> None:
    today = dt.date.today().isoformat()
    content = [
        "---",
        f"title: {label}",
        "type: concept",
        "status: active",
        f"created: {today}",
        f"updated: {today}",
        f"summary: 从资料《{source_title}》自动提取的候选概念，等待人工整理定义、边界和跨学科连接。",
        f"tags: [{domain_slug}, auto-concept]",
        f"sources: [{source_rel}]",
        "---",
        "",
        f"# {label}",
        "",
        "## Working Definition",
        "",
        *definition_lines,
        "",
        "## Source-Derived Evidence",
        "",
        *evidence_lines,
        "",
        "## Source-Derived Relations",
        "",
        *(relation_lines or ["- 待补：尚未抽取到稳定概念关系。"]),
        "",
        "## Open Questions",
        "",
        "- 这个概念是否应该保留为独立页面，还是并入更大的主题页？",
        "- 它和同学科其他概念的层级关系是什么？",
        "- 是否存在跨学科桥接价值？",
        "",
        "## Related",
        "",
        f"- [{domain_label} Knowledge Network](../domains/{domain_slug}.md)",
        "",
        "## Sources",
        "",
        f"- `{source_rel}`",
    ]
    path.write_text("\n".join(content).rstrip() + "\n", encoding="utf-8")


def source_evidence_line(source_summary: Path, source_title: str, excerpt: str) -> str:
    link = rel_link(WIKI_CONCEPTS, source_summary)
    cleaned = excerpt.strip()
    if len(cleaned) > 220:
        cleaned = cleaned[:219].rstrip() + "…"
    return f"- [{source_title}]({link}): {cleaned}"


def relation_line(relation: dict[str, str], source_summary: Path) -> str:
    link = rel_link(WIKI_CONCEPTS, source_summary)
    evidence = relation["evidence"]
    if len(evidence) > 120:
        evidence = evidence[:119].rstrip() + "…"
    return (
        f"- `{relation['source']}` --{relation['relation']}--> `{relation['target']}` "
        f"([source]({link}); evidence: {evidence})"
    )


def concept_path(label: str) -> Path:
    return WIKI_CONCEPTS / f"{slugify(label)}.md"


def ingest_concepts(
    source_summary: Path,
    domain_override: str | None = None,
    old_domain: str | None = None,
) -> dict[str, object]:
    summary_path = source_summary if source_summary.is_absolute() else ROOT / source_summary
    summary_path = summary_path.resolve()
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)
    if WIKI_SOURCES.resolve() not in summary_path.parents:
        raise ValueError(f"Source summary must be under {WIKI_SOURCES.relative_to(ROOT)}")

    meta, body = parse_frontmatter_and_body(summary_path)
    title = title_without_prefix(meta.get("title") or summary_path.stem)
    tags = parse_list(meta.get("tags"))
    domain_slug = domain_override or next((tag for tag in tags if tag != "source"), "general")
    domain_label = domain_slug
    sections = extract_sections(body)
    evidence = "\n\n".join(
        part
        for part in [
            meta.get("summary", ""),
            sections.get("Main Takeaways", ""),
            sections.get("Extracted Notes", ""),
            sections.get("Why This Source Was Added", ""),
        ]
        if part.strip()
    )
    if not evidence.strip():
        return {"source": str(summary_path.relative_to(ROOT)), "concepts": [], "relations": []}

    terms = candidate_terms(title, evidence, tags, domain_slug, domain_label)
    relations = extract_relations(terms, evidence)
    WIKI_CONCEPTS.mkdir(parents=True, exist_ok=True)

    source_rel = summary_path.relative_to(ROOT).as_posix()

    written: list[str] = []
    for term in terms:
        path = concept_path(term)
        sentences = concept_sentences(term, evidence)
        definition_lines = concept_definition_lines(term, title, sentences, source_rel)
        evidence_lines = concept_evidence_lines(summary_path, title, sentences)
        term_relations = [
            relation_line(relation, summary_path)
            for relation in relations
            if relation["source"] == term or relation["target"] == term
        ]
        if path.exists():
            update_existing_concept(path, domain_slug, source_rel, definition_lines, evidence_lines, term_relations, old_domain)
        else:
            create_concept_page(
                path,
                term,
                domain_slug,
                domain_label,
                source_rel,
                title,
                definition_lines,
                evidence_lines,
                term_relations,
            )
        written.append(str(path.relative_to(ROOT)))

    return {
        "source": str(summary_path.relative_to(ROOT)),
        "concepts": written,
        "relations": relations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract candidate concepts and relations from a source summary.")
    parser.add_argument("source_summary", help="wiki/sources/... source summary path.")
    parser.add_argument("--domain", help="Override domain slug.")
    parser.add_argument("--replace-domain", help="Remove this old domain tag from updated auto concept pages.")
    args = parser.parse_args()

    result = ingest_concepts(Path(args.source_summary), args.domain, args.replace_domain)
    for path in result["concepts"]:
        print(path)
    print(f"relations: {len(result['relations'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        raise SystemExit(1)
