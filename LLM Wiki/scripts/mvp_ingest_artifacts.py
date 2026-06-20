#!/usr/bin/env python3

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from new_source import slugify


ROOT = Path(__file__).resolve().parent.parent
RAW_SOURCES = ROOT / "raw" / "sources"
ARTIFACT_ROOT = ROOT / "data" / "ingest_artifacts"

ARTIFACT_FILES = {
    "raw_text": "raw_text.txt",
    "clean_text": "clean_text.txt",
    "source_summary": "source_summary.json",
    "concept_candidates": "concept_candidates.json",
    "accepted_concepts": "accepted_concepts.json",
    "error": "error.json",
}

STATUS_VALUES = {"pending", "running", "completed", "failed", "review_required"}
STEP_VALUES = {
    "READ_SOURCE",
    "EXTRACT_TEXT",
    "CLEAN_TEXT",
    "SUMMARIZE",
    "EXTRACT_CONCEPTS",
    "WRITE_WIKI_SOURCE",
    "COMPLETED",
    "FAILED",
    "REVIEW_REQUIRED",
}


def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def root_relative(path: Path | str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    return candidate.resolve().relative_to(ROOT).as_posix()


def resolve_source_path(source_path: str | Path) -> Path:
    path = Path(source_path).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if RAW_SOURCES.resolve() not in path.parents:
        raise ValueError(f"source_path must be under {RAW_SOURCES.relative_to(ROOT)}")
    return path


def source_id_for_path(source_path: str | Path) -> str:
    path = resolve_source_path(source_path)
    rel = path.relative_to(ROOT).as_posix()
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:10]
    return f"{slugify(path.stem)}-{digest}"


def find_source_path(source_id: str) -> Path | None:
    if not source_id:
        return None
    for path in sorted(RAW_SOURCES.rglob("*.md")):
        if path.name.lower() == "readme.md" or path.name.startswith("."):
            continue
        try:
            if source_id_for_path(path) == source_id:
                return path
        except Exception:
            continue
    return None


def artifact_dir(source_id: str) -> Path:
    target = ARTIFACT_ROOT / source_id
    target.mkdir(parents=True, exist_ok=True)
    return target


def artifact_path(source_id: str, artifact_type: str) -> Path:
    filename = ARTIFACT_FILES.get(artifact_type)
    if not filename:
        raise ValueError(f"unsupported artifact_type: {artifact_type}")
    return artifact_dir(source_id) / filename


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp.write_text(content, encoding="utf-8")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def artifact_flags(source_id: str) -> dict[str, bool]:
    return {
        "raw_text": artifact_path(source_id, "raw_text").exists(),
        "clean_text": artifact_path(source_id, "clean_text").exists(),
        "source_summary": artifact_path(source_id, "source_summary").exists(),
        "concept_candidates": artifact_path(source_id, "concept_candidates").exists(),
        "accepted_concepts": artifact_path(source_id, "accepted_concepts").exists(),
    }


def artifact_updated_at(source_id: str) -> dict[str, str]:
    updated: dict[str, str] = {}
    for artifact_type in ARTIFACT_FILES:
        path = artifact_path(source_id, artifact_type)
        if path.exists():
            updated[artifact_type] = dt.datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat()
    return updated


def default_status(source_id: str, source_path: str) -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "source_id": source_id,
        "source_path": source_path,
        "status": "pending",
        "current_step": "READ_SOURCE",
        "created_at": timestamp,
        "updated_at": timestamp,
        "error": None,
        "artifacts": artifact_flags(source_id),
        "artifact_updated_at": artifact_updated_at(source_id),
    }


def status_path(source_id: str) -> Path:
    return artifact_dir(source_id) / "status.json"


def read_status(source_id: str) -> dict[str, Any] | None:
    path = status_path(source_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_status(
    source_id: str,
    source_path: str,
    status: str,
    current_step: str,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in STATUS_VALUES:
        raise ValueError(f"unsupported status: {status}")
    if current_step not in STEP_VALUES:
        raise ValueError(f"unsupported current_step: {current_step}")

    existing = read_status(source_id) or default_status(source_id, source_path)
    payload = {
        **existing,
        "source_id": source_id,
        "source_path": source_path,
        "status": status,
        "current_step": current_step,
        "updated_at": now_iso(),
        "error": error,
        "artifacts": artifact_flags(source_id),
        "artifact_updated_at": artifact_updated_at(source_id),
    }
    if extra:
        payload.update(extra)
    atomic_write_json(status_path(source_id), payload)
    return payload


def write_text_artifact(source_id: str, artifact_type: str, content: str) -> Path:
    path = artifact_path(source_id, artifact_type)
    atomic_write_text(path, content)
    return path


def write_json_artifact(source_id: str, artifact_type: str, payload: dict[str, Any]) -> Path:
    path = artifact_path(source_id, artifact_type)
    atomic_write_json(path, payload)
    return path


def read_text_artifact(source_id: str, artifact_type: str) -> str:
    return artifact_path(source_id, artifact_type).read_text(encoding="utf-8")


def read_json_artifact(source_id: str, artifact_type: str) -> dict[str, Any]:
    return json.loads(artifact_path(source_id, artifact_type).read_text(encoding="utf-8"))


def artifact_response(source_id: str, artifact_type: str) -> dict[str, Any]:
    path = artifact_path(source_id, artifact_type)
    if not path.exists():
        raise FileNotFoundError(path)
    updated_at = dt.datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat()
    if path.suffix == ".json":
        return {
            "ok": True,
            "source_id": source_id,
            "artifact_type": artifact_type,
            "path": path.relative_to(ROOT).as_posix(),
            "updated_at": updated_at,
            "content": read_json_artifact(source_id, artifact_type),
        }
    return {
        "ok": True,
        "source_id": source_id,
        "artifact_type": artifact_type,
        "path": path.relative_to(ROOT).as_posix(),
        "updated_at": updated_at,
        "content": read_text_artifact(source_id, artifact_type),
    }
