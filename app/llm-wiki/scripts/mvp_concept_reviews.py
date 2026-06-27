#!/usr/bin/env python3

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any

import mvp_ingest_artifacts as mvp_artifacts


REVIEW_FILENAME = "concept_candidate_reviews.json"
RELATION_REVIEW_FILENAME = "relation_candidate_reviews.json"
REVIEW_STATUSES = {"pending", "accepted", "rejected", "renamed"}
RELATION_REVIEW_STATUSES = {"pending", "accepted", "rejected"}
ACCEPTED_PROJECTION_VERSION = 1
ACCEPTED_GRAPH_VERSION = 2
WIKI_CONCEPTS = mvp_artifacts.ROOT / "wiki" / "concepts"


def _parse_frontmatter(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    in_frontmatter = False
    for line in lines:
        value = line.strip()
        if not in_frontmatter:
            if value == "---":
                in_frontmatter = True
            continue
        if value == "---":
            break
        if not value:
            continue
        if ":" not in value:
            continue
        key, raw = value.split(":", 1)
        data[key.strip()] = raw.strip().strip(" \"'")
    return data


def _parse_inline_list(value: str | None) -> list[str]:
    raw = compact(value).strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip() for item in raw.split(",") if item.strip()]


def _normalize_concept_key(value: object) -> str:
    text = compact(value)
    return re.sub(r"\s+", " ", text.lower().replace("：", "").replace("-", "")).strip()


