#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlparse


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT / "scripts"
WEBUI = ROOT / "webui"
SCIVERSE_SKILL = ROOT.parent / ".agents" / "skills" / "sciverse"
RAW_SOURCES = ROOT / "raw" / "sources"
RAW_UPLOADS = ROOT / "raw" / "assets" / "uploads"
WIKI = ROOT / "wiki"
DOMAIN_PAGES = WIKI / "domains"
WIKI_CONCEPTS = WIKI / "concepts"
WIKI_SOURCES = WIKI / "sources"
CONCEPT_ARCHIVE = WIKI / ".archive" / "concepts"
CONCEPT_ARCHIVE_LOG = WIKI / ".archive" / "concept-actions.jsonl"
DELETED_DOMAINS_FILE = ROOT / ".llm-wiki-deleted-domains.json"
MAX_UPLOAD_BYTES = 120 * 1024 * 1024
SCIVERSE_BASE_URL = os.environ.get("SCIVERSE_BASE_URL", "https://api.sciverse.space").rstrip("/")
SCIVERSE_KEYCHAIN_SERVICE = os.environ.get("SCIVERSE_KEYCHAIN_SERVICE", "llm-wiki-sciverse")

sys.path.insert(0, str(SCRIPT_DIR))
import auto_ingest as auto_ingest_lib  # noqa: E402
import mvp_batch_automation  # noqa: E402
import mvp_concept_reviews  # noqa: E402
import mvp_ingest_artifacts as mvp_artifacts  # noqa: E402
from mvp_ingest_runner import run_mvp_ingest  # noqa: E402
from new_source import build_content, infer_source_type, parse_extra_tags, resolve_domain, slugify  # noqa: E402


MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


DOMAIN_OPTIONS = [
    ("ai", "ai"),
    ("ai智能体", "ai智能体"),
    ("math", "数学"),
    ("modern-astronomy", "现代天文学"),
    ("physics", "物理"),
    ("tibetan-astronomy-calendar", "西藏天文历算"),
    ("世界模型", "世界模型"),
    ("垂直小模型", "垂直小模型"),
]
AUTO_DISCOVER_DOMAINS = False


def allowed_domain_slugs() -> set[str]:
    return {slug for slug, _label in DOMAIN_OPTIONS}


def is_allowed_domain(domain_slug: str) -> bool:
    return domain_slug in allowed_domain_slugs()


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


def inline_list(items: list[str]) -> str:
    return f"[{', '.join(item for item in items if item)}]"


