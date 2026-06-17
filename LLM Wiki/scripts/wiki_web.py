#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import re
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "scripts"
WEBUI = ROOT / "webui"
RAW_SOURCES = ROOT / "raw" / "sources"
RAW_UPLOADS = ROOT / "raw" / "assets" / "uploads"
WIKI = ROOT / "wiki"
DOMAIN_PAGES = WIKI / "domains"
WIKI_CONCEPTS = WIKI / "concepts"
MAX_UPLOAD_BYTES = 120 * 1024 * 1024

sys.path.insert(0, str(SCRIPT_DIR))
from new_source import build_content, infer_source_type, parse_extra_tags, resolve_domain, slugify  # noqa: E402


MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


DOMAIN_OPTIONS = [
    ("general", "通用"),
    ("llm-wiki", "LLM Wiki"),
    ("math", "数学"),
    ("physics", "物理"),
    ("tibetan-astronomy-calendar", "西藏天文历算"),
    ("modern-astronomy", "现代天文学"),
]


def read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def write_json(handler: BaseHTTPRequestHandler, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


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


def split_frontmatter(path: Path) -> tuple[list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return [], lines

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[: index + 1], lines[index + 1 :]
    return [], lines


def parse_frontmatter_and_body(path: Path) -> tuple[dict[str, str], str]:
    frontmatter, body = split_frontmatter(path)
    if not frontmatter:
        return {}, "\n".join(body)

    data: dict[str, str] = {}
    for line in frontmatter[1:-1]:
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip()
    return data, "\n".join(body).strip()


def parse_inline_list(value: str | None) -> list[str]:
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


def write_frontmatter(path: Path, updates: dict[str, str]) -> None:
    frontmatter, body = split_frontmatter(path)
    if not frontmatter:
        raise ValueError("raw source 缺少 frontmatter")

    seen = set()
    updated = [frontmatter[0]]
    for line in frontmatter[1:]:
        if line.strip() == "---":
            for key, value in updates.items():
                if key not in seen:
                    updated.append(f"{key}: {value}")
            updated.append(line)
            break
        if ":" not in line:
            updated.append(line)
            continue
        key = line.split(":", 1)[0].strip()
        if key in updates:
            updated.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            updated.append(line)

    path.write_text("\n".join([*updated, *body]).rstrip() + "\n", encoding="utf-8")


def raw_source_files(domain_slug: str | None = None) -> list[Path]:
    root = RAW_SOURCES / domain_slug if domain_slug else RAW_SOURCES
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.name.lower() != "readme.md" and not path.name.startswith(".")
    )


def wiki_pages_for_domain(domain_slug: str) -> int:
    target = DOMAIN_PAGES / f"{domain_slug}.md"
    if not target.exists():
        return 0
    content = target.read_text(encoding="utf-8")
    return max(0, content.count("| `wiki/"))


def shell_run(args: list[str]) -> dict:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": " ".join(args),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "ok": completed.returncode == 0,
    }


def raw_path_from_relative(source_path: str) -> Path:
    path = (ROOT / source_path).resolve()
    if not path.exists():
        raise FileNotFoundError(source_path)
    if RAW_SOURCES.resolve() not in path.parents:
        raise ValueError("只能 ingest raw/sources/ 下的资料")
    return path


def raw_source_domain(path: Path) -> str:
    meta = parse_frontmatter(path)
    if meta.get("domain"):
        return meta["domain"]
    try:
        return path.relative_to(RAW_SOURCES).parts[0]
    except ValueError:
        return "general"


