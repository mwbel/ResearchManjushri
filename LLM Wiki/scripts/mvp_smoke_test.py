#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
WIKI_CONCEPTS = ROOT / "wiki" / "concepts"
ARTIFACT_ROOT = ROOT / "data" / "ingest_artifacts"
EXPECTED_ARTIFACTS = {
    "raw_text": "raw_text.txt",
    "clean_text": "clean_text.txt",
    "source_summary": "source_summary.json",
    "concept_candidates": "concept_candidates.json",
    "relation_candidates": "relation_candidates.json",
}
REVIEW_FILENAME = "concept_candidate_reviews.json"
ACCEPTED_FILENAME = "accepted_concepts.json"


class SmokeFailure(AssertionError):
    pass


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def concept_count() -> int:
    if not WIKI_CONCEPTS.exists():
        return 0
    return len([path for path in WIKI_CONCEPTS.glob("*.md") if path.is_file()])


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any], str]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            content_type = response.headers.get("content-type", "")
            return response.status, json.loads(raw or "{}"), content_type
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        content_type = exc.headers.get("content-type", "")
        try:
            payload_json = json.loads(raw or "{}")
        except json.JSONDecodeError as error:
            raise SmokeFailure(f"{method} {path} returned non-JSON error body: {raw[:200]}") from error
        return exc.code, payload_json, content_type