def load_deleted_domains() -> set[str]:
    if not DELETED_DOMAINS_FILE.exists():
        return set()
    try:
        payload = json.loads(DELETED_DOMAINS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(payload, list):
        return {clean_text(item) for item in payload if clean_text(item)}
    return set()


def save_deleted_domains(domains: set[str]) -> None:
    if domains:
        DELETED_DOMAINS_FILE.write_text(
            json.dumps(sorted(domains), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    elif DELETED_DOMAINS_FILE.exists():
        DELETED_DOMAINS_FILE.unlink()


def remember_deleted_domain(domain_slug: str) -> None:
    deleted = load_deleted_domains()
    deleted.add(domain_slug)
    save_deleted_domains(deleted)


def restore_deleted_domain(domain_slug: str) -> None:
    deleted = load_deleted_domains()
    if domain_slug in deleted:
        deleted.remove(domain_slug)
        save_deleted_domains(deleted)


def compact_spaces(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def first_present(*values: object) -> str:
    for value in values:
        if isinstance(value, list):
            joined = ", ".join(compact_spaces(item) for item in value if compact_spaces(item))
            if joined:
                return joined
        cleaned = compact_spaces(value)
        if cleaned:
            return cleaned
    return ""


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


def friendly_sciverse_error(stderr: str, script_name: str) -> str:
    text = stderr or ""
    if "SCIVERSE_API_TOKEN" in text:
        return "Sciverse token 未配置或为空。请在面板填写 token，或用 start_llm_wiki.command 从 Keychain 启动。"
    if "UND_ERR_SOCKET" in text or "fetch failed" in text or "other side closed" in text:
        return (
            "Sciverse 网络连接被中断。当前更像是本机代理/VPN/TUN/fake-ip 的 TLS 连接问题，"
            "不是 token 或 LLM Wiki 写入问题。请切换代理节点/模式后重试，或在终端用 "
            "`curl -Iv https://api.sciverse.space` 检查 TLS 是否能连通。"
        )
    if "Sciverse API 401" in text or "Sciverse API 403" in text:
        return "Sciverse token 认证失败，请检查 token 是否完整、是否过期，或重新生成后存入 Keychain。"
    if "Sciverse API 429" in text:
        return "Sciverse 请求过于频繁或达到限额，请稍后重试。"
    if "Sciverse API" in text:
        return text.splitlines()[0][:600]
    return (text or f"Sciverse command failed: {script_name}")[:600]


def keychain_sciverse_token() -> str:
    if sys.platform != "darwin":
        return ""
    completed = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            os.environ.get("USER", ""),
            "-s",
            SCIVERSE_KEYCHAIN_SERVICE,
            "-w",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def is_sciverse_socket_error(stderr: str) -> bool:
    text = stderr or ""
    return "UND_ERR_SOCKET" in text or "fetch failed" in text or "other side closed" in text


def validate_sciverse_base_url() -> None:
    parsed = urlparse(SCIVERSE_BASE_URL)
    hostname = parsed.hostname or ""
    if hostname != "sciverse.space" and not hostname.endswith(".sciverse.space"):
        raise ValueError("SCIVERSE_BASE_URL 必须指向 sciverse.space 或 *.sciverse.space")


def sciverse_endpoint_for(script_name: str) -> tuple[str, str]:
    endpoints = {
        "semantic_search.mjs": ("POST", "/agentic-search"),
        "search_papers.mjs": ("POST", "/meta-search"),
        "read_content.mjs": ("GET", "/content"),
    }
    if script_name not in endpoints:
        raise ValueError(f"Sciverse curl fallback does not support: {script_name}")
    return endpoints[script_name]


def sciverse_curl_run(script_name: str, payload: dict, token: str) -> dict:
    validate_sciverse_base_url()
    method, endpoint = sciverse_endpoint_for(script_name)
    url = f"{SCIVERSE_BASE_URL}{endpoint}"
    headers = [
        "-H",
        f"authorization: Bearer {token}",
        "-H",
        "content-type: application/json",
        "-H",
        f"x-request-id: llm-wiki-curl-{uuid.uuid4()}",
    ]
    args = ["curl", "-fsS", "--connect-timeout", "20", "--max-time", "120", "-X", method, *headers]
    input_data = None
    if method == "GET":
        query = urlencode({key: str(value) for key, value in payload.items() if value is not None and str(value) != ""})
        if query:
            url = f"{url}?{query}"
    else:
        input_data = json.dumps(payload, ensure_ascii=False)
        args.extend(["--data-binary", "@-"])
    args.append(url)
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        text=True,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        raise ValueError(friendly_sciverse_error(completed.stderr.strip(), script_name))
    try:
        result = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Sciverse curl fallback 返回了非 JSON 内容: {completed.stdout[:240]}") from exc
    return {
        "ok": True,
        "script": script_name,
        "transport": "curl-fallback",
        "payload": payload,
        "result": result,
    }


def sciverse_run(script_name: str, payload: dict, token: str = "") -> dict:
    effective_token = os.environ.get("SCIVERSE_API_TOKEN") or token or keychain_sciverse_token()
    if not effective_token:
        raise ValueError(
            "Sciverse 尚未启用：请先运行 scripts/store_sciverse_token.command 存入 Keychain，"
            "或在面板填写本次会话 token。"
        )
    if os.environ.get("SCIVERSE_TRANSPORT", "").lower() == "curl":
        return sciverse_curl_run(script_name, payload, effective_token)
    script = SCIVERSE_SKILL / "scripts" / script_name
    if not script.exists():
        raise FileNotFoundError(f"Sciverse script not found: {script}")
    completed = subprocess.run(
        ["node", str(script), json.dumps(payload, ensure_ascii=False)],
        cwd=SCIVERSE_SKILL,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ.copy(), "SCIVERSE_API_TOKEN": effective_token},
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        if is_sciverse_socket_error(stderr):
            return sciverse_curl_run(script_name, payload, effective_token)
        raise ValueError(friendly_sciverse_error(stderr, script_name))
    try:
        result = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Sciverse 返回了非 JSON 内容: {completed.stdout[:240]}") from exc
    return {
        "ok": True,
        "script": script_name,
        "transport": "node-skill",
        "payload": payload,
        "result": result,
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


def run_mvp_ingest_pipeline(source_path: str, payload: dict) -> tuple[list[dict], str, dict]:
    overwrite = bool(payload.get("overwrite_ingest", True))
    result = run_mvp_ingest(source_path, overwrite=overwrite)
    summary_path = clean_text(result.get("wiki_source_path"))
    action = {
        "command": f"mvp_ingest {source_path}",
        "returncode": 0 if result.get("ok") else 1,
        "stdout": json.dumps(result, ensure_ascii=False),
        "stderr": clean_text(result.get("error")),
        "ok": bool(result.get("ok")),
    }
    return [action], summary_path, result


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


def iso_timestamp() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def archive_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]


def append_concept_archive_log(record: dict) -> None:
    CONCEPT_ARCHIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CONCEPT_ARCHIVE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def archive_concept_page(path: Path, action: str, reason: str = "", extra: dict | None = None) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    meta = parse_frontmatter(path)
    record_id = archive_id()
    CONCEPT_ARCHIVE.mkdir(parents=True, exist_ok=True)
    archived_path = unique_path(CONCEPT_ARCHIVE / f"{record_id}-{path.name}")
    original_rel = str(path.relative_to(ROOT))
    archived_rel = str(archived_path.relative_to(ROOT))
    domains = [tag for tag in parse_inline_list(meta.get("tags")) if tag != "auto-concept"]
    record = {
        "id": record_id,
        "created_at": iso_timestamp(),
        "action": action,
        "reason": reason,
        "label": meta.get("title") or path.stem,
        "original_path": original_rel,
        "archived_path": archived_rel,
        "domains": domains,
        "sources": parse_inline_list(meta.get("sources")),
        "extra": extra or {},
    }
    path.replace(archived_path)
    (CONCEPT_ARCHIVE / f"{record_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_concept_archive_log(record)
    return record


def concept_archive_record(record_id: str) -> dict:
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", record_id)
    if not safe_id:
        raise ValueError("缺少 archive id")
    record_path = CONCEPT_ARCHIVE / f"{safe_id}.json"
    if not record_path.exists():
        raise FileNotFoundError(record_id)
    return json.loads(record_path.read_text(encoding="utf-8"))


def recent_concept_archives(limit: int = 12) -> list[dict]:
    if not CONCEPT_ARCHIVE.exists():
        return []
    records: list[dict] = []
    for record_path in CONCEPT_ARCHIVE.glob("*.json"):
        try:
            records.append(json.loads(record_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return records[:limit]


def restore_concept_archive_record(record_id: str) -> dict:
    record = concept_archive_record(record_id)
    archived_path = (ROOT / record["archived_path"]).resolve()
    if not archived_path.exists():
        raise FileNotFoundError(record["archived_path"])
    original_path = (ROOT / record["original_path"]).resolve()
    if WIKI_CONCEPTS.resolve() not in original_path.parents:
        raise ValueError("archive 记录的原路径不在 wiki/concepts 下")
    original_path.parent.mkdir(parents=True, exist_ok=True)
    restored_path = unique_path(original_path)
    archived_path.replace(restored_path)
    restored = {
        **record,
        "restored_at": iso_timestamp(),
        "restored_path": str(restored_path.relative_to(ROOT)),
    }
    (CONCEPT_ARCHIVE / f"{record['id']}.json").write_text(
        json.dumps(restored, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    append_concept_archive_log({"event": "restore", **restored})
    return restored


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
        raise ValueError("已禁用自动新增学科。请先选择现有学科。")

    domain_slug, domain_label = resolve_domain(requested)
    if not is_allowed_domain(domain_slug):
        raise ValueError(f"已禁用自动新增学科：{domain_slug}")
    return domain_slug, domain_label


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
    restore_deleted_domain(domain_slug)
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


def enrich_wechat_payload(payload: dict) -> tuple[dict, dict]:
    enriched = dict(payload)
    source_url = clean_text(enriched.get("source_url") or enriched.get("url"))
    if "mp.weixin.qq.com" not in source_url:
        return enriched, {}
    needs_fetch = not clean_text(enriched.get("title")) or not clean_text(enriched.get("original_content"))
    if not needs_fetch:
        return enriched, {}
    text, status, info = auto_ingest_lib.fetch_wechat_with_crawler(source_url)
    if not text:
        raise ValueError(f"微信文章抓取失败：{status}")
    if not clean_text(enriched.get("title")):
        enriched["title"] = clean_text(info.get("title")) or "微信文章"
    if not clean_text(enriched.get("author")):
        enriched["author"] = clean_text(info.get("author"))
    if not clean_text(enriched.get("published")):
        enriched["published"] = clean_text(info.get("publish_time"))
    if not clean_text(enriched.get("date")) and clean_text(info.get("publish_time")):
        enriched["date"] = clean_text(info.get("publish_time"))[:10]
    if not clean_text(enriched.get("original_content")):
        enriched["original_content"] = text[:120_000]
    return enriched, {
        "status": status,
        "title": clean_text(info.get("title")),
        "author": clean_text(info.get("author")),
        "published": clean_text(info.get("publish_time")),
        "extracted_chars": len(text),
    }


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
    enriched_payload, import_info = enrich_wechat_payload(payload)
    target, content, meta = build_source_payload(enriched_payload)
    if target.exists() and not dry_run:
        raise FileExistsError(f"文件已存在：{target.relative_to(ROOT)}")

    if not dry_run:
        restore_deleted_domain(meta["domain_slug"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    actions: list[dict] = []
    summary_path = ""
    ingest_result: dict | None = None
    domain_slug = meta["domain_slug"]
    if not dry_run and enriched_payload.get("auto_ingest", False):
        actions, summary_path, ingest_result = run_mvp_ingest_pipeline(
            meta["relative_path"],
            {**enriched_payload, "overwrite_ingest": True},
        )
        if ingest_result and ingest_result.get("source_id"):
            source_id = ingest_result["source_id"]
            try:
                ingest_result["concept_reviews"] = mvp_concept_reviews.merged_candidates(source_id)
                ingest_result["relation_reviews"] = mvp_concept_reviews.merged_relations(source_id)
                ingest_result["accepted_graph"] = mvp_concept_reviews.project_accepted_graph(source_id)
            except FileNotFoundError:
                pass
    elif not dry_run:
        if enriched_payload.get("rebuild_domain", True):
            actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))
        if enriched_payload.get("rebuild_index", True):
            actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
        if enriched_payload.get("run_lint", False):
            actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "dry_run": dry_run,
        "path": meta["relative_path"],
        "domain": domain_slug,
        "summary": summary_path,
        "ingest_result": ingest_result,
        "import_info": import_info,
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
    restore_deleted_domain(new_domain)
    if old_domain == new_domain:
        meta = parse_frontmatter(old_path)
        write_frontmatter(old_path, {"domain": new_domain, "domain_label": new_label})
        actions, summary_path, ingest_result = run_mvp_ingest_pipeline(
            str(old_path.relative_to(ROOT)),
            {**payload, "overwrite_ingest": True},
        )
        return {
            "ok": all(action["ok"] for action in actions),
            "path": str(old_path.relative_to(ROOT)),
            "old_domain": old_domain,
            "new_domain": new_domain,
            "summary": summary_path,
            "ingest_result": ingest_result,
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

    actions, summary_path, ingest_result = run_mvp_ingest_pipeline(
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
        "ingest_result": ingest_result,
        "actions": actions,
    }


def sciverse_search(payload: dict) -> dict:
    query = clean_text(payload.get("query"))
    if not query:
        raise ValueError("缺少 Sciverse 检索问题或关键词")

    search_type = clean_text(payload.get("search_type")) or "semantic"
    token = clean_text(payload.get("token"))
    if search_type == "metadata":
        request: dict[str, object] = {
            "query": query,
            "page_size": max(1, min(int(payload.get("page_size") or 10), 50)),
        }
        return sciverse_run("search_papers.mjs", request, token)

    request = {
        "query": query,
        "top_k": max(1, min(int(payload.get("top_k") or 5), 30)),
        "mode": clean_text(payload.get("mode")) or "balanced",
    }
    source_types = payload.get("source_types")
    if isinstance(source_types, list) and source_types:
        request["source_types"] = source_types
    return sciverse_run("semantic_search.mjs", request, token)


def science_tracker(payload: dict) -> dict:
    query = clean_text(payload.get("query")) or "hierarchical memory"
    page_size = max(1, min(int(payload.get("page_size") or 8), 30))
    year_from = clean_text(payload.get("year_from")) or str(dt.date.today().year - 1)
    year_to = clean_text(payload.get("year_to")) or str(dt.date.today().year)
    request = {
        "query": f"Science {query} {year_from} {year_to}",
        "page_size": page_size,
    }
    result = sciverse_run("search_papers.mjs", request, clean_text(payload.get("token")))
    return {
        **result,
        "tracker": {
            "name": "Science main journal",
            "query": query,
            "journals": ["Science"],
            "year_from": int(year_from),
            "year_to": int(year_to),
            "page_size": page_size,
            "filter_mode": "query-biased",
        },
    }


def normalize_sciverse_paper(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        raw = {}
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    paper = raw.get("paper") if isinstance(raw.get("paper"), dict) else {}
    document = raw.get("document") if isinstance(raw.get("document"), dict) else {}
    source = {**document, **paper, **metadata, **raw}
    title = first_present(
        source.get("title"),
        source.get("paper_title"),
        source.get("document_title"),
        "Untitled paper",
    )
    doi = first_present(source.get("doi"), source.get("DOI"))
    source_url = first_present(source.get("url"), source.get("source_url"), source.get("pdf_url"))
    if not source_url and doi:
        source_url = f"https://doi.org/{doi}"
    return {
        "title": title,
        "doc_id": first_present(source.get("doc_id"), source.get("document_id"), source.get("paper_id"), source.get("id")),
        "year": first_present(source.get("year"), source.get("publication_year"), source.get("published")),
        "venue": first_present(source.get("venue"), source.get("journal"), source.get("source")),
        "authors": first_present(source.get("authors"), source.get("author")),
        "doi": doi,
        "score": first_present(source.get("score"), source.get("similarity"), source.get("rank_score")),
        "excerpt": first_present(
            source.get("text"),
            source.get("chunk_text"),
            source.get("excerpt"),
            source.get("snippet"),
            source.get("abstract"),
        ),
        "offset": first_present(source.get("offset"), source.get("start_offset")),
        "source_url": source_url,
    }


def sciverse_source_content(paper: dict[str, str], query: str = "") -> str:
    lines = []
    if query:
        lines.append(f"Retrieval query: {query}")
        lines.append("")
    lines.append(paper["excerpt"] or "暂无 Sciverse 摘录。")
    return "\n".join(lines)


def sciverse_metadata_notes(paper: dict[str, str], query: str = "") -> str:
    lines = [
        "Sciverse metadata for traceability. These fields are not concepts.",
        f"- Title: {paper['title']}",
        f"- Doc ID: {paper['doc_id'] or 'unknown'}",
        f"- Authors: {paper['authors'] or 'unknown'}",
        f"- Year: {paper['year'] or 'unknown'}",
        f"- Venue: {paper['venue'] or 'unknown'}",
        f"- DOI: {paper['doi'] or 'unknown'}",
        f"- Score: {paper['score'] or 'unknown'}",
    ]
    if query:
        lines.append(f"- Retrieval query: {query}")
    if paper["offset"]:
        lines.append(f"- Offset: {paper['offset']}")
    return "\n".join(lines)


def sciverse_import_source(payload: dict) -> dict:
    paper = normalize_sciverse_paper(payload.get("paper") or payload)
    if not paper["title"] or paper["title"] == "Untitled paper":
        raise ValueError("Sciverse 结果缺少论文标题")
    domain = clean_text(payload.get("domain")) or "general"
    query = clean_text(payload.get("query"))
    extra_tags = ["sciverse", "academic"]
    for tag in parse_extra_tags(clean_text(payload.get("tags"))):
        if tag not in extra_tags:
            extra_tags.append(tag)
    create_payload = {
        "title": paper["title"],
        "kind": "paper",
        "source_type": "sciverse",
        "date": clean_text(payload.get("date")) or dt.date.today().isoformat(),
        "domain": domain,
        "status": "active",
        "source_url": paper["source_url"],
        "author": paper["authors"],
        "published": paper["year"],
        "tags": ", ".join(extra_tags),
        "context": clean_text(payload.get("context")) or "Sciverse 学术检索导入，用于补强当前知识网络的论文证据。",
        "original_content": sciverse_source_content(paper, query),
        "notes": sciverse_metadata_notes(paper, query),
        "auto_ingest": bool(payload.get("auto_ingest", True)),
        "concept_network": bool(payload.get("allow_sciverse_concepts", False)),
        "rebuild_domain": bool(payload.get("rebuild_domain", True)),
        "rebuild_index": bool(payload.get("rebuild_index", True)),
        "run_lint": bool(payload.get("run_lint", False)),
    }
    result = create_source(create_payload, dry_run=bool(payload.get("dry_run", False)))
    return {"ok": result["ok"], "paper": paper, "source": result}


def evidence_line_from_paper(paper: dict[str, str], source_path: str = "") -> str:
    citation_bits = []
    if paper["doc_id"]:
        citation_bits.append(f"doc_id: {paper['doc_id']}")
    if paper["doi"]:
        citation_bits.append(f"DOI: {paper['doi']}")
    if paper["year"]:
        citation_bits.append(paper["year"])
    citation = "; ".join(citation_bits) or "Sciverse"
    locator = source_path or paper["source_url"]
    if locator.startswith("wiki/sources/"):
        locator = f"../sources/{Path(locator).name}"
    elif locator.startswith("wiki/"):
        locator = f"../{Path(locator).relative_to('wiki')}"
    label = paper["title"]
    if locator:
        link = f"[{label}]({locator})"
    else:
        link = label
    excerpt = paper["excerpt"] or "待补：需要从 Sciverse read_content 或论文原文补充证据片段。"
    return f"- {link} ({citation}): {excerpt}"


def append_markdown_section(body: str, heading: str, line: str, before_heading: str = "## Open Questions") -> tuple[str, bool]:
    if line in body:
        return body, False
    lines = body.splitlines()
    section_index = next((index for index, item in enumerate(lines) if item.strip() == heading), -1)
    if section_index >= 0:
        insert_at = len(lines)
        for index in range(section_index + 1, len(lines)):
            if lines[index].startswith("## "):
                insert_at = index
                break
        prefix = [] if insert_at > section_index + 1 and lines[insert_at - 1].strip() == "" else [""]
        lines[insert_at:insert_at] = [*prefix, line]
        return "\n".join(lines).rstrip() + "\n", True

    insert_at = next((index for index, item in enumerate(lines) if item.strip() == before_heading), len(lines))
    block = [heading, "", line, ""]
    if insert_at > 0 and lines[insert_at - 1].strip() != "":
        block.insert(0, "")
    lines[insert_at:insert_at] = block
    return "\n".join(lines).rstrip() + "\n", True


def add_academic_evidence(payload: dict) -> dict:
    slug = clean_text(payload.get("slug"))
    if not slug:
        raise ValueError("缺少 concept slug")
    paper = normalize_sciverse_paper(payload.get("paper") or payload)
    source_path = clean_text(payload.get("source_path"))
    path = concept_file_by_slug(slug)
    frontmatter, body_lines = split_frontmatter(path)
    if not frontmatter:
        raise ValueError("concept page 缺少 frontmatter")
    body = "\n".join(body_lines).strip()
    line = evidence_line_from_paper(paper, source_path)
    updated_body, changed = append_markdown_section(body, "## Academic Evidence", line)
    dry_run = bool(payload.get("dry_run", False))
    if changed and not dry_run:
        write_frontmatter(path, {"updated": dt.date.today().isoformat()})
        frontmatter, _ = split_frontmatter(path)
        path.write_text("\n".join([*frontmatter, "", updated_body]).rstrip() + "\n", encoding="utf-8")
    return {
        "ok": True,
        "dry_run": dry_run,
        "changed": changed,
        "path": str(path.relative_to(ROOT)),
        "paper": paper,
        "evidence": line,
        "preview": updated_body if dry_run else "",
    }


def list_domains() -> dict:
    domains = []
    deleted_domains = load_deleted_domains()
    known = {slug: label for slug, label in DOMAIN_OPTIONS if slug not in deleted_domains}
    if AUTO_DISCOVER_DOMAINS and RAW_SOURCES.exists():
        for path in RAW_SOURCES.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                known.setdefault(path.name, domain_label_for(path.name))
    if AUTO_DISCOVER_DOMAINS and DOMAIN_PAGES.exists():
        for path in DOMAIN_PAGES.glob("*.md"):
            if not path.name.startswith(".") and path.stem not in deleted_domains:
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
        ingest_preview = mvp_ingest_preview(path)
        rows.append(
            {
                "title": meta.get("title") or path.stem,
                "domain": meta.get("domain") or path.parent.parent.name,
                "kind": meta.get("kind") or "source",
                "status": meta.get("status") or "unknown",
                "path": str(path.relative_to(ROOT)),
                "source_id": ingest_preview["source_id"],
                "ingest": ingest_preview,
                "source_url": meta.get("source_url") or "",
                "local_path": meta.get("local_path") or "",
            }
        )
    return {"sources": rows}


def extract_body_sections(body: str) -> dict[str, str]:
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


def source_summary_paths_for_raw(raw_rel: str) -> list[Path]:
    matches: list[Path] = []
    for path in wiki_source_files():
        meta = parse_frontmatter(path)
        if raw_rel in parse_inline_list(meta.get("sources")):
            matches.append(path)
    return matches


def mvp_ingest_preview(path: Path) -> dict:
    try:
        source_id = mvp_artifacts.source_id_for_path(path)
    except Exception:
        return {
            "source_id": "",
            "status": None,
            "summary": None,
            "concept_candidates": [],
            "relation_candidates": [],
        }

    status = mvp_artifacts.read_status(source_id)
    summary = None
    concepts: list[dict] = []
    try:
        summary = mvp_artifacts.read_json_artifact(source_id, "source_summary")
    except Exception:
        summary = None
    try:
        concept_payload = mvp_artifacts.read_json_artifact(source_id, "concept_candidates")
        concepts = list(concept_payload.get("concept_candidates") or [])
    except Exception:
        concepts = []
    try:
        concept_reviews = mvp_concept_reviews.merged_candidates(source_id)
    except Exception:
        concept_reviews = None
    try:
        relation_reviews = mvp_concept_reviews.merged_relations(source_id)
    except Exception:
        relation_reviews = None
    try:
        accepted_graph = mvp_concept_reviews.project_accepted_graph(source_id)
    except Exception:
        accepted_graph = None

    return {
        "source_id": source_id,
        "status": status,
        "artifact_updated_at": mvp_artifacts.artifact_updated_at(source_id),
        "summary": summary,
        "concept_candidates": concepts[:10],
        "concept_reviews": concept_reviews,
        "relation_reviews": relation_reviews,
        "accepted_graph": accepted_graph,
    }


def source_row(path: Path, include_body: bool = False) -> dict:
    meta, body = parse_frontmatter_and_body(path)
    sections = extract_body_sections(body)
    raw_rel = str(path.relative_to(ROOT))
    summaries = source_summary_paths_for_raw(raw_rel)
    ingest_preview = mvp_ingest_preview(path)
    row = {
        "title": meta.get("title") or path.stem,
        "domain": meta.get("domain") or raw_source_domain(path),
        "domain_label": meta.get("domain_label") or domain_label_for(meta.get("domain") or raw_source_domain(path)),
        "kind": meta.get("kind") or "source",
        "source_type": meta.get("source_type") or "",
        "status": meta.get("status") or "unknown",
        "source_url": meta.get("source_url") or "",
        "local_path": meta.get("local_path") or "",
        "author": meta.get("author") or "",
        "published": meta.get("published") or "",
        "created": meta.get("created") or "",
        "tags": ", ".join(tag for tag in parse_inline_list(meta.get("tags")) if tag != (meta.get("domain") or "")),
        "path": raw_rel,
        "source_id": ingest_preview["source_id"],
        "ingest": ingest_preview,
        "summary_paths": [str(summary.relative_to(ROOT)) for summary in summaries],
    }
    if include_body:
        row.update(
            {
                "context": sections.get("Context", ""),
                "original_content": sections.get("Original Content Or Extract", ""),
                "notes": sections.get("Notes", ""),
            }
        )
    return row


def list_sources(domain_slug: str | None = None) -> dict:
    files = raw_source_files(domain_slug)
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    domain = domain_slug or "all"
    return {
        "domain": domain,
        "domain_label": domain_label_for(domain) if domain_slug else "全部",
        "sources": [source_row(path, include_body=True) for path in files],
    }


def update_source(payload: dict) -> dict:
    source_path = clean_text(payload.get("path"))
    if not source_path:
        raise ValueError("缺少 raw source 路径")
    path = raw_path_from_relative(source_path)
    meta, body = parse_frontmatter_and_body(path)
    sections = extract_body_sections(body)
    domain_slug = raw_source_domain(path)
    domain_label = meta.get("domain_label") or domain_label_for(domain_slug)
    created = clean_text(meta.get("created")) or dt.date.today().isoformat()
    title = clean_text(payload.get("title")) or meta.get("title") or path.stem
    kind = clean_text(payload.get("kind")) or meta.get("kind") or "article"
    source_url = clean_text(payload.get("source_url")) if "source_url" in payload else clean_text(meta.get("source_url"))
    local_path = clean_text(payload.get("local_path")) if "local_path" in payload else clean_text(meta.get("local_path"))
    source_type = clean_text(payload.get("source_type")) or meta.get("source_type") or infer_source_type(kind, source_url, local_path)
    status = clean_text(payload.get("status")) or meta.get("status") or "inbox"
    author = clean_text(payload.get("author")) if "author" in payload else clean_text(meta.get("author"))
    published = clean_text(payload.get("published")) if "published" in payload else clean_text(meta.get("published"))
    context = clean_text(payload.get("context")) if "context" in payload else sections.get("Context", "")
    original_content = (
        clean_text(payload.get("original_content"))
        if "original_content" in payload
        else sections.get("Original Content Or Extract", "")
    )
    notes = clean_text(payload.get("notes")) if "notes" in payload else sections.get("Notes", "")

    tags = [domain_slug]
    for tag in parse_extra_tags(clean_text(payload.get("tags"))):
        if tag not in tags:
            tags.append(tag)
    if "tags" not in payload:
        for tag in parse_inline_list(meta.get("tags")):
            if tag not in tags:
                tags.append(tag)

    content = build_content(
        title,
        kind,
        source_type,
        created,
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
    path.write_text(content, encoding="utf-8")

    actions: list[dict] = []
    summary_path = ""
    ingest_result: dict | None = None
    pipeline_payload = {**payload, "overwrite_ingest": True}
    if source_type == "sciverse":
        pipeline_payload["concept_network"] = False
    if payload.get("auto_ingest", True):
        actions, summary_path, ingest_result = run_mvp_ingest_pipeline(str(path.relative_to(ROOT)), pipeline_payload)
    else:
        if payload.get("rebuild_domain", True):
            actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))
        if payload.get("rebuild_index", True):
            actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
        if payload.get("run_lint", False):
            actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "path": str(path.relative_to(ROOT)),
        "summary": summary_path,
        "ingest_result": ingest_result,
        "actions": actions,
    }


def section_needs_supplement(value: str) -> bool:
    cleaned = auto_ingest_lib.remove_placeholders(value or "")
    if not cleaned.strip():
        return True
    return auto_ingest_lib.is_blocked_or_boilerplate(cleaned)


def extract_external_source_text(meta: dict[str, str]) -> tuple[str, str, dict[str, str]]:
    source_url = clean_text(meta.get("source_url"))
    local_path = clean_text(meta.get("local_path"))
    if source_url:
        if "mp.weixin.qq.com" in source_url:
            text, status, info = auto_ingest_lib.fetch_wechat_with_crawler(source_url)
            if text:
                return text, status, info
        text, status = auto_ingest_lib.fetch_web_text(source_url)
        return text, status, {}
    if local_path:
        text, status = auto_ingest_lib.read_local_text(local_path)
        return text, status, {}
    return "", "skipped: no source_url or local_path", {}


def source_summary_fallback_text(raw_rel: str) -> str:
    snippets: list[str] = []
    for summary_path in source_summary_paths_for_raw(raw_rel):
        _meta, summary_body = parse_frontmatter_and_body(summary_path)
        snippets.extend(markdown_list_items(summary_body, "## Main Takeaways", 8))
        snippets.extend(markdown_list_items(summary_body, "## Extracted Notes", 8))
    cleaned = [strip_markdown_inline(item) for item in snippets]
    cleaned = [item for item in cleaned if item and "待补" not in item]
    return "\n".join(f"- {item}" for item in cleaned[:12]).strip()


def automatic_source_context(title: str, domain_label: str) -> str:
    return (
        f"自动补充：这份资料属于「{domain_label}」资料库，用于补强《{title}》相关的核心观点、"
        "概念证据和学科网络关系。"
    )


def automatic_source_notes(status: str, info: dict[str, str]) -> str:
    lines = [
        "自动补充记录：",
        f"- 抽取状态：{status}",
        f"- 补充时间：{dt.datetime.now().isoformat(timespec='seconds')}",
    ]
    if info.get("author"):
        lines.append(f"- 抽取作者：{info['author']}")
    if info.get("publish_time"):
        lines.append(f"- 抽取发表时间：{info['publish_time']}")
    if info.get("html_length"):
        lines.append(f"- HTML 长度：{info['html_length']}")
    lines.append("- 原始链接、本地路径和 raw source 保持可追溯。")
    return "\n".join(lines)


def auto_supplement_proposal(payload: dict) -> dict:
    source_path = clean_text(payload.get("path"))
    if not source_path:
        raise ValueError("缺少 raw source 路径")
    path = raw_path_from_relative(source_path)
    meta, body = parse_frontmatter_and_body(path)
    sections = extract_body_sections(body)
    domain_slug = raw_source_domain(path)
    domain_label = meta.get("domain_label") or domain_label_for(domain_slug)
    title = meta.get("title") or path.stem

    external_text, extraction_status, extraction_info = extract_external_source_text(meta)
    external_text = auto_ingest_lib.remove_placeholders(external_text)
    if external_text and auto_ingest_lib.is_blocked_or_boilerplate(external_text):
        external_text = ""
    if clean_text(meta.get("local_path")) and extraction_status == "local path not found":
        raise FileNotFoundError(f"文件不存在：{clean_text(meta.get('local_path'))}")
    if not external_text:
        fallback_text = source_summary_fallback_text(str(path.relative_to(ROOT)))
        if fallback_text:
            external_text = fallback_text
            extraction_status = "source summary fallback"

    context = sections.get("Context", "")
    original_content = sections.get("Original Content Or Extract", "")
    notes = sections.get("Notes", "")

    filled: list[str] = []
    if section_needs_supplement(context):
        context = automatic_source_context(title, domain_label)
        filled.append("context")
    if section_needs_supplement(original_content) and external_text:
        original_content = external_text[:80_000].strip()
        filled.append("original_content")
    if section_needs_supplement(notes):
        notes = automatic_source_notes(extraction_status, extraction_info)
        filled.append("notes")

    author = meta.get("author", "")
    published = meta.get("published", "")
    if not clean_text(author) and extraction_info.get("author"):
        author = extraction_info["author"]
        filled.append("author")
    if not clean_text(published) and extraction_info.get("publish_time"):
        published = extraction_info["publish_time"]
        filled.append("published")

    update_payload = {
        **payload,
        "path": str(path.relative_to(ROOT)),
        "title": title,
        "kind": meta.get("kind") or "article",
        "source_url": meta.get("source_url") or "",
        "local_path": meta.get("local_path") or "",
        "source_type": meta.get("source_type") or infer_source_type(meta.get("kind") or "article", meta.get("source_url"), meta.get("local_path")),
        "status": meta.get("status") or "active",
        "author": author,
        "published": published,
        "tags": ", ".join(tag for tag in parse_inline_list(meta.get("tags")) if tag != domain_slug),
        "context": context,
        "original_content": original_content,
        "notes": notes,
        "auto_ingest": bool(payload.get("auto_ingest", True)),
        "concept_network": bool(payload.get("concept_network", True)),
        "rebuild_domain": bool(payload.get("rebuild_domain", True)),
        "rebuild_index": bool(payload.get("rebuild_index", True)),
        "run_lint": bool(payload.get("run_lint", False)),
    }
    return {
        "ok": True,
        "path": str(path.relative_to(ROOT)),
        "applied": False,
        "proposal": update_payload,
        "supplement": {
            "filled": filled,
            "extraction_status": extraction_status,
            "extracted_chars": len(external_text),
            "source": str(path.relative_to(ROOT)),
        },
    }


def auto_supplement_source(payload: dict) -> dict:
    proposal = auto_supplement_proposal(payload)
    if not bool(payload.get("apply", False)):
        return proposal
    result = update_source(proposal["proposal"])
    return {
        **result,
        "applied": True,
        "proposal": proposal["proposal"],
        "supplement": proposal["supplement"],
    }


def cleanup_concepts_for_deleted_sources(summary_paths: list[Path], delete_orphans: bool = True) -> dict:
    changed_pages: list[str] = []
    deleted_pages: list[str] = []
    archived_pages: list[dict] = []
    cleaned_relation_refs: list[str] = []
    deleted_refs = {str(path.relative_to(ROOT)) for path in summary_paths}
    deleted_refs.update(path.name for path in summary_paths)

    for path in WIKI_CONCEPTS.glob("*.md"):
        if not path.exists():
            continue
        meta = parse_frontmatter(path)
        sources = parse_inline_list(meta.get("sources"))
        matching_sources = [source for source in sources if source in deleted_refs or Path(source).name in deleted_refs]
        remaining_sources = [source for source in sources if source not in matching_sources and Path(source).name not in deleted_refs]
        tags = parse_inline_list(meta.get("tags"))
        is_orphan_auto_concept = delete_orphans and matching_sources and not remaining_sources and "auto-concept" in tags
        label = meta.get("title") or path.stem

        if is_orphan_auto_concept:
            archive = archive_concept_page(path, "delete_orphan", "source summary was deleted")
            deleted_pages.append(str(path.relative_to(ROOT)))
            archived_pages.append(archive)
            cleaned_relation_refs.extend(remove_concept_relation_refs(label))
            continue

        lines = path.read_text(encoding="utf-8").splitlines()
        kept = []
        changed = False
        for line in lines:
            if any(ref in line for ref in deleted_refs):
                changed = True
                continue
            kept.append(line)
        if changed:
            path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")
            changed_pages.append(str(path.relative_to(ROOT)))
        if matching_sources and remaining_sources:
            write_frontmatter(path, {"sources": f"[{', '.join(remaining_sources)}]"})
            rel = str(path.relative_to(ROOT))
            if rel not in changed_pages:
                changed_pages.append(rel)

    return {
        "changed_pages": sorted(set(changed_pages)),
        "deleted_pages": sorted(set(deleted_pages)),
        "archived_pages": archived_pages,
        "cleaned_relation_refs": sorted(set(cleaned_relation_refs)),
    }


def cleanup_concepts_for_deleted_domain(domain_slug: str, summary_paths: list[Path]) -> dict:
    cleaned = cleanup_concepts_for_deleted_sources(summary_paths, delete_orphans=True)
    changed_pages = set(cleaned.get("changed_pages", []))
    deleted_pages = set(cleaned.get("deleted_pages", []))
    archived_pages = list(cleaned.get("archived_pages", []))
    cleaned_relation_refs = set(cleaned.get("cleaned_relation_refs", []))

    for path in WIKI_CONCEPTS.glob("*.md"):
        rel = str(path.relative_to(ROOT))
        if rel in deleted_pages or not path.exists():
            continue
        meta = parse_frontmatter(path)
        if meta.get("type") != "concept":
            continue
        tags = parse_inline_list(meta.get("tags"))
        if domain_slug not in tags:
            continue

        remaining_tags = [tag for tag in tags if tag != domain_slug]
        domain_tags = [tag for tag in remaining_tags if tag != "auto-concept"]
        label = meta.get("title") or path.stem
        if "auto-concept" in tags and not domain_tags:
            archive = archive_concept_page(path, "delete_domain_orphan", f"domain {domain_slug} was deleted")
            deleted_pages.add(rel)
            archived_pages.append(archive)
            cleaned_relation_refs.update(remove_concept_relation_refs(label))
            continue

        if not remaining_tags:
            remaining_tags = ["general"]
        write_frontmatter(path, {"tags": inline_list(remaining_tags)})
        changed_pages.add(rel)

    return {
        "changed_pages": sorted(changed_pages - deleted_pages),
        "deleted_pages": sorted(deleted_pages),
        "archived_pages": archived_pages,
        "cleaned_relation_refs": sorted(cleaned_relation_refs),
    }


def delete_source(payload: dict) -> dict:
    source_path = clean_text(payload.get("path"))
    if not source_path:
        raise ValueError("缺少 raw source 路径")
    path = raw_path_from_relative(source_path)
    domain_slug = raw_source_domain(path)
    raw_rel = str(path.relative_to(ROOT))
    summaries = source_summary_paths_for_raw(raw_rel)
    delete_summary = bool(payload.get("delete_summary", True))
    delete_orphan_concepts = bool(payload.get("delete_orphan_concepts", True))
    deleted = [raw_rel]
    cleaned_concepts: dict = {"changed_pages": [], "deleted_pages": [], "cleaned_relation_refs": []}

    path.unlink()
    remove_empty_parents(path.parent, RAW_SOURCES / domain_slug)

    if delete_summary:
        cleaned_concepts = cleanup_concepts_for_deleted_sources(summaries, delete_orphan_concepts)
        for summary in summaries:
            if summary.exists():
                summary.unlink()
                deleted.append(str(summary.relative_to(ROOT)))

    actions = []
    if payload.get("rebuild_domain", True):
        actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))
    if payload.get("rebuild_index", True):
        actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if payload.get("run_lint", False):
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "deleted": deleted,
        "cleaned_concepts": cleaned_concepts,
        "domain": domain_slug,
        "actions": actions,
    }


def delete_domain(payload: dict) -> dict:
    domain_slug = clean_text(payload.get("domain"))
    if not domain_slug or domain_slug == "__new__":
        raise ValueError("缺少学科")

    domain_label = domain_label_for(domain_slug)
    raw_files = raw_source_files(domain_slug)
    raw_rels = [str(path.relative_to(ROOT)) for path in raw_files]
    summaries = {
        summary
        for raw_rel in raw_rels
        for summary in source_summary_paths_for_raw(raw_rel)
    }
    summaries.update(
        path
        for path in wiki_source_files()
        if summary_domain(path, parse_frontmatter(path)) == domain_slug
    )
    summary_paths = sorted(summaries)

    cleaned_concepts = cleanup_concepts_for_deleted_domain(domain_slug, summary_paths)
    deleted: list[str] = []

    for summary in summary_paths:
        if summary.exists():
            deleted.append(str(summary.relative_to(ROOT)))
            summary.unlink()

    raw_root = RAW_SOURCES / domain_slug
    if raw_root.exists():
        shutil.rmtree(raw_root)
        deleted.extend(raw_rels)

    domain_page = DOMAIN_PAGES / f"{domain_slug}.md"
    had_domain_page = domain_page.exists()
    if had_domain_page:
        deleted.append(str(domain_page.relative_to(ROOT)))
        domain_page.unlink()

    remember_deleted_domain(domain_slug)

    actions = []
    if payload.get("rebuild_domains", True):
        actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py"]))
    if payload.get("rebuild_index", True):
        actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if payload.get("run_lint", False):
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "domain": domain_slug,
        "domain_label": domain_label,
        "deleted": sorted(set(deleted)),
        "deleted_counts": {
            "raw_sources": len(raw_rels),
            "source_summaries": len(summary_paths),
            "domain_page": 1 if had_domain_page else 0,
        },
        "cleaned_concepts": cleaned_concepts,
        "local_uploads_deleted": False,
        "actions": actions,
    }


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


def wiki_source_files() -> list[Path]:
    if not WIKI_SOURCES.exists():
        return []
    return sorted(
        path
        for path in WIKI_SOURCES.rglob("*.md")
        if path.name.lower() != "readme.md" and not path.name.startswith(".")
    )


def summary_domain(path: Path, meta: dict[str, str]) -> str:
    tags = [tag for tag in parse_inline_list(meta.get("tags")) if tag not in {"source", "auto-source"}]
    if tags:
        return tags[0]
    for source in parse_inline_list(meta.get("sources")):
        parts = Path(source).parts
        if len(parts) >= 3 and parts[0] == "raw" and parts[1] == "sources":
            return parts[2]
    return "general"


def concept_review_reason(body: str) -> str:
    checks = [
        ("待整理", "需要确认概念定义"),
        ("待补：尚未抽取到稳定概念关系", "缺少稳定关系"),
        ("这个概念是否应该保留为独立页面", "需要决定是否独立成页"),
        ("是否存在跨学科桥接价值", "需要判断跨学科价值"),
    ]
    for marker, reason in checks:
        if marker in body:
            return reason
    return ""


NOISE_CONCEPT_TERMS = {
    "abstract",
    "academic",
    "auth",
    "author",
    "authors",
    "doc id",
    "doc_id",
    "doi",
    "excerpt",
    "offset",
    "paper",
    "retrieval",
    "score",
    "source",
    "title",
    "venue",
    "year",
    "the",
}

CORE_CONCEPT_TERMS = {
    "ai",
    "attention mechanism",
    "attention mechanisms",
    "attention mechanism 注意力机制",
    "bp",
    "large language model",
    "large language models",
    "llm",
    "nli",
    "noise leading in",
    "self attention",
    "transformer",
    "transformers",
    "人工智能",
    "不完全的归纳法",
    "大语言模型",
    "归纳法",
    "知识论",
    "真信念且证成",
    "结构化的噪声引入",
    "语言模型",
    "大语言模型",
    "注意力机制",
    "自注意力",
    "自注意力机制",
}

TOOL_ENTITY_TERMS = {
    "anthropic",
    "article-copilot",
    "claude",
    "claude api",
    "crea",
    "creator",
    "cursor",
    "github",
    "kenneth",
    "mulerun",
    "openai",
    "sciverse",
    "simon",
    "vs code",
    "yann lecun",
    "yann-lecun",
}

BAD_CONCEPT_PHRASE_PREFIXES = (
    "与",
    "如果",
    "或者",
    "只要",
    "你",
    "过去",
    "随着",
    "对",
    "几个",
    "一些",
    "这些",
    "于是",
    "而是",
    "这个",
    "这种",
    "那些",
)

BAD_CONCEPT_PHRASE_MARKERS = (
    "与早期",
    "如果说",
    "或Gemini",
    "等大语言模型",
    "几个",
    "几个人工智能模型",
    "一次解决",
    "成千上万",
    "你可以",
    "过去数学家",
    "这些模型",
    "随着AI模型",
    "对AI模型",
    "或者",
    "只要",
    "去年大家",
    "试图把",
    "真正写过",
    "触碰到",
    "落地天花板",
    "单纯的",
    "简单草图",
    "核心业务",
)

CONCEPT_ALIAS_GROUPS = [
    ["AI", "人工智能", "Artificial Intelligence"],
    ["LLM", "大语言模型", "Large Language Model", "Large Language Models"],
    ["注意力机制", "Attention Mechanism", "Attention Mechanisms"],
    ["NLI", "Noise Leading In", "结构化的噪声引入"],
]

CONCEPT_DEFINITION_OVERRIDES = {
    "ai": "AI（人工智能）是研究和构造能够执行感知、推理、生成、规划或行动等智能任务的计算系统与方法。",
    "人工智能": "人工智能（AI）是研究和构造能够执行感知、推理、生成、规划或行动等智能任务的计算系统与方法。",
    "llm": "LLM（大语言模型）是以大规模文本和代码数据训练的语言模型，能够根据上下文生成、理解和转换自然语言或程序文本。",
    "大语言模型": "大语言模型（LLM）是以大规模文本和代码数据训练的语言模型，能够根据上下文生成、理解和转换自然语言或程序文本。",
    "transformer": "Transformer 是一种以注意力机制为核心的神经网络架构，用来在序列内部直接建模不同位置之间的依赖关系。",
    "注意力机制": "注意力机制是一类让模型按上下文动态分配信息权重的方法，用于突出当前任务最相关的输入位置或表示。",
    "attention mechanism": "Attention Mechanism（注意力机制）是一类让模型按上下文动态分配信息权重的方法，用于突出当前任务最相关的输入位置或表示。",
    "语言模型": "语言模型是估计文本序列概率或生成下一个文本单元的模型，是现代自然语言处理和大语言模型的基础。",
}

CONCEPT_RELATION_PATTERN = re.compile(r"^-\s+`([^`]+)`\s+--(.+?)-->\s+`([^`]+)`(?:\s+\((.+)\))?")


def alias_group_for(label: str) -> list[str]:
    normalized = normalize_concept_term(label)
    for group in CONCEPT_ALIAS_GROUPS:
        if any(normalize_concept_term(item) == normalized for item in group):
            return group
    return []


def alias_candidates_for(label: str) -> list[str]:
    normalized = normalize_concept_term(label)
    return [item for item in alias_group_for(label) if normalize_concept_term(item) != normalized]


def alias_target_for(title: str, current_slug: str, catalog_by_slug: dict[str, dict]) -> dict | None:
    group = alias_group_for(title)
    if not group:
        return None
    current_norm = normalize_concept_term(title)
    by_norm = {
        normalize_concept_term(item["label"]): item
        for item in catalog_by_slug.values()
        if item.get("label")
    }
    for candidate in group:
        candidate_norm = normalize_concept_term(candidate)
        item = by_norm.get(candidate_norm)
        if item and item.get("slug") != current_slug and candidate_norm != current_norm:
            return item
    for item in catalog_by_slug.values():
        if item.get("slug") != current_slug and normalize_concept_term(item.get("label", "")) in {
            normalize_concept_term(candidate) for candidate in group
        }:
            return item
    return None


def markdown_list_items(body: str, heading: str, limit: int = 4) -> list[str]:
    section = markdown_section(body, heading)
    items: list[str] = []
    for line in section.splitlines():
        text = line.strip()
        if not text.startswith("- "):
            continue
        cleaned = text[2:].strip()
        if cleaned and cleaned not in items:
            items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def strip_markdown_inline(value: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", value)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def evidence_source_labels(body: str, limit: int = 4) -> list[str]:
    labels: list[str] = []
    for item in markdown_list_items(body, "## Source-Derived Evidence", limit=20):
        match = re.match(r"\[([^\]]+)\]\([^)]+\)", item)
        label = match.group(1).strip() if match else ""
        if label and label not in labels:
            labels.append(label)
        if len(labels) >= limit:
            break
    return labels


def concept_lead_definition(title: str, summary: str, body: str, domain_label: str) -> str:
    normalized = normalize_concept_term(title)
    if normalized in CONCEPT_DEFINITION_OVERRIDES:
        return CONCEPT_DEFINITION_OVERRIDES[normalized]
    for alias in alias_candidates_for(title):
        alias_norm = normalize_concept_term(alias)
        if alias_norm in CONCEPT_DEFINITION_OVERRIDES:
            return CONCEPT_DEFINITION_OVERRIDES[alias_norm]
    definition_items = markdown_list_items(body, "## Working Definition", limit=1)
    if definition_items:
        text = strip_markdown_inline(definition_items[0])
        text = re.sub(r"^在资料《.+?》中，(.+?) 的当前工作性理解来自这条摘录：", f"{title}：", text)
        text = re.sub(r"^(.+?) 是从资料《.+?》中抽取出的候选概念；", f"{title} 是一个来自资料抽取的候选概念；", text)
        if text:
            return text
    if summary:
        return strip_markdown_inline(summary)
    return f"{title} 是 {domain_label or '当前学科'} 知识网络中的概念页；它的定义、边界和证据仍可继续整理。"


def concept_introduction_reason(meta: dict[str, str], body: str) -> str:
    sources = evidence_source_labels(body, 2)
    if sources:
        return f"由资料《{'》《'.join(sources)}》中的摘录或关系自动引入。"
    source_paths = parse_inline_list(meta.get("sources"))
    if source_paths:
        return f"由 {len(source_paths)} 条 source-derived 记录自动引入。"
    return "由自动抽取流程引入，当前缺少明确证据来源。"


def concept_relation_ref_pages(label: str) -> list[str]:
    refs: list[str] = []
    label_slug = slugify(label)
    for path in WIKI_CONCEPTS.glob("*.md"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = CONCEPT_RELATION_PATTERN.match(line.strip())
            if not match:
                continue
            source, _, target, _ = match.groups()
            if slugify(source) == label_slug or slugify(target) == label_slug:
                refs.append(str(path.relative_to(ROOT)))
                break
    return sorted(set(refs))


def markdown_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == heading), -1)
    if start < 0:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start + 1 : end]).strip()


def replace_markdown_section(body: str, heading: str, replacement_lines: list[str]) -> str:
    lines = body.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == heading), -1)
    if start < 0:
        return "\n".join([body.rstrip(), "", heading, "", *replacement_lines]).rstrip() + "\n"
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    lines[start:end] = [heading, "", *replacement_lines]
    return "\n".join(lines).rstrip() + "\n"


def concept_evidence_count(body: str) -> int:
    section = markdown_section(body, "## Source-Derived Evidence")
    count = 0
    for line in section.splitlines():
        text = line.strip()
        if not text.startswith("- "):
            continue
        if "暂无" in text or "待补" in text:
            continue
        count += 1
    return count


def concept_relation_count(body: str) -> int:
    section = markdown_section(body, "## Source-Derived Relations")
    return sum(1 for line in section.splitlines() if line.strip().startswith("- `") and "--" in line)


def concept_is_auto(meta: dict[str, str]) -> bool:
    return "auto-concept" in parse_inline_list(meta.get("tags"))


def normalize_concept_term(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[-_/]+", " ", value).strip().lower())


def concept_noise_reason(title: str) -> str:
    normalized = normalize_concept_term(title)
    if normalized in CORE_CONCEPT_TERMS:
        return ""
    compact = title.strip()
    if compact.startswith(BAD_CONCEPT_PHRASE_PREFIXES) or any(marker in compact for marker in BAD_CONCEPT_PHRASE_MARKERS):
        return "叙述性句子片段或观点短语，不适合作为独立概念页"
    if "的" in compact and len(compact) >= 6 and normalized not in CORE_CONCEPT_TERMS:
        return "修饰性短语，不适合作为独立概念页"
    if normalized in NOISE_CONCEPT_TERMS:
        return "元数据字段或检索字段，不应进入概念库"
    if normalized in TOOL_ENTITY_TERMS:
        return "工具、产品或人物实体，当前阶段不作为概念页保留"
    if len(normalized) <= 3 and normalized not in {"ai", "bp", "llm", "nli"}:
        return "过短且缺少稳定概念含义"
    return ""


def singular_candidate(label: str) -> str:
    normalized = label.strip()
    lower = normalized.lower()
    special = {
        "skills": "Skill",
        "agent skills": "Agent Skill",
        "claude skills": "Claude Skill",
    }
    if lower in special:
        return special[lower]
    if re.fullmatch(r"[A-Za-z][A-Za-z -]+s", normalized) and not lower.endswith("ss"):
        return normalized[:-1]
    return ""


def concept_organize_action(path: Path, domain_slug: str, catalog_by_slug: dict[str, dict]) -> dict:
    meta, body = parse_frontmatter_and_body(path)
    title = meta.get("title") or path.stem
    tags = parse_inline_list(meta.get("tags"))
    evidence_count = concept_evidence_count(body)
    relation_count = concept_relation_count(body)
    reason = concept_review_reason(body)
    is_auto = "auto-concept" in tags
    is_curated = "curated-concept" in tags
    noise_reason = concept_noise_reason(title)
    relation_ref_pages = concept_relation_ref_pages(title)
    base = {
        "slug": path.stem,
        "title": title,
        "path": str(path.relative_to(ROOT)),
        "evidence_count": evidence_count,
        "relation_count": relation_count,
        "review_reason": reason,
        "introduced_by": concept_introduction_reason(meta, body),
        "evidence_sources": evidence_source_labels(body),
        "evidence_preview": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Source-Derived Evidence", 2)],
        "alias_candidates": alias_candidates_for(title),
        "auto_concept": is_auto,
        "curated_concept": is_curated,
    }
    if is_curated:
        return {
            **base,
            "action": "already_curated",
            "confidence": "high",
            "reason": "已保留为正式概念，不需要进入自动整理队列",
            "apply": False,
            "affected_files": [str(path.relative_to(ROOT))],
        }

    if is_auto and noise_reason:
        return {
            **base,
            "action": "delete_noise",
            "confidence": "high",
            "reason": noise_reason,
            "apply": True,
            "affected_files": sorted(set([str(path.relative_to(ROOT)), *relation_ref_pages])),
        }

    alias_target = alias_target_for(title, path.stem, catalog_by_slug)
    if alias_target:
        target_path = clean_text(alias_target.get("path"))
        return {
            **base,
            "action": "merge_suggested",
            "confidence": "high",
            "reason": f"疑似同义词、缩写或中英翻译别名，建议并入“{alias_target['label']}”并作为 alias 保留",
            "target_slug": alias_target["slug"],
            "target_title": alias_target["label"],
            "apply": False,
            "affected_files": sorted(set([str(path.relative_to(ROOT)), target_path, *relation_ref_pages])),
        }

    singular = singular_candidate(title)
    if singular and slugify(singular) in catalog_by_slug and slugify(singular) != path.stem:
        target = catalog_by_slug[slugify(singular)]
        return {
            **base,
            "action": "merge_suggested",
            "confidence": "medium",
            "reason": f"疑似复数/变体，建议并入“{target['label']}”",
            "target_slug": target["slug"],
            "target_title": target["label"],
            "apply": False,
            "affected_files": sorted(set([str(path.relative_to(ROOT)), clean_text(target.get("path")), *relation_ref_pages])),
        }

    if is_auto and evidence_count >= 2 and relation_count >= 1 and "暂无与该概念直接匹配" not in body:
        return {
            **base,
            "action": "promote",
            "confidence": "medium",
            "reason": "已有证据和关系，可先保留为独立概念并移出待整理队列",
            "apply": True,
            "affected_files": [str(path.relative_to(ROOT))],
        }

    return {
        **base,
        "action": "manual_review",
        "confidence": "low",
        "reason": reason or "证据或关系不足，需要人工判断是否保留",
        "apply": False,
        "affected_files": [str(path.relative_to(ROOT))],
    }


def promote_concept(path: Path, domain_slug: str) -> str:
    meta, body = parse_frontmatter_and_body(path)
    title = meta.get("title") or path.stem
    tags = [tag for tag in parse_inline_list(meta.get("tags")) if tag != "auto-concept"]
    if "curated-concept" not in tags:
        tags.append("curated-concept")
    summary = meta.get("summary", "")
    if "自动提取" in summary or "等待人工整理" in summary or "候选概念" in summary:
        summary = f"{title} 是 {domain_label_for(domain_slug)} 知识网络中已保留的概念页，当前定义基于入库资料证据和概念关系，可继续精炼边界与跨学科连接。"
    write_frontmatter(
        path,
        {
            "updated": dt.date.today().isoformat(),
            "summary": summary,
            "tags": inline_list(tags),
        },
    )
    meta, body = parse_frontmatter_and_body(path)
    body = replace_markdown_section(
        body,
        "## Open Questions",
        [
            "- 自动整理：已保留为独立概念页。",
            "- 后续可继续补充更精确的定义、边界、反例和跨学科连接。",
        ],
    )
    frontmatter, _ = split_frontmatter(path)
    path.write_text("\n".join([*frontmatter, "", body]).rstrip() + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def concept_organizer_prompt(domain_slug: str) -> str:
    return f"""你是 LLM Wiki 的概念整理器。你的任务是整理 `{domain_slug}` 学科下由 ingest 自动生成的候选概念页。

LLM Wiki 原则：
1. raw sources 是不可修改的事实层；不得改写、删除或伪造原始资料。
2. wiki/concepts 是可维护的知识层；可以删除噪声、合并重复、重命名概念、补强定义和关系。
3. 每个动作都必须能追溯到 source-derived evidence 或明确说明证据不足。
4. 不要把工具、产品、作者、机构、元数据字段当作“概念”，除非它们在该学科中被明确作为研究对象。
5. 合并与删除必须保守；不确定时输出 manual_review。
6. 核心技术概念受保护：LLM、大语言模型、Transformer、Attention Mechanism、注意力机制、自注意力等默认不作为噪声删除；证据不足时输出 manual_review 或 keep，而不是 delete_noise。

判定标准：
- keep/promote：概念有稳定含义，有至少一条可引用证据，且能连接到学科问题或其他概念。
- delete_noise：Title、Author、Doc ID、Score、Retrieval、The 等元数据/停用词/抽取噪声。
- entity_not_concept：OpenAI、Claude、Cursor、GitHub、Anthropic 等工具/产品/实体；当前阶段默认不进入概念库。
- merge：复数、同义词、大小写、翻译变体或父子概念误拆，例如 Skills -> Skill。
- rename：名称不规范但概念值得保留，例如泛称、半句话、过长标题式概念。
- bridge：具备跨学科连接价值，需要保留并标记桥接方向。
- manual_review：证据不足、边界不清、可能有价值但无法自动判断。

请只输出 JSON，不要输出解释性散文。JSON schema：
{{
  "domain": "{domain_slug}",
  "decisions": [
    {{
      "slug": "concept-page-slug",
      "title": "当前标题",
      "decision": "keep|delete_noise|entity_not_concept|merge|rename|bridge|manual_review",
      "confidence": "high|medium|low",
      "target_slug": "合并目标，可为空",
      "new_title": "重命名目标，可为空",
      "definition": "若保留，给出一句清晰工作定义",
      "evidence": ["引用 source-derived evidence 的短句"],
      "reason": "为什么这样处理",
      "risk": "可能误判之处"
    }}
  ],
  "global_notes": ["对该学科概念网络的整体整理建议"]
}}
"""


def organize_concepts(payload: dict) -> dict:
    domain_slug = clean_text(payload.get("domain")) or "general"
    apply_changes = bool(payload.get("apply", False))
    concept_files = concept_files_for_domain(domain_slug)
    catalog = concept_catalog(domain_slug)
    catalog_by_slug = {item["slug"]: item for item in catalog}
    actions = [concept_organize_action(path, domain_slug, catalog_by_slug) for path in concept_files]
    actions = [action for action in actions if action["action"] != "already_curated"]
    actions.sort(key=lambda item: (item["action"], item["title"].lower()))

    applied: list[dict] = []
    affected_domains = {domain_slug}
    if apply_changes:
        for action in actions:
            path = WIKI_CONCEPTS / f"{action['slug']}.md"
            if not path.exists():
                continue
            if action["action"] == "delete_noise" and action.get("apply"):
                meta = parse_frontmatter(path)
                label = meta.get("title") or path.stem
                archive = archive_concept_page(path, "delete_noise", clean_text(action.get("reason")))
                cleaned_refs = remove_concept_relation_refs(label)
                applied.append({**action, "deleted": True, "archive": archive, "cleaned_refs": cleaned_refs})
            elif action["action"] == "promote" and action.get("apply"):
                updated_path = promote_concept(path, domain_slug)
                applied.append({**action, "updated": updated_path})

    command_results: list[dict] = []
    if apply_changes and applied:
        for domain in sorted(affected_domains):
            command_results.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain]))
        if payload.get("rebuild_index", True):
            command_results.append(shell_run(["python3", "scripts/rebuild_index.py"]))
        if payload.get("run_lint", False):
            command_results.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    counts: dict[str, int] = {}
    for action in actions:
        counts[action["action"]] = counts.get(action["action"], 0) + 1

    return {
        "ok": all(result["ok"] for result in command_results) if command_results else True,
        "domain": domain_slug,
        "domain_label": domain_label_for(domain_slug),
        "apply": apply_changes,
        "principles": [
            "raw sources 不修改，整理只作用于 wiki/concepts 层。",
            "明显噪声可删除，疑似合并只建议不自动执行。",
            "LLM、Transformer、Attention Mechanism / 注意力机制等核心技术概念默认不作为噪声删除。",
            "有证据和关系的候选概念可转为保留概念，并继续保留 source-derived evidence。",
        ],
        "llm_prompt": concept_organizer_prompt(domain_slug),
        "counts": counts,
        "actions": actions,
        "applied": applied,
        "command_results": command_results,
    }