def run_ingest_pipeline(source_path: str, payload: dict) -> tuple[list[dict], str]:
    raw_path = raw_path_from_relative(source_path)
    domain_slug = raw_source_domain(raw_path)
    actions: list[dict] = []

    rebuild_domain = bool(payload.get("rebuild_domain", True))
    rebuild_index = bool(payload.get("rebuild_index", True))
    run_lint = bool(payload.get("run_lint", False))
    overwrite = bool(payload.get("overwrite_ingest", False))
    concept_network = bool(payload.get("concept_network", True))

    # Pre-create a domain page so auto_ingest can link to it for custom disciplines.
    if rebuild_domain and not (DOMAIN_PAGES / f"{domain_slug}.md").exists():
        actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))

    ingest_args = ["python3", "scripts/auto_ingest.py", str(raw_path.relative_to(ROOT))]
    if overwrite:
        ingest_args.append("--overwrite")
    actions.append(shell_run(ingest_args))

    summary_path = ""
    if actions[-1]["ok"]:
        summary_path = actions[-1]["stdout"].splitlines()[-1] if actions[-1]["stdout"] else ""

    if concept_network and summary_path:
        concept_args = ["python3", "scripts/concept_ingest.py", summary_path, "--domain", domain_slug]
        old_domain_for_concepts = clean_text(payload.get("old_domain_for_concepts"))
        if old_domain_for_concepts and old_domain_for_concepts != domain_slug:
            concept_args.extend(["--replace-domain", old_domain_for_concepts])
        actions.append(shell_run(concept_args))

    if rebuild_domain:
        actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))
    if rebuild_index:
        actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if run_lint:
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return actions, summary_path


def clean_text(value: object) -> str:
    return str(value or "").strip()


def clean_filename(filename: str) -> str:
    raw_name = Path(filename or "upload").name
    stem = Path(raw_name).stem
    suffix = Path(raw_name).suffix.lower()
    safe_stem = slugify(stem)
    if not safe_stem:
        safe_stem = "upload"
    safe_suffix = re.sub(r"[^a-z0-9.]", "", suffix)
    return f"{safe_stem}{safe_suffix}"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def remove_empty_parents(path: Path, stop: Path) -> None:
    current = path
    stop = stop.resolve()
    while current.exists() and current.resolve() != stop:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def maybe_move_local_upload(local_path: str, old_domain: str, new_domain: str, year: str) -> str:
    if not local_path:
        return local_path
    path = Path(local_path).expanduser().resolve()
    if not path.exists():
        return local_path
    try:
        relative = path.relative_to(RAW_UPLOADS.resolve())
    except ValueError:
        return local_path
    parts = relative.parts
    if len(parts) < 3 or parts[0] != old_domain:
        return local_path

    target_dir = RAW_UPLOADS / new_domain / year
    target_dir.mkdir(parents=True, exist_ok=True)
    target = unique_path(target_dir / path.name)
    path.replace(target)
    remove_empty_parents(path.parent, RAW_UPLOADS)
    return str(target)


def resolve_payload_domain(payload: dict) -> tuple[str, str]:
    requested = clean_text(payload.get("domain")) or "general"
    new_label = clean_text(payload.get("new_domain_label"))
    new_slug = clean_text(payload.get("new_domain_slug"))

    if requested == "__new__" or new_label or new_slug:
        domain_label = new_label or new_slug
        if not domain_label:
            raise ValueError("新增学科需要填写名称")
        domain_slug = slugify(new_slug or domain_label)
        if not domain_slug:
            raise ValueError("新增学科标识不能为空")
        return domain_slug, domain_label

    return resolve_domain(requested)


def save_upload(payload: dict) -> dict:
    filename = clean_text(payload.get("filename"))
    data_base64 = clean_text(payload.get("content_base64"))
    date = clean_text(payload.get("date")) or dt.date.today().isoformat()
    if not filename:
        raise ValueError("缺少文件名")
    if not data_base64:
        raise ValueError("缺少文件内容")

    try:
        file_bytes = base64.b64decode(data_base64, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"文件内容不是有效 base64: {exc}") from exc
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("文件过大，当前单文件上限为 120MB")

    domain_slug, domain_label = resolve_payload_domain(payload)
    safe_name = clean_filename(filename)
    target_dir = RAW_UPLOADS / domain_slug / date[:4]
    target_dir.mkdir(parents=True, exist_ok=True)
    target = unique_path(target_dir / safe_name)
    target.write_bytes(file_bytes)

    return {
        "ok": True,
        "domain": domain_slug,
        "domain_label": domain_label,
        "filename": target.name,
        "relative_path": str(target.relative_to(ROOT)),
        "absolute_path": str(target),
        "size": len(file_bytes),
    }