def wait_for_server(base_url: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status, payload, _ = request_json(base_url, "GET", "/api/health")
            if status == 200 and payload.get("ok"):
                return
        except Exception:
            time.sleep(0.2)
    raise SmokeFailure(f"Web service did not become ready: {base_url}")


def start_server(host: str, port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "scripts/wiki_web.py", "--host", host, "--port", str(port)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def create_source_payload(title: str, original_content: str, context: str, notes: str) -> dict[str, Any]:
    return {
        "title": title,
        "domain": "ai智能体",
        "kind": "note",
        "date": dt.date.today().isoformat(),
        "status": "inbox",
        "source_type": "note",
        "source_url": "",
        "local_path": "",
        "author": "mvp-smoke-test",
        "published": "",
        "tags": "mvp-smoke",
        "context": context,
        "original_content": original_content,
        "notes": notes,
        "auto_ingest": True,
        "concept_network": True,
        "rebuild_domain": False,
        "rebuild_index": False,
        "run_lint": False,
    }


def remove_path(path: str | None) -> None:
    if not path:
        return
    target = (ROOT / path).resolve()
    try:
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    except FileNotFoundError:
        return


def artifact_dir_for(source_id: str) -> Path:
    return ARTIFACT_ROOT / source_id


def quote_path_segment(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def candidate_review_path(source_id: str) -> Path:
    return artifact_dir_for(source_id) / REVIEW_FILENAME


def accepted_concepts_path(source_id: str) -> Path:
    return artifact_dir_for(source_id) / ACCEPTED_FILENAME


def get_candidate_reviews(base_url: str, source_id: str) -> dict[str, Any]:
    status, payload, content_type = request_json(
        base_url,
        "GET",
        f"/api/sources/{quote_path_segment(source_id)}/concept-candidates",
    )
    assert_true(status == 200, f"concept-candidates API failed: {status} {payload}")
    assert_true(content_type.startswith("application/json"), f"concept-candidates content-type not JSON: {content_type}")
    assert_true(payload.get("ok") is True, f"concept-candidates response not ok: {payload}")
    return payload


def get_accepted_concepts(base_url: str, source_id: str) -> dict[str, Any]:
    status, payload, content_type = request_json(
        base_url,
        "GET",
        f"/api/sources/{quote_path_segment(source_id)}/accepted-concepts",
    )
    assert_true(status == 200, f"accepted-concepts API failed: {status} {payload}")
    assert_true(content_type.startswith("application/json"), f"accepted-concepts content-type not JSON: {content_type}")
    assert_true(payload.get("ok") is True, f"accepted-concepts response not ok: {payload}")
    return payload


def get_relation_candidates(base_url: str, source_id: str) -> dict[str, Any]:
    status, payload, content_type = request_json(
        base_url,
        "GET",
        f"/api/sources/{quote_path_segment(source_id)}/relation-candidates",
    )
    assert_true(status == 200, f"relation-candidates API failed: {status} {payload}")
    assert_true(content_type.startswith("application/json"), f"relation-candidates content-type not JSON: {content_type}")
    assert_true(payload.get("ok") is True, f"relation-candidates response not ok: {payload}")
    return payload


def get_accepted_graph(base_url: str, source_id: str) -> dict[str, Any]:
    status, payload, content_type = request_json(
        base_url,
        "GET",
        f"/api/sources/{quote_path_segment(source_id)}/accepted-graph",
    )
    assert_true(status == 200, f"accepted-graph API failed: {status} {payload}")
    assert_true(content_type.startswith("application/json"), f"accepted-graph content-type not JSON: {content_type}")
    assert_true(payload.get("ok") is True, f"accepted-graph response not ok: {payload}")
    return payload


def post_candidate_action(
    base_url: str,
    source_id: str,
    candidate_id: str,
    action: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status, response, content_type = request_json(
        base_url,
        "POST",
        f"/api/sources/{quote_path_segment(source_id)}/concept-candidates/{quote_path_segment(candidate_id)}/{action}",
        payload or {},
    )
    assert_true(status == 200, f"{action} candidate failed: {status} {response}")
    assert_true(content_type.startswith("application/json"), f"{action} content-type not JSON: {content_type}")
    assert_true(response.get("ok") is True, f"{action} response not ok: {response}")
    return response


def post_relation_action(
    base_url: str,
    source_id: str,
    relation_id: str,
    action: str,
) -> dict[str, Any]:
    status, response, content_type = request_json(
        base_url,
        "POST",
        f"/api/sources/{quote_path_segment(source_id)}/relation-candidates/{quote_path_segment(relation_id)}/{action}",
        {},
    )
    assert_true(status == 200, f"{action} relation failed: {status} {response}")
    assert_true(content_type.startswith("application/json"), f"{action} relation content-type not JSON: {content_type}")
    assert_true(response.get("ok") is True, f"{action} relation response not ok: {response}")
    return response


def candidate_by_id(payload: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    for candidate in payload.get("candidates") or []:
        if candidate.get("candidate_id") == candidate_id:
            return candidate
    raise SmokeFailure(f"candidate not found in response: {candidate_id}")


def accepted_ids(payload: dict[str, Any]) -> list[str]:
    return [
        item.get("candidate_id")
        for item in payload.get("accepted_concepts") or []
        if item.get("candidate_id")
    ]


def post_batch_automation(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    status, response, content_type = request_json(base_url, "POST", "/api/batch-automation", payload)
    assert_true(status == 200, f"batch automation failed: {status} {response}")
    assert_true(content_type.startswith("application/json"), f"batch automation content-type not JSON: {content_type}")
    assert_true("counts" in response and "items" in response, f"batch automation response malformed: {response}")
    return response


def run_smoke(base_url: str) -> dict[str, Any]:
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    created_paths: list[str] = []
    source_ids: list[str] = []
    normal_wiki_source = ""
    before_count = concept_count()
    result: dict[str, Any] = {"before_concept_count": before_count}

    try:
        normal_title = f"MVP Smoke 普通资料 {stamp}"
        normal_payload = create_source_payload(
            normal_title,
            (
                "Transformer 是一种以注意力机制为核心的模型架构。"
                "注意力机制帮助模型在不同上下文之间分配权重。"
                "大语言模型、AI Agent、人工智能系统和世界模型都依赖清晰的知识表示。"
                "这个资料用于验证自动摘要、候选概念、人工审核状态和 artifact 查看功能。"
            ),
            "mvp_smoke_test 自动创建的普通资料，用于验证 MVP ingest 闭环。",
            "应生成 completed 状态和可读 source card。",
        )
        status, normal_response, _ = request_json(base_url, "POST", "/api/sources", normal_payload)
        assert_true(status == 200, f"normal source create failed: HTTP {status} {normal_response}")
        assert_true(normal_response.get("ok") is True, f"normal source response not ok: {normal_response}")
        ingest_result = normal_response.get("ingest_result") or {}
        assert_true(bool(ingest_result), "normal response missing ingest_result")
        assert_true(ingest_result.get("status") == "completed", f"expected completed, got {ingest_result}")
        assert_true(ingest_result.get("current_step") == "COMPLETED", f"expected COMPLETED step, got {ingest_result}")
        source_id = ingest_result["source_id"]
        source_id_url = urllib.parse.quote(source_id, safe="")
        source_ids.append(source_id)
        created_paths.append(normal_response.get("path", ""))
        normal_wiki_source = ingest_result.get("wiki_source_path") or ""
        created_paths.append(normal_wiki_source)

        artifact_dir = artifact_dir_for(source_id)
        assert_true(artifact_dir.exists(), f"artifact dir missing: {artifact_dir}")
        for artifact_type, filename in EXPECTED_ARTIFACTS.items():
            artifact_path = artifact_dir / filename
            assert_true(artifact_path.exists(), f"artifact file missing: {artifact_path}")
            api_status, artifact_response, content_type = request_json(
                base_url,
                "GET",
                f"/api/sources/{source_id_url}/artifacts/{artifact_type}",
            )
            assert_true(api_status == 200, f"artifact API failed for {artifact_type}: {api_status} {artifact_response}")
            assert_true(content_type.startswith("application/json"), f"artifact API content-type not JSON: {content_type}")
            assert_true("updated_at" in artifact_response, f"artifact API missing updated_at for {artifact_type}")
            assert_true("content" in artifact_response, f"artifact API missing content for {artifact_type}")

        missing_status, missing_payload, missing_type = request_json(
            base_url,
            "GET",
            f"/api/sources/{source_id_url}/artifacts/error",
        )
        assert_true(missing_status == 404, f"missing artifact should return 404, got {missing_status}")
        assert_true(missing_type.startswith("application/json"), f"missing artifact content-type not JSON: {missing_type}")
        assert_true(missing_payload.get("ok") is False and missing_payload.get("error"), f"missing artifact JSON malformed: {missing_payload}")

        review_payload = get_candidate_reviews(base_url, source_id)
        candidates = review_payload.get("candidates") or []
        assert_true(len(candidates) >= 3, f"expected at least 3 concept candidates, got {len(candidates)}")
        assert_true(candidate_review_path(source_id).exists(), "concept_candidate_reviews.json was not initialized")
        for candidate in candidates:
            assert_true(candidate.get("status") == "pending", f"default candidate status should be pending: {candidate}")

        first_id = candidates[0]["candidate_id"]
        second_id = candidates[1]["candidate_id"]
        third_id = candidates[2]["candidate_id"]
        renamed_display_name = f"MVP Smoke 改名概念 {stamp}"

        initial_accepted = get_accepted_concepts(base_url, source_id)
        assert_true(accepted_concepts_path(source_id).exists(), "accepted_concepts.json was not initialized")
        assert_true(
            accepted_ids(initial_accepted) == [],
            f"initial accepted projection should be empty: {initial_accepted}",
        )

        accepted_payload = post_candidate_action(base_url, source_id, first_id, "accept")
        assert_true(candidate_by_id(accepted_payload, first_id).get("status") == "accepted", "accepted candidate status not persisted")
        accepted_projection = accepted_payload.get("accepted_concepts") or {}
        assert_true(
            accepted_ids(accepted_projection) == [first_id],
            f"accepted projection should contain only first candidate: {accepted_projection}",
        )
        rejected_payload = post_candidate_action(base_url, source_id, second_id, "reject")
        assert_true(candidate_by_id(rejected_payload, second_id).get("status") == "rejected", "rejected candidate status not persisted")
        renamed_payload = post_candidate_action(
            base_url,
            source_id,
            third_id,
            "rename",
            {"display_name": renamed_display_name},
        )
        renamed_candidate = candidate_by_id(renamed_payload, third_id)
        assert_true(renamed_candidate.get("status") == "renamed", "renamed candidate status not persisted")
        assert_true(
            renamed_candidate.get("display_name") == renamed_display_name,
            f"renamed display_name not persisted: {renamed_candidate}",
        )
        accepted_after_all_reviews = get_accepted_concepts(base_url, source_id)
        assert_true(
            accepted_ids(accepted_after_all_reviews) == [first_id],
            f"rejected and renamed candidates must not enter accepted projection: {accepted_after_all_reviews}",
        )
        accepted_artifact_status, accepted_artifact_response, accepted_artifact_type = request_json(
            base_url,
            "GET",
            f"/api/sources/{source_id_url}/artifacts/accepted_concepts",
        )
        assert_true(
            accepted_artifact_status == 200,
            f"accepted_concepts artifact API failed: {accepted_artifact_status} {accepted_artifact_response}",
        )
        assert_true(
            accepted_artifact_type.startswith("application/json"),
            f"accepted_concepts artifact content-type not JSON: {accepted_artifact_type}",
        )
        assert_true(
            accepted_ids(accepted_artifact_response.get("content") or {}) == [first_id],
            f"accepted_concepts artifact content malformed: {accepted_artifact_response}",
        )

        bad_candidate_status, bad_candidate_payload, bad_candidate_type = request_json(
            base_url,
            "POST",
            f"/api/sources/{source_id_url}/concept-candidates/{quote_path_segment('missing-candidate')}/accept",
            {},
        )
        assert_true(bad_candidate_status == 404, f"missing candidate should return 404, got {bad_candidate_status}")
        assert_true(bad_candidate_type.startswith("application/json"), f"missing candidate content-type not JSON: {bad_candidate_type}")
        assert_true(
            bad_candidate_payload.get("ok") is False and bad_candidate_payload.get("error"),
            f"missing candidate JSON malformed: {bad_candidate_payload}",
        )

        status_before, status_payload_before, _ = request_json(base_url, "GET", f"/api/sources/{source_id_url}/ingest-status")
        assert_true(status_before == 200, f"status API failed before reingest: {status_payload_before}")
        updated_before = status_payload_before["status"]["updated_at"]
        time.sleep(1.1)
        reingest_status, reingest_payload, reingest_type = request_json(
            base_url,
            "POST",
            f"/api/sources/{source_id_url}/reingest",
            {},
        )
        assert_true(reingest_status == 200, f"reingest failed: {reingest_status} {reingest_payload}")
        assert_true(reingest_type.startswith("application/json"), f"reingest content-type not JSON: {reingest_type}")
        assert_true(reingest_payload.get("ok") is True, f"reingest returned non-ok JSON: {reingest_payload}")
        status_after, status_payload_after, _ = request_json(base_url, "GET", f"/api/sources/{source_id_url}/ingest-status")
        assert_true(status_after == 200, f"status API failed after reingest: {status_payload_after}")
        updated_after = status_payload_after["status"]["updated_at"]
        assert_true(updated_after != updated_before, "status.json updated_at did not change after reingest")
        review_after_reingest = get_candidate_reviews(base_url, source_id)
        assert_true(
            candidate_by_id(review_after_reingest, first_id).get("status") == "accepted",
            "accepted status was not preserved after reingest",
        )
        assert_true(
            candidate_by_id(review_after_reingest, second_id).get("status") == "rejected",
            "rejected status was not preserved after reingest",
        )
        third_after_reingest = candidate_by_id(review_after_reingest, third_id)
        assert_true(third_after_reingest.get("status") == "renamed", "renamed status was not preserved after reingest")
        assert_true(
            third_after_reingest.get("display_name") == renamed_display_name,
            "renamed display_name was not preserved after reingest",
        )
        accepted_after_reingest = get_accepted_concepts(base_url, source_id)
        assert_true(
            accepted_ids(accepted_after_reingest) == [first_id],
            f"accepted projection was not preserved after reingest: {accepted_after_reingest}",
        )

        relation_payload = get_relation_candidates(base_url, source_id)
        relations = relation_payload.get("relations") or []
        assert_true(relations, f"expected at least one relation candidate: {relation_payload}")
        relation = relations[0]
        source_candidate_id = relation["source_candidate_id"]
        target_candidate_id = relation["target_candidate_id"]
        post_candidate_action(base_url, source_id, source_candidate_id, "accept")
        post_candidate_action(base_url, source_id, target_candidate_id, "accept")
        relation_result = post_relation_action(
            base_url,
            source_id,
            relation["relation_id"],
            "accept",
        )
        accepted_graph = relation_result.get("accepted_graph") or get_accepted_graph(base_url, source_id)
        assert_true(accepted_graph.get("edge_count") == 1, f"accepted graph should contain one edge: {accepted_graph}")
        assert_true(
            accepted_graph["edges"][0]["relation_id"] == relation["relation_id"],
            f"accepted graph relation mismatch: {accepted_graph}",
        )

        batch_domain = f"mvp-batch-{stamp}"
        batch_title = f"MVP Smoke 批量资料 {stamp}"
        batch_payload = create_source_payload(
            batch_title,
            (
                "批量自动化资料用于验证旧资料补跑。"
                "Transformer、注意力机制和大语言模型用于生成候选概念。"
            ),
            "mvp_smoke_test 自动创建的批量资料，用于验证 batch automation。",
            "应由 batch automation 补跑 ingest artifacts。",
        )
        batch_payload.update(
            {
                "domain": batch_domain,
                "auto_ingest": False,
                "concept_network": False,
                "rebuild_domain": False,
                "rebuild_index": False,
            }
        )
        batch_status, batch_response, _ = request_json(base_url, "POST", "/api/sources", batch_payload)
        assert_true(batch_status == 200, f"batch source create failed: HTTP {batch_status} {batch_response}")
        assert_true(batch_response.get("ok") is True, f"batch source response not ok: {batch_response}")
        batch_source_path = batch_response.get("path")
        created_paths.append(batch_source_path)

        batch_dry_run = post_batch_automation(
            base_url,
            {
                "domain": batch_domain,
                "apply": False,
                "project_accepted": True,
            },
        )
        assert_true(batch_dry_run["counts"]["selected_sources"] == 1, f"batch dry-run should select one source: {batch_dry_run}")
        assert_true(batch_dry_run["items"][0]["action"] == "would_ingest", f"batch dry-run action mismatch: {batch_dry_run}")

        batch_apply = post_batch_automation(
            base_url,
            {
                "domain": batch_domain,
                "apply": True,
                "project_accepted": True,
            },
        )
        assert_true(batch_apply["counts"]["ingested"] == 1, f"batch apply should ingest one source: {batch_apply}")
        batch_item = batch_apply["items"][0]
        batch_source_id = batch_item["source_id"]
        source_ids.append(batch_source_id)
        assert_true(artifact_dir_for(batch_source_id).exists(), f"batch artifact dir missing: {batch_source_id}")
        assert_true((artifact_dir_for(batch_source_id) / "concept_candidates.json").exists(), "batch concept candidates missing")
        assert_true((artifact_dir_for(batch_source_id) / "accepted_concepts.json").exists(), "batch accepted projection missing")
        batch_wiki_source = (batch_item.get("result") or {}).get("wiki_source_path") or ""
        created_paths.append(batch_wiki_source)

        blocked_title = f"MVP Smoke 微信风控 {stamp}"
        blocked_payload = create_source_payload(
            blocked_title,
            "当前环境存在异常，请完成验证后即可继续访问。请在微信客户端打开。访问频率过高。",
            "mvp_smoke_test 自动创建的微信风控资料。",
            "应进入 review_required，并生成 error.json。",
        )
        blocked_status, blocked_response, _ = request_json(base_url, "POST", "/api/sources", blocked_payload)
        assert_true(blocked_status == 200, f"blocked source create failed: HTTP {blocked_status} {blocked_response}")
        blocked_ingest = blocked_response.get("ingest_result") or {}
        assert_true(blocked_ingest.get("status") == "review_required", f"expected review_required, got {blocked_ingest}")
        assert_true(not blocked_ingest.get("wiki_source_path"), f"review_required should not have wiki_source_path: {blocked_ingest}")
        blocked_id = blocked_ingest["source_id"]
        blocked_id_url = urllib.parse.quote(blocked_id, safe="")
        source_ids.append(blocked_id)
        created_paths.append(blocked_response.get("path", ""))
        error_path = artifact_dir_for(blocked_id) / "error.json"
        assert_true(error_path.exists(), f"blocked error.json missing: {error_path}")
        error_status, error_payload, error_type = request_json(
            base_url,
            "GET",
            f"/api/sources/{blocked_id_url}/artifacts/error",
        )
        assert_true(error_status == 200, f"blocked error artifact API failed: {error_status} {error_payload}")
        assert_true(error_type.startswith("application/json"), f"blocked error content-type not JSON: {error_type}")
        assert_true("风控" in json.dumps(error_payload, ensure_ascii=False), f"blocked error reason missing: {error_payload}")

        after_count = concept_count()
        assert_true(after_count == before_count, f"concept count changed: before {before_count}, after {after_count}")
        result.update(
            {
                "ok": True,
                "normal": {
                    "source_id": source_id,
                    "source_path": normal_response.get("path"),
                    "wiki_source_path": normal_wiki_source,
                    "updated_before": updated_before,
                    "updated_after": updated_after,
                },
                "blocked": {
                    "source_id": blocked_id,
                    "source_path": blocked_response.get("path"),
                    "status": blocked_ingest.get("status"),
                },
                "after_concept_count": after_count,
            }
        )
        return result
    finally:
        for path in created_paths:
            remove_path(path)
        for source_id in source_ids:
            shutil.rmtree(artifact_dir_for(source_id), ignore_errors=True)
        result["cleanup_checked"] = True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MVP ingest smoke tests through the Web API.")
    parser.add_argument("--base-url", help="Use an already running wiki_web.py service instead of starting one.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()

    server: subprocess.Popen | None = None
    base_url = (args.base_url or f"http://{args.host}:{args.port}").rstrip("/")
    try:
        if not args.base_url:
            server = start_server(args.host, args.port)
        wait_for_server(base_url)
        result = run_smoke(base_url)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