def concept_decision(payload: dict) -> dict:
    slug = clean_text(payload.get("slug"))
    decision = clean_text(payload.get("decision"))
    domain_slug = clean_text(payload.get("domain")) or "general"
    if not slug:
        raise ValueError("缺少 concept slug")
    if decision not in {"promote", "keep", "delete", "delete_noise", "entity_not_concept"}:
        raise ValueError("不支持的概念处理动作")

    path = concept_file_by_slug(slug)
    meta = parse_frontmatter(path)
    label = meta.get("title") or path.stem
    actions: list[dict] = []
    result: dict[str, object]

    if decision in {"promote", "keep"}:
        updated_path = promote_concept(path, domain_slug)
        result = {
            "decision": "promote",
            "updated": updated_path,
            "label": label,
        }
    else:
        archive = archive_concept_page(path, decision, f"manual decision: {decision}")
        cleaned_refs = remove_concept_relation_refs(label)
        result = {
            "decision": "delete",
            "deleted": str(path.relative_to(ROOT)),
            "archive": archive,
            "label": label,
            "cleaned_refs": cleaned_refs,
        }

    if payload.get("rebuild_domain", True):
        actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain_slug]))
    if payload.get("rebuild_index", True):
        actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if payload.get("run_lint", False):
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions),
        "domain": domain_slug,
        **result,
        "actions": actions,
    }