def label_from_domain_page(domain_slug: str) -> str | None:
    domain_page = DOMAIN_PAGES / f"{domain_slug}.md"
    if not domain_page.exists():
        return None
    title = parse_frontmatter(domain_page).get("title", "").strip()
    suffix = " Knowledge Network"
    if title.endswith(suffix):
        return title[: -len(suffix)]
    return title or None


def label_from_raw_sources(domain_slug: str) -> str | None:
    for path in raw_source_files(domain_slug):
        label = parse_frontmatter(path).get("domain_label", "").strip()
        if label:
            return label
    return None


def domain_label_for(domain_slug: str, fallback: str | None = None) -> str:
    known = {slug: label for slug, label in DOMAIN_OPTIONS}
    return (
        known.get(domain_slug)
        or label_from_raw_sources(domain_slug)
        or label_from_domain_page(domain_slug)
        or fallback
        or domain_slug
    )


def build_source_payload(payload: dict) -> tuple[Path, str, dict]:
    title = clean_text(payload.get("title"))
    if not title:
        raise ValueError("标题不能为空")

    kind = clean_text(payload.get("kind")) or "article"
    date = clean_text(payload.get("date")) or dt.date.today().isoformat()
    if len(date) < 10:
        raise ValueError("日期需要使用 YYYY-MM-DD")

    domain_slug, domain_label = resolve_payload_domain(payload)
    slug = clean_text(payload.get("slug")) or slugify(title)
    target_dir = RAW_SOURCES / domain_slug / date[:4]
    target = target_dir / f"{date}-{slug}.md"

    source_url = clean_text(payload.get("source_url") or payload.get("url"))
    local_path = clean_text(payload.get("local_path"))
    tags = [domain_slug]
    for tag in parse_extra_tags(clean_text(payload.get("tags"))):
        if tag not in tags:
            tags.append(tag)

    source_type = clean_text(payload.get("source_type")) or infer_source_type(kind, source_url, local_path)
    status = clean_text(payload.get("status")) or "inbox"
    author = clean_text(payload.get("author"))
    published = clean_text(payload.get("published"))
    context = clean_text(payload.get("context"))
    original_content = clean_text(payload.get("original_content"))
    notes = clean_text(payload.get("notes"))

    content = build_content(
        title,
        kind,
        source_type,
        date,
        domain_slug,
        domain_label,
        status,
        source_url,
        local_path,
        author,
        published,
        tags,
    )
    content = content.replace(
        "为什么要收录这份资料？它与当前 wiki 的哪条主线相关？",
        context or "为什么要收录这份资料？它与当前 wiki 的哪条主线相关？",
    )
    content = content.replace(
        "把原文、摘录、转写或清洗后的正文放在这里。",
        original_content or "把原文、摘录、转写或清洗后的正文放在这里。",
    )
    content = content.replace(
        "可补充少量人工备注，但尽量不要破坏原始内容的可追溯性。",
        notes or "可补充少量人工备注，但尽量不要破坏原始内容的可追溯性。",
    )

    meta = {
        "domain_slug": domain_slug,
        "domain_label": domain_label,
        "relative_path": str(target.relative_to(ROOT)),
    }
    return target, content, meta


def create_source(payload: dict, dry_run: bool = False) -> dict:
    target, content, meta = build_source_payload(payload)
    if target.exists() and not dry_run:
        raise FileExistsError(f"文件已存在：{target.relative_to(ROOT)}")

    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    actions: list[dict] = []
    summary_path = ""
    domain_slug = meta["domain_slug"]
    if not dry_run and payload.get("auto_ingest", False):
        actions, summary_path = run_ingest_pipeline(meta["relative_path"], payload)
    elif not dry_run:
        if payload.get("rebuild_domain", True):
            actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))
        if payload.get("rebuild_index", True):
            actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
        if payload.get("run_lint", False):
            actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "dry_run": dry_run,
        "path": meta["relative_path"],
        "domain": domain_slug,
        "summary": summary_path,
        "content": content if dry_run else "",
        "actions": actions,
    }


