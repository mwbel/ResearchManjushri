#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import mvp_concept_reviews
import mvp_ingest_artifacts as mvp_artifacts
from mvp_ingest_runner import ROOT, RAW_SOURCES, run_mvp_ingest


REQUIRED_ARTIFACTS = ("clean_text", "source_summary", "concept_candidates", "relation_candidates")


def compact(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def raw_source_files(domain: str | None = None) -> list[Path]:
    root = RAW_SOURCES / domain if domain else RAW_SOURCES
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.name.lower() != "readme.md" and not path.name.startswith(".")
    )


def source_domain(path: Path) -> str:
    try:
        return path.relative_to(RAW_SOURCES).parts[0]
    except Exception:
        return "uncategorized"


def has_required_artifacts(source_id: str) -> bool:
    flags = safe_artifact_flags(source_id)
    return all(flags.get(name) for name in REQUIRED_ARTIFACTS)


def safe_artifact_dir(source_id: str) -> Path:
    return mvp_artifacts.ARTIFACT_ROOT / source_id


def safe_artifact_flags(source_id: str) -> dict[str, bool]:
    artifact_dir = safe_artifact_dir(source_id)
    return {
        artifact_type: (artifact_dir / filename).exists()
        for artifact_type, filename in mvp_artifacts.ARTIFACT_FILES.items()
        if artifact_type != "error"
    }


def safe_status(source_id: str) -> dict[str, Any] | None:
    path = safe_artifact_dir(source_id) / "status.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def safe_accepted_projection(source_id: str) -> dict[str, Any] | None:
    path = safe_artifact_dir(source_id) / "accepted_concepts.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def source_snapshot(path: Path) -> dict[str, Any]:
    source_id = mvp_artifacts.source_id_for_path(path)
    status = safe_status(source_id)
    flags = safe_artifact_flags(source_id)
    accepted_projection = safe_accepted_projection(source_id)
    needs_ingest = not has_required_artifacts(source_id)
    needs_projection = bool(flags.get("concept_candidates")) and (
        not flags.get("accepted_concepts") or not flags.get("accepted_graph")
    )
    return {
        "source_id": source_id,
        "source_path": path.relative_to(ROOT).as_posix(),
        "domain": source_domain(path),
        "status": status.get("status") if status else "missing",
        "current_step": status.get("current_step") if status else "",
        "artifacts": flags,
        "accepted_count": int((accepted_projection or {}).get("accepted_count") or 0),
        "needs_ingest": needs_ingest,
        "needs_projection": needs_projection,
    }


def run_backfill_for_source(item: dict[str, Any], *, apply: bool, overwrite: bool) -> dict[str, Any]:
    if not item["needs_ingest"]:
        return {**item, "action": "skip_ingest", "result": None}
    if not apply:
        return {**item, "action": "would_ingest", "result": None}
    result = run_mvp_ingest(item["source_path"], overwrite=overwrite)
    updated = source_snapshot(ROOT / item["source_path"])
    return {**updated, "action": "ingested", "result": result}


def run_projection_for_source(item: dict[str, Any], *, apply: bool) -> dict[str, Any]:
    if not item["artifacts"].get("concept_candidates"):
        return {**item, "projection_action": "skip_missing_candidates", "projection": None}
    if not apply:
        return {**item, "projection_action": "would_project", "projection": None}
    projection = mvp_concept_reviews.project_accepted_concepts(item["source_id"])
    graph = mvp_concept_reviews.project_accepted_graph(item["source_id"])
    updated = source_snapshot(ROOT / item["source_path"])
    return {
        **item,
        **updated,
        "projection_action": "projected",
        "projection": {
            "accepted_count": projection.get("accepted_count", 0),
            "edge_count": graph.get("edge_count", 0),
            "updated_at": projection.get("updated_at"),
        },
    }


def batch_automation(
    *,
    domain: str | None = None,
    apply: bool = False,
    limit: int | None = None,
    include_completed: bool = False,
    overwrite: bool = False,
    project_accepted: bool = True,
) -> dict[str, Any]:
    files = raw_source_files(domain)
    snapshots = [source_snapshot(path) for path in files]
    selected = [
        item
        for item in snapshots
        if include_completed or item["needs_ingest"] or (project_accepted and item["needs_projection"])
    ]
    if limit is not None and limit > 0:
        selected = selected[:limit]

    results: list[dict[str, Any]] = []
    for item in selected:
        next_item = run_backfill_for_source(item, apply=apply, overwrite=overwrite)
        ingest_result = next_item.get("result") or {}
        if project_accepted and (
            next_item["artifacts"].get("concept_candidates")
            or ingest_result.get("status") in {"completed", "review_required"}
        ):
            next_item = run_projection_for_source(next_item, apply=apply)
        results.append(next_item)

    counts = {
        "total_sources": len(snapshots),
        "selected_sources": len(selected),
        "missing_ingest": len([item for item in snapshots if item["needs_ingest"]]),
        "missing_projection": len([item for item in snapshots if item["needs_projection"]]),
        "ingested": len([item for item in results if item.get("action") == "ingested"]),
        "projected": len([item for item in results if item.get("projection_action") == "projected"]),
        "failed": len([item for item in results if item.get("result") and not item["result"].get("ok")]),
    }
    return {
        "ok": counts["failed"] == 0,
        "apply": apply,
        "domain": domain or "",
        "limit": limit,
        "include_completed": include_completed,
        "overwrite": overwrite,
        "project_accepted": project_accepted,
        "counts": counts,
        "items": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill MVP ingest artifacts and accepted concept projections.")
    parser.add_argument("--domain", default="", help="Limit to one raw source domain.")
    parser.add_argument("--apply", action="store_true", help="Write artifacts. Omit for dry-run.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum sources to process.")
    parser.add_argument("--include-completed", action="store_true", help="Include sources that already have artifacts.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MVP wiki source pages during ingest.")
    parser.add_argument("--no-project-accepted", action="store_true", help="Skip accepted_concepts projection.")
    args = parser.parse_args()

    result = batch_automation(
        domain=compact(args.domain) or None,
        apply=args.apply,
        limit=args.limit or None,
        include_completed=args.include_completed,
        overwrite=args.overwrite,
        project_accepted=not args.no_project_accepted,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