def rebuild_after_concept_change(domains: list[str], payload: dict) -> list[dict]:
    actions: list[dict] = []
    if payload.get("rebuild_domain", True):
        for domain in sorted(set(domain for domain in domains if domain)):
            actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain]))
    if payload.get("rebuild_index", True):
        actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if payload.get("run_lint", False):
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))
    return actions


def merge_concept(payload: dict) -> dict:
    source_slug = clean_text(payload.get("source_slug") or payload.get("slug"))
    target_slug = clean_text(payload.get("target_slug"))
    domain_slug = clean_text(payload.get("domain")) or "general"
    if not source_slug or not target_slug:
        raise ValueError("合并概念需要 source_slug 和 target_slug")
    if slugify(source_slug) == slugify(target_slug):
        raise ValueError("源概念和目标概念不能相同")
    source_path = concept_file_by_slug(source_slug)
    target_path = concept_file_by_slug(target_slug)
    if source_path == target_path:
        raise ValueError("源概念和目标概念不能相同")

    source_meta = parse_frontmatter(source_path)
    target_meta = parse_frontmatter(target_path)
    domains = [
        tag
        for tag in [
            domain_slug,
            *parse_inline_list(source_meta.get("tags")),
            *parse_inline_list(target_meta.get("tags")),
        ]
        if tag and tag != "auto-concept" and tag != "curated-concept"
    ]
    merge_result = merge_concept_pages(
        source_path,
        target_path,
        domain_slug,
        clean_text(payload.get("reason")) or "manual merge",
    )
    actions = rebuild_after_concept_change(domains or [domain_slug], payload)
    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "domain": domain_slug,
        "merge": merge_result,
        "actions": actions,
    }