def update_source_domain(payload: dict) -> dict:
    source_path = clean_text(payload.get("path"))
    if not source_path:
        raise ValueError("缺少 raw source 路径")

    old_path = raw_path_from_relative(source_path)
    old_domain = raw_source_domain(old_path)
    new_domain, new_label = resolve_payload_domain(payload)
    if old_domain == new_domain:
        meta = parse_frontmatter(old_path)
        write_frontmatter(old_path, {"domain": new_domain, "domain_label": new_label})
        actions, summary_path = run_ingest_pipeline(str(old_path.relative_to(ROOT)), {**payload, "overwrite_ingest": True})
        return {
            "ok": all(action["ok"] for action in actions),
            "path": str(old_path.relative_to(ROOT)),
            "old_domain": old_domain,
            "new_domain": new_domain,
            "summary": summary_path,
            "actions": actions,
        }

    meta = parse_frontmatter(old_path)
    created = clean_text(meta.get("created")) or dt.date.today().isoformat()
    year = created[:4] if len(created) >= 4 else old_path.parent.name
    target_dir = RAW_SOURCES / new_domain / year
    target = target_dir / old_path.name
    if target.exists():
        raise FileExistsError(f"目标学科已有同名 raw source：{target.relative_to(ROOT)}")

    tags = parse_inline_list(meta.get("tags"))
    tags = [tag for tag in tags if tag != old_domain]
    if new_domain not in tags:
        tags.insert(0, new_domain)

    local_path = maybe_move_local_upload(clean_text(meta.get("local_path")), old_domain, new_domain, year)
    updates = {
        "domain": new_domain,
        "domain_label": new_label,
        "local_path": local_path,
        "tags": f"[{', '.join(tags)}]",
    }
    write_frontmatter(old_path, updates)

    target_dir.mkdir(parents=True, exist_ok=True)
    old_path.replace(target)
    remove_empty_parents(old_path.parent, RAW_SOURCES / old_domain)

    actions, summary_path = run_ingest_pipeline(
        str(target.relative_to(ROOT)),
        {
            **payload,
            "overwrite_ingest": True,
            "rebuild_domain": True,
            "rebuild_index": True,
            "old_domain_for_concepts": old_domain,
        },
    )
    actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", old_domain]))
    actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if payload.get("run_lint", False):
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions),
        "path": str(target.relative_to(ROOT)),
        "old_path": source_path,
        "old_domain": old_domain,
        "new_domain": new_domain,
        "summary": summary_path,
        "actions": actions,
    }


def list_domains() -> dict:
    domains = []
    known = {slug: label for slug, label in DOMAIN_OPTIONS}
    if RAW_SOURCES.exists():
        for path in RAW_SOURCES.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                known.setdefault(path.name, domain_label_for(path.name))
    if DOMAIN_PAGES.exists():
        for path in DOMAIN_PAGES.glob("*.md"):
            if not path.name.startswith("."):
                known.setdefault(path.stem, domain_label_for(path.stem))

    for slug, label in sorted(known.items()):
        sources = raw_source_files(slug)
        domain_page = DOMAIN_PAGES / f"{slug}.md"
        domains.append(
            {
                "slug": slug,
                "label": domain_label_for(slug, label),
                "source_count": len(sources),
                "wiki_page_count": wiki_pages_for_domain(slug),
                "domain_page": str(domain_page.relative_to(ROOT)) if domain_page.exists() else "",
            }
        )
    return {"domains": domains}


def recent_sources(limit: int = 12) -> dict:
    files = raw_source_files()
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    rows = []
    for path in files[:limit]:
        meta = parse_frontmatter(path)
        rows.append(
            {
                "title": meta.get("title") or path.stem,
                "domain": meta.get("domain") or path.parent.parent.name,
                "kind": meta.get("kind") or "source",
                "status": meta.get("status") or "unknown",
                "path": str(path.relative_to(ROOT)),
                "source_url": meta.get("source_url") or "",
                "local_path": meta.get("local_path") or "",
            }
        )
    return {"sources": rows}


def concept_files_for_domain(domain_slug: str) -> list[Path]:
    if not WIKI_CONCEPTS.exists():
        return []
    files: list[Path] = []
    for path in sorted(WIKI_CONCEPTS.glob("*.md")):
        meta = parse_frontmatter(path)
        if meta.get("type") != "concept":
            continue
        tags = parse_inline_list(meta.get("tags"))
        if domain_slug in tags:
            files.append(path)
    return files


