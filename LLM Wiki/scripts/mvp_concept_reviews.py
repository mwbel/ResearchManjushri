#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mvp_ingest_artifacts as mvp_artifacts


REVIEW_FILENAME = "concept_candidate_reviews.json"
REVIEW_STATUSES = {"pending", "accepted", "rejected", "renamed"}
ACCEPTED_PROJECTION_VERSION = 1


def now_iso() -> str:
    return mvp_artifacts.now_iso()


def review_path(source_id: str) -> Path:
    return mvp_artifacts.ARTIFACT_ROOT / source_id / REVIEW_FILENAME


def compact(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_name(value: object) -> str:
    return compact(value).lower()


def candidate_id_for(index: int, candidate: dict[str, Any]) -> str:
    existing = compact(candidate.get("candidate_id") or candidate.get("id"))
    return existing or f"concept-{index + 1:03d}"


def load_candidate_artifact(source_id: str) -> list[dict[str, Any]]:
    path = mvp_artifacts.ARTIFACT_ROOT / source_id / "concept_candidates.json"
    if not path.exists():
        raise FileNotFoundError(path)
    payload = mvp_artifacts.read_json_artifact(source_id, "concept_candidates")
    candidates = payload.get("concept_candidates") or []
    return [item for item in candidates if isinstance(item, dict)]


def read_review_state(source_id: str) -> dict[str, Any] | None:
    path = review_path(source_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_review_state(source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    mvp_artifacts.atomic_write_json(review_path(source_id), payload)
    return payload


def read_accepted_projection(source_id: str) -> dict[str, Any] | None:
    path = mvp_artifacts.artifact_path(source_id, "accepted_concepts")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def valid_status(value: object) -> str:
    status = compact(value)
    return status if status in REVIEW_STATUSES else "pending"


def normalized_review(review: dict[str, Any]) -> dict[str, Any]:
    original_name = compact(review.get("original_name"))
    display_name = compact(review.get("display_name")) or original_name
    return {
        "candidate_id": compact(review.get("candidate_id")),
        "original_name": original_name,
        "display_name": display_name,
        "status": valid_status(review.get("status")),
        "note": compact(review.get("note")),
        "reviewed_at": review.get("reviewed_at") or None,
        **({"orphan": True} if review.get("orphan") else {}),
    }


def sync_review_state(source_id: str) -> dict[str, Any]:
    candidates = load_candidate_artifact(source_id)
    existing = read_review_state(source_id) or {"source_id": source_id, "updated_at": now_iso(), "reviews": []}
    existing_reviews = [
        normalized_review(review)
        for review in existing.get("reviews", [])
        if isinstance(review, dict)
    ]

    by_id = {review["candidate_id"]: review for review in existing_reviews if review.get("candidate_id")}
    by_name: dict[str, dict[str, Any]] = {}
    for review in existing_reviews:
        for key in (review.get("original_name"), review.get("display_name")):
            normalized = normalize_name(key)
            if normalized:
                by_name.setdefault(normalized, review)

    used_review_ids: set[int] = set()
    next_reviews: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        candidate_id = candidate_id_for(index, candidate)
        name = compact(candidate.get("name")) or candidate_id
        matched = by_id.get(candidate_id) or by_name.get(normalize_name(name))
        if matched:
            used_review_ids.add(id(matched))
            display_name = compact(matched.get("display_name")) or name
            status = valid_status(matched.get("status"))
            note = compact(matched.get("note"))
            reviewed_at = matched.get("reviewed_at") or None
        else:
            display_name = name
            status = "pending"
            note = ""
            reviewed_at = None
        next_reviews.append(
            {
                "candidate_id": candidate_id,
                "original_name": name,
                "display_name": display_name,
                "status": status,
                "note": note,
                "reviewed_at": reviewed_at,
            }
        )

    for review in existing_reviews:
        if id(review) in used_review_ids:
            continue
        if review.get("orphan"):
            orphan = {**review, "orphan": True}
        else:
            orphan = {**review, "orphan": True}
        next_reviews.append(orphan)

    payload = {
        "source_id": source_id,
        "updated_at": existing.get("updated_at") or now_iso(),
        "reviews": next_reviews,
    }
    comparable_existing = {
        "source_id": existing.get("source_id"),
        "reviews": existing_reviews,
    }
    comparable_next = {
        "source_id": payload["source_id"],
        "reviews": next_reviews,
    }
    if comparable_existing != comparable_next:
        payload["updated_at"] = now_iso()
        write_review_state(source_id, payload)
    return payload


def merged_candidates(source_id: str) -> dict[str, Any]:
    candidates = load_candidate_artifact(source_id)
    state = sync_review_state(source_id)
    reviews = {
        review.get("candidate_id"): review
        for review in state.get("reviews", [])
        if isinstance(review, dict) and not review.get("orphan")
    }
    merged: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        candidate_id = candidate_id_for(index, candidate)
        name = compact(candidate.get("name")) or candidate_id
        review = reviews.get(candidate_id) or {
            "candidate_id": candidate_id,
            "original_name": name,
            "display_name": name,
            "status": "pending",
            "note": "",
            "reviewed_at": None,
        }
        merged.append(
            {
                "candidate_id": candidate_id,
                "name": name,
                "display_name": compact(review.get("display_name")) or name,
                "aliases": candidate.get("aliases") or [],
                "type": compact(candidate.get("type")),
                "definition_draft": compact(candidate.get("definition_draft")),
                "evidence_quote": compact(candidate.get("evidence_quote")),
                "confidence": candidate.get("confidence"),
                "status": valid_status(review.get("status")),
                "note": compact(review.get("note")),
                "reviewed_at": review.get("reviewed_at") or None,
            }
        )
    orphan_reviews = [
        review
        for review in state.get("reviews", [])
        if isinstance(review, dict) and review.get("orphan")
    ]
    return {
        "ok": True,
        "source_id": source_id,
        "candidates": merged,
        "orphan_reviews": orphan_reviews,
        "updated_at": state.get("updated_at") or now_iso(),
    }


def projection_review_indexes(source_id: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    existing = read_review_state(source_id) or {"reviews": []}
    reviews = [
        normalized_review(review)
        for review in existing.get("reviews", [])
        if isinstance(review, dict) and not review.get("orphan")
    ]
    by_id = {review["candidate_id"]: review for review in reviews if review.get("candidate_id")}
    by_name: dict[str, dict[str, Any]] = {}
    for review in reviews:
        for key in (review.get("original_name"), review.get("display_name")):
            normalized = normalize_name(key)
            if normalized:
                by_name.setdefault(normalized, review)
    return by_id, by_name


def same_projection(left: dict[str, Any] | None, right: dict[str, Any]) -> bool:
    if not left:
        return False
    ignored = {"updated_at"}
    return (
        {key: value for key, value in left.items() if key not in ignored}
        == {key: value for key, value in right.items() if key not in ignored}
    )


def project_accepted_concepts(source_id: str) -> dict[str, Any]:
    candidates = load_candidate_artifact(source_id)
    reviews_by_id, reviews_by_name = projection_review_indexes(source_id)

    accepted: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        candidate_id = candidate_id_for(index, candidate)
        name = compact(candidate.get("name")) or candidate_id
        review = reviews_by_id.get(candidate_id) or reviews_by_name.get(normalize_name(name))
        if not review or valid_status(review.get("status")) != "accepted":
            continue
        accepted.append(
            {
                "candidate_id": candidate_id,
                "name": name,
                "display_name": compact(review.get("display_name")) or name,
                "aliases": candidate.get("aliases") or [],
                "type": compact(candidate.get("type")),
                "definition_draft": compact(candidate.get("definition_draft")),
                "evidence_quote": compact(candidate.get("evidence_quote")),
                "confidence": candidate.get("confidence"),
                "status": "accepted",
                "note": compact(review.get("note")),
                "reviewed_at": review.get("reviewed_at") or None,
            }
        )

    payload = {
        "ok": True,
        "projection_version": ACCEPTED_PROJECTION_VERSION,
        "source_id": source_id,
        "updated_at": now_iso(),
        "accepted_count": len(accepted),
        "accepted_concepts": accepted,
        "inputs": {
            "concept_candidates": "concept_candidates.json",
            "concept_candidate_reviews": REVIEW_FILENAME,
        },
    }
    existing = read_accepted_projection(source_id)
    if same_projection(existing, payload):
        return existing or payload
    mvp_artifacts.write_json_artifact(source_id, "accepted_concepts", payload)
    return payload


def update_review(
    source_id: str,
    candidate_id: str,
    action: str,
    *,
    display_name: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if action not in {"accept", "reject", "rename", "note"}:
        raise ValueError(f"unsupported review action: {action}")

    state = sync_review_state(source_id)
    reviews = state.get("reviews", [])
    target: dict[str, Any] | None = None
    for review in reviews:
        if isinstance(review, dict) and not review.get("orphan") and compact(review.get("candidate_id")) == candidate_id:
            target = review
            break
    if target is None:
        raise LookupError(f"Concept candidate not found: {candidate_id}")

    timestamp = now_iso()
    if action == "accept":
        target["status"] = "accepted"
        target["reviewed_at"] = timestamp
    elif action == "reject":
        target["status"] = "rejected"
        target["reviewed_at"] = timestamp
    elif action == "rename":
        new_name = compact(display_name)
        if not new_name:
            raise ValueError("display_name is required")
        target["display_name"] = new_name
        target["status"] = "renamed"
        target["reviewed_at"] = timestamp
    elif action == "note":
        target["note"] = compact(note)
        target["reviewed_at"] = timestamp

    state["updated_at"] = timestamp
    write_review_state(source_id, state)
    result = merged_candidates(source_id)
    result["accepted_concepts"] = project_accepted_concepts(source_id)
    return result