def restore_concept_archive(payload: dict) -> dict:
    record_id = clean_text(payload.get("archive_id") or payload.get("id"))
    restored = restore_concept_archive_record(record_id)
    domains = restored.get("domains") or [clean_text(payload.get("domain")) or "general"]
    actions = rebuild_after_concept_change(domains, payload)
    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "restored": restored,
        "actions": actions,
    }


def source_ingest_ready(raw_rel: str) -> bool:
    if not raw_rel:
        return False
    try:
        raw_path = raw_path_from_relative(raw_rel)
        source_id = mvp_artifacts.source_id_for_path(raw_path)
        status = mvp_artifacts.read_status(source_id) or {}
    except Exception:
        return False
    artifacts = status.get("artifacts") or {}
    return (
        status.get("status") == "completed"
        and bool(artifacts.get("clean_text"))
        and bool(artifacts.get("source_summary"))
        and bool(artifacts.get("concept_candidates"))
    )


def source_review_reason(body: str, meta: dict[str, str], raw_sources: list[str] | None = None) -> str:
    if raw_sources and any(source_ingest_ready(source) for source in raw_sources):
        return ""
    summary = meta.get("summary", "")
    if "等待补充" in summary or "已登记" in summary:
        return "需要补充摘要或正文"
    if "待补" in body:
        return "需要补充主线关系和核心观点"
    if "暂无可提取摘录" in body:
        return "需要补充可提取摘录"
    return ""