def concept_catalog(domain_slug: str | None = None) -> list[dict]:
    files = concept_files_for_domain(domain_slug) if domain_slug else sorted(WIKI_CONCEPTS.glob("*.md"))
    concepts: list[dict] = []
    for path in files:
        meta = parse_frontmatter(path)
        if meta.get("type") != "concept":
            continue
        title = meta.get("title") or path.stem
        concepts.append(
            {
                "id": slugify(title),
                "slug": path.stem,
                "label": title,
                "summary": meta.get("summary") or "",
                "path": str(path.relative_to(ROOT)),
                "tags": parse_inline_list(meta.get("tags")),
            }
        )
    return sorted(concepts, key=lambda item: item["label"].lower())


def concept_file_by_slug(slug: str) -> Path:
    safe_slug = slugify(slug)
    direct = WIKI_CONCEPTS / f"{safe_slug}.md"
    if direct.exists():
        return direct
    for path in WIKI_CONCEPTS.glob("*.md"):
        meta = parse_frontmatter(path)
        if slugify(meta.get("title") or path.stem) == safe_slug:
            return path
    raise FileNotFoundError(slug)


def relation_evidence(raw: str) -> str:
    if not raw:
        return ""
    evidence = raw
    if "evidence:" in evidence:
        evidence = evidence.split("evidence:", 1)[1]
    evidence = evidence.rstrip(") ").strip()
    return evidence


def concept_graph(domain_slug: str) -> dict:
    if not domain_slug:
        domain_slug = "general"

    nodes_by_label: dict[str, dict] = {}
    edges: list[dict] = []
    relation_pattern = re.compile(r"^-\s+`([^`]+)`\s+--(.+?)-->\s+`([^`]+)`(?:\s+\((.+)\))?")

    def add_node(label: str, path: str = "") -> None:
        if not label:
            return
        node_id = slugify(label)
        existing = nodes_by_label.get(label)
        if existing:
            if path and not existing.get("path"):
                existing["path"] = path
            return
        nodes_by_label[label] = {
            "id": node_id,
            "label": label,
            "path": path,
        }

    concept_files = concept_files_for_domain(domain_slug)
    for path in concept_files:
        meta = parse_frontmatter(path)
        title = meta.get("title") or path.stem
        add_node(title, str(path.relative_to(ROOT)))
        for line in path.read_text(encoding="utf-8").splitlines():
            match = relation_pattern.match(line.strip())
            if not match:
                continue
            source, relation, target, evidence_raw = match.groups()
            add_node(source)
            add_node(target)
            edge_id = f"{slugify(source)}::{slugify(relation)}::{slugify(target)}"
            if any(edge["id"] == edge_id for edge in edges):
                continue
            edges.append(
                {
                    "id": edge_id,
                    "source": slugify(source),
                    "source_label": source,
                    "relation": relation.strip(),
                    "target": slugify(target),
                    "target_label": target,
                    "evidence": relation_evidence(evidence_raw or ""),
                    "concept_page": str(path.relative_to(ROOT)),
                }
            )

    return {
        "domain": domain_slug,
        "domain_label": domain_label_for(domain_slug),
        "nodes": sorted(nodes_by_label.values(), key=lambda node: node["label"].lower()),
        "edges": edges,
        "relations": edges,
        "concept_count": len(concept_files),
        "relation_count": len(edges),
        "domain_page": str((DOMAIN_PAGES / f"{domain_slug}.md").relative_to(ROOT)),
    }