def _load_domain_concept_index(domain_slug: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not WIKI_CONCEPTS.exists():
        return index
    for path in sorted(WIKI_CONCEPTS.glob("*.md")):
        if not path.exists():
            continue
        meta = _parse_frontmatter(path)
        if compact(meta.get("type")) != "concept":
            continue
        tags = _parse_inline_list(meta.get("tags"))
        if domain_slug and domain_slug not in tags:
            continue
        title = compact(meta.get("title")) or path.stem
        aliases: list[str] = []
        aliases.extend(_parse_inline_list(meta.get("aliases")))
        aliases.append(title)
        for alias in aliases:
            key = _normalize_concept_key(alias)
            if not key:
                continue
            index.setdefault(
                key,
                {
                    "label": title,
                    "slug": path.stem,
                    "path": str(path.relative_to(mvp_artifacts.ROOT)),
                },
            )
    return index


def _best_existing_match(
    label: str,
    concept_index: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    key = _normalize_concept_key(label)
    if not key:
        return None
    direct = concept_index.get(key)
    if direct:
        return direct

    best = None
    best_score = 0
    for candidate_key, candidate in concept_index.items():
        if not candidate_key or candidate_key == key:
            continue
        if key in candidate_key or candidate_key in key:
            score = min(len(key), len(candidate_key))
            if abs(len(key) - len(candidate_key)) <= 8 and score > best_score:
                best_score = score
                best = candidate
    return best


def now_iso() -> str:
    return mvp_artifacts.now_iso()


def review_path(source_id: str) -> Path:
    return mvp_artifacts.ARTIFACT_ROOT / source_id / REVIEW_FILENAME


def relation_review_path(source_id: str) -> Path:
    return mvp_artifacts.ARTIFACT_ROOT / source_id / RELATION_REVIEW_FILENAME


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


def load_relation_artifact(source_id: str) -> list[dict[str, Any]]:
    path = mvp_artifacts.ARTIFACT_ROOT / source_id / "relation_candidates.json"
    if not path.exists():
        raise FileNotFoundError(path)
    payload = mvp_artifacts.read_json_artifact(source_id, "relation_candidates")
    relations = payload.get("relation_candidates") or []
    return [item for item in relations if isinstance(item, dict)]


def read_review_state(source_id: str) -> dict[str, Any] | None:
    path = review_path(source_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_review_state(source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    mvp_artifacts.atomic_write_json(review_path(source_id), payload)
    return payload


def read_relation_review_state(source_id: str) -> dict[str, Any] | None:
    path = relation_review_path(source_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_relation_review_state(source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    mvp_artifacts.atomic_write_json(relation_review_path(source_id), payload)
    return payload


def read_accepted_projection(source_id: str) -> dict[str, Any] | None:
    path = mvp_artifacts.artifact_path(source_id, "accepted_concepts")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_accepted_graph(source_id: str) -> dict[str, Any] | None:
    path = mvp_artifacts.artifact_path(source_id, "accepted_graph")
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


def relation_id_for(index: int, relation: dict[str, Any]) -> str:
    existing = compact(relation.get("relation_id") or relation.get("id"))
    return existing or f"relation-{index + 1:03d}"


def relation_key(relation: dict[str, Any]) -> str:
    return "::".join(
        [
            normalize_name(relation.get("source_name") or relation.get("source_candidate_id")),
            normalize_name(relation.get("relation")),
            normalize_name(relation.get("target_name") or relation.get("target_candidate_id")),
        ]
    )


def sync_relation_review_state(source_id: str) -> dict[str, Any]:
    relations = load_relation_artifact(source_id)
    existing = read_relation_review_state(source_id) or {
        "source_id": source_id,
        "updated_at": now_iso(),
        "reviews": [],
    }
    existing_reviews = [
        review for review in existing.get("reviews", [])
        if isinstance(review, dict)
    ]
    by_id = {
        compact(review.get("relation_id")): review
        for review in existing_reviews
        if compact(review.get("relation_id"))
    }
    by_key = {
        compact(review.get("relation_key")): review
        for review in existing_reviews
        if compact(review.get("relation_key"))
    }
    next_reviews: list[dict[str, Any]] = []
    for index, relation in enumerate(relations):
        relation_id = relation_id_for(index, relation)
        key = relation_key(relation)
        matched = by_key.get(key) or by_id.get(relation_id) or {}
        status = compact(matched.get("status"))
        if status not in RELATION_REVIEW_STATUSES:
            status = "pending"
        next_reviews.append(
            {
                "relation_id": relation_id,
                "relation_key": key,
                "status": status,
                "note": compact(matched.get("note")),
                "reviewed_at": matched.get("reviewed_at") or None,
            }
        )
    payload = {
        "source_id": source_id,
        "updated_at": existing.get("updated_at") or now_iso(),
        "reviews": next_reviews,
    }
    if existing_reviews != next_reviews:
        payload["updated_at"] = now_iso()
        write_relation_review_state(source_id, payload)
    return payload


def merged_relations(source_id: str) -> dict[str, Any]:
    relations = load_relation_artifact(source_id)
    state = sync_relation_review_state(source_id)
    reviews = {
        compact(review.get("relation_id")): review
        for review in state.get("reviews", [])
        if isinstance(review, dict)
    }
    merged: list[dict[str, Any]] = []
    for index, relation in enumerate(relations):
        relation_id = relation_id_for(index, relation)
        review = reviews.get(relation_id) or {}
        merged.append(
            {
                **relation,
                "relation_id": relation_id,
                "status": review.get("status") or "pending",
                "note": compact(review.get("note")),
                "reviewed_at": review.get("reviewed_at") or None,
            }
        )
    return {
        "ok": True,
        "source_id": source_id,
        "relations": merged,
        "updated_at": state.get("updated_at") or now_iso(),
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


def project_accepted_graph(source_id: str) -> dict[str, Any]:
    accepted_payload = project_accepted_concepts(source_id)
    accepted = accepted_payload.get("accepted_concepts") or []
    accepted_labels = [compact(item.get("display_name") or item.get("name")) for item in accepted]
    accepted_by_id = {
        compact(item.get("candidate_id")): item
        for item in accepted
        if compact(item.get("candidate_id"))
    }
    accepted_by_label = {
        _normalize_concept_key(item.get("display_name") or item.get("name")): item
        for item in accepted
        if compact(item.get("display_name") or item.get("name"))
    }
    relation_payload = merged_relations(source_id)
    edges: list[dict[str, Any]] = []
    relation_edge_ids: set[str] = set()
    for relation in relation_payload.get("relations") or []:
        if relation.get("status") != "accepted":
            continue
        source_id_ref = compact(relation.get("source_candidate_id"))
        target_id_ref = compact(relation.get("target_candidate_id"))
        if source_id_ref not in accepted_by_id or target_id_ref not in accepted_by_id:
            continue
        source = accepted_by_id[source_id_ref]
        target = accepted_by_id[target_id_ref]
        edges.append(
            {
                "relation_id": relation.get("relation_id"),
                "source_candidate_id": source_id_ref,
                "source": compact(source.get("display_name") or source.get("name")),
                "relation": compact(relation.get("relation")) or "相关",
                "target_candidate_id": target_id_ref,
                "target": compact(target.get("display_name") or target.get("name")),
                "evidence_quote": compact(relation.get("evidence_quote")),
                "confidence": relation.get("confidence"),
                "status": "accepted",
                "note": compact(relation.get("note")),
                "reviewed_at": relation.get("reviewed_at") or None,
            }
        )
        relation_edge_ids.add(
            f"{_normalize_concept_key(source.get('display_name') or source.get('name'))}::{compact(relation.get('relation'))}::{_normalize_concept_key(target.get('display_name') or target.get('name'))}"
        )
    status = mvp_artifacts.read_status(source_id) or {}
    source_path = compact(status.get("source_path"))
    source_parts = Path(source_path).parts
    domain = source_parts[2] if len(source_parts) > 2 and source_parts[:2] == ("raw", "sources") else ""

    existing_index = _load_domain_concept_index(domain)
    auto_nodes: dict[str, dict[str, Any]] = {}
    for accepted_item in accepted:
        label = compact(accepted_item.get("display_name") or accepted_item.get("name"))
        if not label:
            continue
        candidate = accepted_by_label.get(_normalize_concept_key(label))
        if not candidate:
            continue
        match = _best_existing_match(label, existing_index)
        if not match:
            continue
        target_label = compact(match.get("label"))
        if not target_label:
            continue
        if _normalize_concept_key(label) == _normalize_concept_key(target_label):
            continue
        edge_key = f"{_normalize_concept_key(label)}::映射到::{_normalize_concept_key(target_label)}"
        if edge_key in relation_edge_ids:
            continue
        relation_edge_ids.add(edge_key)
        edges.append(
            {
                "relation_id": f"auto-existing-{len(edges) + 1:03d}",
                "source_candidate_id": compact(candidate.get("candidate_id")),
                "source": label,
                "relation": "映射到",
                "target_candidate_id": f"existing::{compact(match.get('slug'))}",
                "target": target_label,
                "evidence_quote": f"与既有概念“{target_label}”名称一致。",
                "confidence": 0.86,
                "status": "auto",
                "note": "基于名称归一化匹配自动建立。",
                "reviewed_at": now_iso(),
                "target_path": compact(match.get("path")),
            }
        )
        auto_nodes[compact(match.get("slug"))] = {
            "name": target_label,
            "display_name": target_label,
            "path": compact(match.get("path")),
            "source": "wiki_concept",
            "slug": compact(match.get("slug")),
            "link_type": "existing_concept",
        }

    merged_nodes = [
        *(
            {
                **node,
                "source_id": source_id,
                "node_source": "accepted_concept",
            }
            for node in accepted
        ),
        *(
            node for node in auto_nodes.values()
            if compact(node.get("name"))
        ),
    ]
    payload = {
        "ok": True,
        "projection_version": ACCEPTED_GRAPH_VERSION,
        "source_id": source_id,
        "source_path": source_path,
        "domain": domain,
        "updated_at": now_iso(),
        "node_count": len(merged_nodes),
        "edge_count": len(edges),
        "nodes": merged_nodes,
        "edges": edges,
        "inputs": {
            "accepted_concepts": "accepted_concepts.json",
            "relation_candidates": "relation_candidates.json",
            "relation_candidate_reviews": RELATION_REVIEW_FILENAME,
            "concepts_catalog": "wiki/concepts",
        },
    }
    existing = read_accepted_graph(source_id)
    if same_projection(existing, payload):
        return existing or payload
    mvp_artifacts.write_json_artifact(source_id, "accepted_graph", payload)
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
    try:
        result["accepted_graph"] = project_accepted_graph(source_id)
    except FileNotFoundError:
        pass
    return result


def update_relation_review(
    source_id: str,
    relation_id: str,
    action: str,
    *,
    note: str | None = None,
) -> dict[str, Any]:
    if action not in {"accept", "reject", "note"}:
        raise ValueError(f"unsupported relation review action: {action}")
    state = sync_relation_review_state(source_id)
    target = next(
        (
            review for review in state.get("reviews", [])
            if isinstance(review, dict) and compact(review.get("relation_id")) == relation_id
        ),
        None,
    )
    if target is None:
        raise LookupError(f"Relation candidate not found: {relation_id}")
    timestamp = now_iso()
    if action == "accept":
        target["status"] = "accepted"
    elif action == "reject":
        target["status"] = "rejected"
    else:
        target["note"] = compact(note)
    target["reviewed_at"] = timestamp
    state["updated_at"] = timestamp
    write_relation_review_state(source_id, state)
    result = merged_relations(source_id)
    result["accepted_graph"] = project_accepted_graph(source_id)
    return result