def count_relations_for_domain(domain_slug: str) -> int:
    try:
        return int(concept_graph(domain_slug).get("relation_count", 0))
    except Exception:  # noqa: BLE001
        return 0


def workbench(domain_slug: str | None = None) -> dict:
    domain_slug = domain_slug or "general"
    raw_files = raw_source_files(domain_slug)
    concept_files = concept_files_for_domain(domain_slug)
    relation_count = count_relations_for_domain(domain_slug)
    catalog_by_slug = {item["slug"]: item for item in concept_catalog(domain_slug)}

    source_queue = []
    for path in wiki_source_files():
        meta, body = parse_frontmatter_and_body(path)
        if summary_domain(path, meta) != domain_slug:
            continue
        raw_sources = [
            source for source in parse_inline_list(meta.get("sources"))
            if source.startswith("raw/sources/")
        ]
        reason = source_review_reason(body, meta, raw_sources)
        if not reason:
            continue
        source_queue.append(
            {
                "title": meta.get("title", path.stem).replace("Source - ", ""),
                "reason": reason,
                "summary": meta.get("summary", ""),
                "updated": meta.get("updated") or meta.get("created") or "",
                "path": str(path.relative_to(ROOT)),
                "raw_path": raw_sources[0] if raw_sources else "",
            }
        )

    concept_queue = []
    for path in concept_files:
        meta, body = parse_frontmatter_and_body(path)
        action = concept_organize_action(path, domain_slug, catalog_by_slug)
        if action["action"] == "already_curated":
            continue
        title = meta.get("title") or path.stem
        concept_queue.append(
            {
                "title": title,
                "slug": path.stem,
                "reason": action["reason"],
                "action": action["action"],
                "confidence": action["confidence"],
                "introduced_by": action.get("introduced_by", ""),
                "recommended_action": action["action"],
                "target_slug": action.get("target_slug", ""),
                "target_title": action.get("target_title", ""),
                "evidence_count": action.get("evidence_count", 0),
                "relation_count": action.get("relation_count", 0),
                "evidence_sources": action.get("evidence_sources", []),
                "evidence_preview": action.get("evidence_preview", []),
                "affected_files": action.get("affected_files", []),
                "summary": meta.get("summary", ""),
                "updated": meta.get("updated") or meta.get("created") or "",
                "path": str(path.relative_to(ROOT)),
            }
        )

    recent = recent_sources(6).get("sources", [])
    recent = [item for item in recent if item.get("domain") == domain_slug][:5]

    source_queue.sort(key=lambda item: item.get("updated", ""), reverse=True)
    concept_queue.sort(key=lambda item: item.get("updated", ""), reverse=True)

    return {
        "domain": domain_slug,
        "domain_label": domain_label_for(domain_slug),
        "stats": {
            "raw_sources": len(raw_files),
            "source_summaries": len([item for item in wiki_source_files() if summary_domain(item, parse_frontmatter(item)) == domain_slug]),
            "concepts": len(concept_files),
            "relations": relation_count,
            "source_queue": len(source_queue),
            "concept_queue": len(concept_queue),
        },
        "source_queue": source_queue[:8],
        "concept_queue": concept_queue[:10],
        "recent_sources": recent,
    }


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
                "aliases": parse_inline_list(meta.get("aliases")),
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
        if any(slugify(alias) == safe_slug for alias in parse_inline_list(meta.get("aliases"))):
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

    nodes_by_id: dict[str, dict] = {}
    edges: list[dict] = []
    relation_pattern = re.compile(r"^-\s+`([^`]+)`\s+--(.+?)-->\s+`([^`]+)`(?:\s+\((.+)\))?")

    def add_node(label: str, path: str = "", extra: dict | None = None) -> None:
        if not label:
            return
        node_id = slugify(label)
        existing = nodes_by_id.get(node_id)
        if existing:
            if path and not existing.get("path"):
                existing["path"] = path
            if extra:
                existing.update({key: value for key, value in extra.items() if value})
            return
        nodes_by_id[node_id] = {
            "id": node_id,
            "label": label,
            "path": path,
            **({key: value for key, value in (extra or {}).items() if value}),
        }

    concept_files = concept_files_for_domain(domain_slug)
    for path in concept_files:
        meta = parse_frontmatter(path)
        title = meta.get("title") or path.stem
        raw_source_paths = [
            source for source in parse_inline_list(meta.get("sources"))
            if source.startswith("raw/sources/")
        ]
        add_node(
            title,
            str(path.relative_to(ROOT)),
            {"source_paths": raw_source_paths},
        )
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

    for artifact_dir in sorted(mvp_artifacts.ARTIFACT_ROOT.glob("*")):
        accepted_path = artifact_dir / "accepted_graph.json"
        if not accepted_path.exists():
            continue
        try:
            accepted_graph = json.loads(accepted_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if clean_text(accepted_graph.get("domain")) != domain_slug:
            continue
        source_path = clean_text(accepted_graph.get("source_path"))
        graph_source_id = clean_text(accepted_graph.get("source_id"))
        for item in accepted_graph.get("nodes") or []:
            label = clean_text(item.get("display_name") or item.get("name"))
            item_source_path = clean_text(item.get("source_path")) or source_path
            add_node(
                label,
                clean_text(item.get("path")),
                {
                    "source_id": clean_text(item.get("source_id")) or graph_source_id,
                    "candidate_id": clean_text(item.get("candidate_id")),
                    "node_source": clean_text(item.get("node_source")) or clean_text(item.get("source")),
                    "source_path": item_source_path,
                    "source_paths": [item_source_path] if item_source_path else [],
                },
            )
        for item in accepted_graph.get("edges") or []:
            source = clean_text(item.get("source"))
            target = clean_text(item.get("target"))
            relation = clean_text(item.get("relation")) or "相关"
            if not source or not target:
                continue
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
                    "relation": relation,
                    "target": slugify(target),
                    "target_label": target,
                    "evidence": clean_text(item.get("evidence_quote")),
                    "concept_page": "",
                    "source_path": source_path,
                    "projection": "accepted_graph",
                }
            )

    return {
        "domain": domain_slug,
        "domain_label": domain_label_for(domain_slug),
        "nodes": sorted(nodes_by_id.values(), key=lambda node: node["label"].lower()),
        "edges": edges,
        "relations": edges,
        "concept_count": len(nodes_by_id),
        "relation_count": len(edges),
        "domain_page": str((DOMAIN_PAGES / f"{domain_slug}.md").relative_to(ROOT)),
    }