def concept_page(slug: str, domain_slug: str | None = None) -> dict:
    path = concept_file_by_slug(slug)
    meta, body = parse_frontmatter_and_body(path)
    title = meta.get("title") or path.stem
    domain = domain_slug or next((tag for tag in parse_inline_list(meta.get("tags")) if tag != "auto-concept"), "")
    graph = concept_graph(domain) if domain else {"edges": []}
    concept_id = slugify(title)
    related_edges = [
        edge
        for edge in graph.get("edges", [])
        if edge.get("source") == concept_id or edge.get("target") == concept_id
    ]
    return {
        "slug": path.stem,
        "id": concept_id,
        "title": title,
        "summary": meta.get("summary") or "",
        "status": meta.get("status") or "",
        "updated": meta.get("updated") or "",
        "tags": parse_inline_list(meta.get("tags")),
        "sources": parse_inline_list(meta.get("sources")),
        "path": str(path.relative_to(ROOT)),
        "body": body,
        "domain": domain,
        "domain_label": domain_label_for(domain) if domain else "",
        "catalog": concept_catalog(domain) if domain else concept_catalog(),
        "related_edges": related_edges,
    }


def safe_static_path(route_path: str) -> Path:
    if route_path in {"", "/"}:
        route_path = "/index.html"
    candidate = (WEBUI / route_path.lstrip("/")).resolve()
    if WEBUI.resolve() not in candidate.parents and candidate != WEBUI.resolve():
        raise FileNotFoundError(route_path)
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


class WikiWebHandler(BaseHTTPRequestHandler):
    server_version = "LLMWikiWeb/0.1"

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        try:
            path = safe_static_path(parsed.path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(parsed.path)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", MIME_TYPES.get(path.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(path.stat().st_size))
            self.end_headers()
        except FileNotFoundError:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/domains":
            write_json(self, list_domains())
            return
        if parsed.path == "/api/sources/recent":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["12"])[0])
            write_json(self, recent_sources(limit))
            return
        if parsed.path == "/api/concepts/graph":
            query = parse_qs(parsed.query)
            domain = clean_text(query.get("domain", ["general"])[0])
            write_json(self, concept_graph(domain))
            return
        if parsed.path == "/api/concepts/page":
            query = parse_qs(parsed.query)
            slug = clean_text(query.get("slug", [""])[0])
            domain = clean_text(query.get("domain", [""])[0])
            if not slug:
                write_json(self, {"ok": False, "error": "缺少 concept slug"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                write_json(self, concept_page(slug, domain or None))
            except FileNotFoundError:
                write_json(self, {"ok": False, "error": f"Concept not found: {slug}"}, HTTPStatus.NOT_FOUND)
            return
        if parsed.path == "/api/health":
            write_json(self, {"ok": True, "root": str(ROOT)})
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = read_json(self)
            if parsed.path == "/api/sources":
                write_json(self, create_source(payload))
                return
            if parsed.path == "/api/sources/preview":
                write_json(self, create_source(payload, dry_run=True))
                return
            if parsed.path == "/api/uploads":
                write_json(self, save_upload(payload))
                return
            if parsed.path == "/api/sources/domain":
                write_json(self, update_source_domain(payload))
                return
            if parsed.path == "/api/ingest":
                source_path = clean_text(payload.get("path"))
                if not source_path:
                    raise ValueError("缺少 raw source 路径")
                actions, summary_path = run_ingest_pipeline(source_path, payload)
                write_json(
                    self,
                    {
                        "ok": all(action["ok"] for action in actions),
                        "path": source_path,
                        "summary": summary_path,
                        "actions": actions,
                    },
                )
                return
            if parsed.path == "/api/rebuild":
                domain = clean_text(payload.get("domain"))
                actions = []
                if domain:
                    actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain]))
                else:
                    actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py"]))
                actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
                if payload.get("run_lint", True):
                    actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))
                write_json(self, {"ok": all(action["ok"] for action in actions), "actions": actions})
                return
            write_json(self, {"ok": False, "error": "Unknown endpoint"}, HTTPStatus.NOT_FOUND)
        except FileExistsError as exc:
            write_json(self, {"ok": False, "error": str(exc)}, HTTPStatus.CONFLICT)
        except ValueError as exc:
            write_json(self, {"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            write_json(self, {"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def serve_static(self, route_path: str) -> None:
        try:
            path = safe_static_path(route_path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(route_path)
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", MIME_TYPES.get(path.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            write_json(self, {"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local LLM Wiki web intake UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), WikiWebHandler)
    print(f"LLM Wiki web UI: http://{args.host}:{args.port}")
    print(f"Root: {ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