def concept_page(slug: str, domain_slug: str | None = None) -> dict:
    path = concept_file_by_slug(slug)
    meta, body = parse_frontmatter_and_body(path)
    title = meta.get("title") or path.stem
    domain = domain_slug or next((tag for tag in parse_inline_list(meta.get("tags")) if tag != "auto-concept"), "")
    domain_label = domain_label_for(domain) if domain else ""
    graph = concept_graph(domain) if domain else {"edges": []}
    concept_id = slugify(title)
    related_edges = [
        edge
        for edge in graph.get("edges", [])
        if edge.get("source") == concept_id or edge.get("target") == concept_id
    ]
    aliases = parse_inline_list(meta.get("aliases"))
    for alias in alias_candidates_for(title):
        if alias and alias not in aliases:
            aliases.append(alias)
    return {
        "slug": path.stem,
        "id": concept_id,
        "title": title,
        "lead_definition": concept_lead_definition(title, meta.get("summary") or "", body, domain_label),
        "summary": meta.get("summary") or "",
        "status": meta.get("status") or "",
        "updated": meta.get("updated") or "",
        "tags": parse_inline_list(meta.get("tags")),
        "aliases": aliases,
        "sources": parse_inline_list(meta.get("sources")),
        "path": str(path.relative_to(ROOT)),
        "body": body,
        "domain": domain,
        "domain_label": domain_label,
        "sections": {
            "definition": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Working Definition", 4)],
            "aliases": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Aliases", 12)],
            "source_evidence": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Source-Derived Evidence", 10)],
            "academic_evidence": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Academic Evidence", 10)],
            "relations": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Source-Derived Relations", 12)],
            "open_questions": [strip_markdown_inline(item) for item in markdown_list_items(body, "## Open Questions", 8)],
        },
        "introduced_by": concept_introduction_reason(meta, body),
        "catalog": concept_catalog(domain) if domain else concept_catalog(),
        "related_edges": related_edges,
    }


def concept_markdown_body(title: str, summary: str, body: str = "") -> str:
    cleaned = clean_text(body)
    if cleaned:
        return cleaned.rstrip() + "\n"
    definition = summary or f"{title} 的工作定义待补。"
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Working Definition",
            "",
            f"- {definition}",
            "",
            "## Source-Derived Evidence",
            "",
            "- 待补：暂无来源证据。",
            "",
            "## Source-Derived Relations",
            "",
            "- 待补：暂无稳定关系。",
            "",
            "## Open Questions",
            "",
            "- 待补：这个概念的边界和来源证据需要继续整理。",
            "",
        ]
    )


def create_concept(payload: dict) -> dict:
    title = clean_text(payload.get("title"))
    domain_slug = clean_text(payload.get("domain")) or "general"
    if not title:
        raise ValueError("缺少概念标题")
    slug = slugify(clean_text(payload.get("slug")) or title)
    path = WIKI_CONCEPTS / f"{slug}.md"
    if path.exists():
        raise FileExistsError(f"概念已存在：{path.relative_to(ROOT)}")

    today = dt.date.today().isoformat()
    summary = clean_text(payload.get("summary")) or f"{title} 的概念页。"
    aliases = parse_extra_tags(clean_text(payload.get("aliases")))
    tags = [domain_slug, "curated-concept"]
    content = "\n".join(
        [
            "---",
            f"title: {title}",
            "type: concept",
            "status: active",
            f"created: {today}",
            f"updated: {today}",
            f"summary: {summary}",
            f"tags: {inline_list(tags)}",
            f"aliases: {inline_list(aliases)}",
            "sources: []",
            "---",
            "",
            concept_markdown_body(title, summary, clean_text(payload.get("body"))).rstrip(),
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    actions = rebuild_after_concept_change([domain_slug], payload)
    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "created": str(path.relative_to(ROOT)),
        "slug": path.stem,
        "domain": domain_slug,
        "page": concept_page(path.stem, domain_slug),
        "actions": actions,
    }


def update_concept(payload: dict) -> dict:
    slug = clean_text(payload.get("slug"))
    domain_slug = clean_text(payload.get("domain")) or "general"
    if not slug:
        raise ValueError("缺少 concept slug")
    path = concept_file_by_slug(slug)
    meta, existing_body = parse_frontmatter_and_body(path)
    title = clean_text(payload.get("title")) or meta.get("title") or path.stem
    summary = clean_text(payload.get("summary")) or meta.get("summary") or ""
    aliases = parse_extra_tags(clean_text(payload.get("aliases"))) if "aliases" in payload else parse_inline_list(meta.get("aliases"))
    tags = parse_inline_list(meta.get("tags"))
    if domain_slug and domain_slug not in tags:
        tags.insert(0, domain_slug)
    if "curated-concept" not in tags:
        tags.append("curated-concept")
    body = clean_text(payload.get("body")) if "body" in payload else existing_body

    frontmatter, _ = split_frontmatter(path)
    updates = {
        "title": title,
        "status": clean_text(payload.get("status")) or meta.get("status") or "active",
        "updated": dt.date.today().isoformat(),
        "summary": summary,
        "tags": inline_list(tags),
        "aliases": inline_list(aliases),
    }
    seen = set()
    updated_frontmatter = [frontmatter[0]] if frontmatter else ["---"]
    for line in frontmatter[1:-1]:
        if ":" not in line:
            updated_frontmatter.append(line)
            continue
        key = line.split(":", 1)[0].strip()
        if key in updates:
            updated_frontmatter.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            updated_frontmatter.append(line)
    for key, value in updates.items():
        if key not in seen:
            updated_frontmatter.append(f"{key}: {value}")
    updated_frontmatter.append("---")
    path.write_text("\n".join([*updated_frontmatter, "", concept_markdown_body(title, summary, body).rstrip(), ""]).rstrip() + "\n", encoding="utf-8")
    actions = rebuild_after_concept_change([domain_slug], payload)
    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "updated": str(path.relative_to(ROOT)),
        "slug": path.stem,
        "domain": domain_slug,
        "page": concept_page(path.stem, domain_slug),
        "actions": actions,
    }


def delete_graph_node(payload: dict) -> dict:
    source_id = clean_text(payload.get("source_id"))
    candidate_id = clean_text(payload.get("candidate_id"))
    label = clean_text(payload.get("label"))
    domain_slug = clean_text(payload.get("domain")) or "general"
    if not source_id or not candidate_id:
        if not label:
            raise ValueError("删除图谱节点需要 source_id/candidate_id 或 label")
        cleaned_refs = remove_concept_relation_refs(label)
        actions = rebuild_after_concept_change([domain_slug], payload)
        return {
            "ok": all(action["ok"] for action in actions) if actions else True,
            "domain": domain_slug,
            "label": label,
            "removed_relation_refs": cleaned_refs,
            "actions": actions,
        }
    result = mvp_concept_reviews.update_review(source_id, candidate_id, "reject")
    graph = mvp_concept_reviews.project_accepted_graph(source_id)
    return {
        "ok": True,
        "domain": domain_slug,
        "source_id": source_id,
        "candidate_id": candidate_id,
        "review": result,
        "accepted_graph": graph,
    }


def remove_concept_relation_refs(label: str) -> list[str]:
    removed_from: list[str] = []
    label_slug = slugify(label)
    for path in WIKI_CONCEPTS.glob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        kept: list[str] = []
        changed = False
        for line in lines:
            match = CONCEPT_RELATION_PATTERN.match(line.strip())
            if match:
                source, _, target, _ = match.groups()
                if slugify(source) == label_slug or slugify(target) == label_slug:
                    changed = True
                    continue
            kept.append(line)
        if changed:
            path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")
            removed_from.append(str(path.relative_to(ROOT)))
    return removed_from


def relation_line_with_labels(line: str, old_label: str, new_label: str) -> tuple[str, bool]:
    match = CONCEPT_RELATION_PATTERN.match(line.strip())
    if not match:
        return line, False
    source, relation, target, evidence_raw = match.groups()
    changed = False
    old_slug = slugify(old_label)
    if slugify(source) == old_slug:
        source = new_label
        changed = True
    if slugify(target) == old_slug:
        target = new_label
        changed = True
    if not changed:
        return line, False
    suffix = f" ({evidence_raw})" if evidence_raw else ""
    return f"- `{source}` --{relation.strip()}--> `{target}`{suffix}", True


def update_concept_relation_label(old_label: str, new_label: str) -> list[str]:
    changed_pages: list[str] = []
    for path in WIKI_CONCEPTS.glob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        updated: list[str] = []
        changed = False
        for line in lines:
            rewritten, line_changed = relation_line_with_labels(line, old_label, new_label)
            updated.append(rewritten)
            changed = changed or line_changed
        if changed:
            path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
            changed_pages.append(str(path.relative_to(ROOT)))
    return sorted(set(changed_pages))


def markdown_section_raw_lines(body: str, heading: str) -> list[str]:
    section = markdown_section(body, heading)
    return [line.strip() for line in section.splitlines() if line.strip()]


def merge_markdown_section_lines(body: str, heading: str, additions: list[str]) -> str:
    existing = markdown_section_raw_lines(body, heading)
    merged: list[str] = []
    for line in [*existing, *additions]:
        cleaned = line.strip()
        if cleaned and cleaned not in merged:
            merged.append(cleaned)
    return replace_markdown_section(body, heading, merged or ["- 待补：暂无内容。"])


def merge_concept_pages(source_path: Path, target_path: Path, domain_slug: str, reason: str = "") -> dict:
    source_meta, source_body = parse_frontmatter_and_body(source_path)
    target_meta, target_body = parse_frontmatter_and_body(target_path)
    source_title = source_meta.get("title") or source_path.stem
    target_title = target_meta.get("title") or target_path.stem
    if slugify(source_title) == slugify(target_title):
        raise ValueError("源概念和目标概念相同")

    existing_aliases = parse_inline_list(target_meta.get("aliases"))
    source_aliases = parse_inline_list(source_meta.get("aliases"))
    alias_group = alias_group_for(source_title) or alias_group_for(target_title)
    aliases: list[str] = []
    for item in [*existing_aliases, source_title, *source_aliases, *alias_group]:
        cleaned = clean_text(item)
        if not cleaned or slugify(cleaned) == slugify(target_title):
            continue
        if cleaned not in aliases:
            aliases.append(cleaned)

    target_sources = parse_inline_list(target_meta.get("sources"))
    for item in parse_inline_list(source_meta.get("sources")):
        if item and item not in target_sources:
            target_sources.append(item)

    target_tags = parse_inline_list(target_meta.get("tags"))
    for tag in parse_inline_list(source_meta.get("tags")):
        if tag and tag != "auto-concept" and tag not in target_tags:
            target_tags.append(tag)
    if "curated-concept" not in target_tags:
        target_tags.append("curated-concept")

    target_body = merge_markdown_section_lines(
        target_body,
        "## Aliases",
        [f"- `{alias}`" for alias in aliases],
    )
    target_body = merge_markdown_section_lines(
        target_body,
        "## Source-Derived Evidence",
        markdown_section_raw_lines(source_body, "## Source-Derived Evidence"),
    )
    relation_additions = []
    for line in markdown_section_raw_lines(source_body, "## Source-Derived Relations"):
        rewritten, _ = relation_line_with_labels(line, source_title, target_title)
        relation_additions.append(rewritten)
    target_body = merge_markdown_section_lines(target_body, "## Source-Derived Relations", relation_additions)
    academic_lines = markdown_section_raw_lines(source_body, "## Academic Evidence")
    if academic_lines:
        target_body = merge_markdown_section_lines(target_body, "## Academic Evidence", academic_lines)

    target_body = replace_markdown_section(
        target_body,
        "## Open Questions",
        [
            f"- 已将 `{source_title}` 作为 `{target_title}` 的 alias 合并；后续可继续校正定义边界。",
            "- 后续可继续补充更精确的定义、边界、反例和跨学科连接。",
        ],
    )

    write_frontmatter(
        target_path,
        {
            "updated": dt.date.today().isoformat(),
            "tags": inline_list(target_tags),
            "sources": inline_list(target_sources),
            "aliases": inline_list(aliases),
        },
    )
    frontmatter, _ = split_frontmatter(target_path)
    target_path.write_text("\n".join([*frontmatter, "", target_body]).rstrip() + "\n", encoding="utf-8")

    updated_refs = update_concept_relation_label(source_title, target_title)
    archive = archive_concept_page(
        source_path,
        "merge",
        reason or f"merged into {target_title}",
        {
            "target_path": str(target_path.relative_to(ROOT)),
            "target_title": target_title,
            "aliases_added": aliases,
        },
    )
    return {
        "source": str(source_path.relative_to(ROOT)),
        "target": str(target_path.relative_to(ROOT)),
        "source_title": source_title,
        "target_title": target_title,
        "aliases": aliases,
        "updated_relation_refs": updated_refs,
        "archive": archive,
    }


def delete_concept(payload: dict) -> dict:
    slug = clean_text(payload.get("slug"))
    if not slug:
        raise ValueError("缺少 concept slug")
    path = concept_file_by_slug(slug)
    meta = parse_frontmatter(path)
    label = meta.get("title") or path.stem
    tags = parse_inline_list(meta.get("tags"))
    domains = [tag for tag in tags if tag != "auto-concept"]
    if not domains:
        domains = [clean_text(payload.get("domain")) or "general"]

    archive = archive_concept_page(path, "delete_manual", "deleted from concept reader")
    cleaned_refs = remove_concept_relation_refs(label)
    actions = []
    if payload.get("rebuild_domain", True):
        for domain in domains:
            actions.append(shell_run(["python3", "scripts/rebuild_domain_network.py", "--domain", domain]))
    if payload.get("rebuild_index", True):
        actions.append(shell_run(["python3", "scripts/rebuild_index.py"]))
    if payload.get("run_lint", False):
        actions.append(shell_run(["python3", "scripts/lint_wiki.py"]))

    return {
        "ok": all(action["ok"] for action in actions) if actions else True,
        "deleted": str(path.relative_to(ROOT)),
        "archive": archive,
        "label": label,
        "cleaned_refs": cleaned_refs,
        "actions": actions,
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
        if parsed.path == "/api/sources":
            query = parse_qs(parsed.query)
            domain = clean_text(query.get("domain", [""])[0])
            write_json(self, list_sources(domain or None))
            return
        if parsed.path == "/api/sources/recent":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["12"])[0])
            write_json(self, recent_sources(limit))
            return
        if parsed.path == "/api/workbench":
            query = parse_qs(parsed.query)
            domain = clean_text(query.get("domain", ["general"])[0])
            write_json(self, workbench(domain))
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
        if parsed.path == "/api/concepts/archive/recent":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["12"])[0])
            write_json(self, {"ok": True, "archives": recent_concept_archives(limit)})
            return
        status_match = re.fullmatch(r"/api/sources/([^/]+)/ingest-status", parsed.path)
        if status_match:
            source_id = unquote(status_match.group(1))
            status = mvp_artifacts.read_status(source_id)
            if not status:
                write_json(self, {"ok": False, "error": f"Ingest status not found: {source_id}"}, HTTPStatus.NOT_FOUND)
                return
            write_json(self, {"ok": True, "status": status})
            return
        candidate_match = re.fullmatch(r"/api/sources/([^/]+)/concept-candidates", parsed.path)
        if candidate_match:
            source_id = unquote(candidate_match.group(1))
            try:
                write_json(self, mvp_concept_reviews.merged_candidates(source_id))
            except FileNotFoundError:
                write_json(
                    self,
                    {"ok": False, "error": f"Concept candidates not found: {source_id}"},
                    HTTPStatus.NOT_FOUND,
                )
            return
        accepted_match = re.fullmatch(r"/api/sources/([^/]+)/accepted-concepts", parsed.path)
        if accepted_match:
            source_id = unquote(accepted_match.group(1))
            try:
                write_json(self, mvp_concept_reviews.project_accepted_concepts(source_id))
            except FileNotFoundError:
                write_json(
                    self,
                    {"ok": False, "error": f"Concept candidates not found: {source_id}"},
                    HTTPStatus.NOT_FOUND,
                )
            return
        relation_match = re.fullmatch(r"/api/sources/([^/]+)/relation-candidates", parsed.path)
        if relation_match:
            source_id = unquote(relation_match.group(1))
            try:
                write_json(self, mvp_concept_reviews.merged_relations(source_id))
            except FileNotFoundError:
                write_json(
                    self,
                    {"ok": False, "error": f"Relation candidates not found: {source_id}"},
                    HTTPStatus.NOT_FOUND,
                )
            return
        accepted_graph_match = re.fullmatch(r"/api/sources/([^/]+)/accepted-graph", parsed.path)
        if accepted_graph_match:
            source_id = unquote(accepted_graph_match.group(1))
            try:
                write_json(self, mvp_concept_reviews.project_accepted_graph(source_id))
            except FileNotFoundError:
                write_json(
                    self,
                    {"ok": False, "error": f"Accepted graph inputs not found: {source_id}"},
                    HTTPStatus.NOT_FOUND,
                )
            return
        artifact_match = re.fullmatch(r"/api/sources/([^/]+)/artifacts/([^/]+)", parsed.path)
        if artifact_match:
            source_id = unquote(artifact_match.group(1))
            artifact_type = unquote(artifact_match.group(2))
            try:
                write_json(self, mvp_artifacts.artifact_response(source_id, artifact_type))
            except FileNotFoundError:
                write_json(
                    self,
                    {"ok": False, "error": f"Artifact not found: {source_id}/{artifact_type}"},
                    HTTPStatus.NOT_FOUND,
                )
            except ValueError as exc:
                write_json(self, {"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
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
            if parsed.path == "/api/sources/update":
                write_json(self, update_source(payload))
                return
            if parsed.path == "/api/sources/auto-supplement":
                write_json(self, auto_supplement_source(payload))
                return
            if parsed.path == "/api/sources/delete":
                write_json(self, delete_source(payload))
                return
            if parsed.path == "/api/domains/delete":
                write_json(self, delete_domain(payload))
                return
            if parsed.path == "/api/sciverse/search":
                write_json(self, sciverse_search(payload))
                return
            if parsed.path == "/api/trackers/science":
                write_json(self, science_tracker(payload))
                return
            if parsed.path == "/api/sciverse/import-source":
                write_json(self, sciverse_import_source(payload))
                return
            if parsed.path == "/api/concepts/academic-evidence":
                write_json(self, add_academic_evidence(payload))
                return
            if parsed.path == "/api/concepts/create":
                write_json(self, create_concept(payload))
                return
            if parsed.path == "/api/concepts/update":
                write_json(self, update_concept(payload))
                return
            if parsed.path == "/api/concepts/graph-node/delete":
                write_json(self, delete_graph_node(payload))
                return
            if parsed.path == "/api/concepts/delete":
                write_json(self, delete_concept(payload))
                return
            if parsed.path == "/api/concepts/organize":
                write_json(self, organize_concepts(payload))
                return
            if parsed.path == "/api/concepts/decision":
                write_json(self, concept_decision(payload))
                return
            if parsed.path == "/api/concepts/merge":
                write_json(self, merge_concept(payload))
                return
            if parsed.path == "/api/concepts/restore":
                write_json(self, restore_concept_archive(payload))
                return
            if parsed.path == "/api/batch-automation":
                write_json(
                    self,
                    mvp_batch_automation.batch_automation(
                        domain=clean_text(payload.get("domain")) or None,
                        apply=bool(payload.get("apply")),
                        limit=int(payload.get("limit") or 0) or None,
                        include_completed=bool(payload.get("include_completed")),
                        overwrite=bool(payload.get("overwrite")),
                        project_accepted=payload.get("project_accepted", True) is not False,
                    ),
                )
                return
            reingest_match = re.fullmatch(r"/api/sources/([^/]+)/reingest", parsed.path)
            if reingest_match:
                source_id = unquote(reingest_match.group(1))
                source_path = mvp_artifacts.find_source_path(source_id)
                if not source_path:
                    write_json(self, {"ok": False, "error": f"Source not found for source_id: {source_id}"}, HTTPStatus.NOT_FOUND)
                    return
                result = run_mvp_ingest(str(source_path.relative_to(ROOT)), overwrite=True)
                try:
                    result["accepted_concepts"] = mvp_concept_reviews.project_accepted_concepts(source_id)
                    result["relation_reviews"] = mvp_concept_reviews.merged_relations(source_id)
                    result["accepted_graph"] = mvp_concept_reviews.project_accepted_graph(source_id)
                except FileNotFoundError:
                    pass
                write_json(self, result)
                return
            candidate_action_match = re.fullmatch(
                r"/api/sources/([^/]+)/concept-candidates/([^/]+)/(accept|reject|rename|note)",
                parsed.path,
            )
            if candidate_action_match:
                source_id = unquote(candidate_action_match.group(1))
                candidate_id = unquote(candidate_action_match.group(2))
                action = unquote(candidate_action_match.group(3))
                try:
                    result = mvp_concept_reviews.update_review(
                        source_id,
                        candidate_id,
                        action,
                        display_name=payload.get("display_name"),
                        note=payload.get("note"),
                    )
                    write_json(self, result)
                except FileNotFoundError:
                    write_json(
                        self,
                        {"ok": False, "error": f"Concept candidates not found: {source_id}"},
                        HTTPStatus.NOT_FOUND,
                    )
                except LookupError as exc:
                    write_json(self, {"ok": False, "error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            relation_action_match = re.fullmatch(
                r"/api/sources/([^/]+)/relation-candidates/([^/]+)/(accept|reject|note)",
                parsed.path,
            )
            if relation_action_match:
                source_id = unquote(relation_action_match.group(1))
                relation_id = unquote(relation_action_match.group(2))
                action = unquote(relation_action_match.group(3))
                try:
                    write_json(
                        self,
                        mvp_concept_reviews.update_relation_review(
                            source_id,
                            relation_id,
                            action,
                            note=payload.get("note"),
                        ),
                    )
                except FileNotFoundError:
                    write_json(
                        self,
                        {"ok": False, "error": f"Relation candidates not found: {source_id}"},
                        HTTPStatus.NOT_FOUND,
                    )
                except LookupError as exc:
                    write_json(self, {"ok": False, "error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            if parsed.path == "/api/ingest":
                source_path = clean_text(payload.get("path"))
                if not source_path:
                    raise ValueError("缺少 raw source 路径")
                actions, summary_path, ingest_result = run_mvp_ingest_pipeline(source_path, {**payload, "overwrite_ingest": True})
                write_json(
                    self,
                    {
                        "ok": all(action["ok"] for action in actions),
                        "path": source_path,
                        "summary": summary_path,
                        "ingest_result": ingest_result,
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
