import os
import json
import pytest

CYCLONEDX_FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "fixtures", "cyclonedx", "valid_cyclonedx.json")
)


def test_scenario_run_and_evidence(client, user_a_headers, user_b_headers):
    # 1. Setup project and snapshot
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Run Test Project"},
        headers=user_a_headers,
    )
    proj_id = proj_resp.json()["id"]

    with open(CYCLONEDX_FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        f"/api/v1/projects/{proj_id}/snapshots",
        files={"file": ("valid_cyclonedx.json", file_bytes, "application/json")},
        headers=user_a_headers,
    )
    snap_id = upload_resp.json()["id"]

    # 2. POST /runs: simulate compromise of qs@6.11.0
    run_resp = client.post(
        "/api/v1/runs",
        json={
            "snapshot_id": snap_id,
            "source": {
                "kind": "occurrence",
                "id": "qs@6.11.0",
                "scope": "all_matching_occurrences",
            },
            "mode": "runtime",
            "gate_overrides": [],
        },
        headers=user_a_headers,
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    run_id = run_data["id"]

    assert "lower_index" in run_data
    assert "upper_index" in run_data
    assert run_data["lower_index"] <= run_data["upper_index"]
    assert len(run_data["reached_assets"]) > 0
    assert len(run_data["evidence_ids"]) > 0

    # 3. GET /runs/{run_id}
    get_run = client.get(f"/api/v1/runs/{run_id}", headers=user_a_headers)
    assert get_run.status_code == 200
    assert get_run.json()["id"] == run_id

    # 4. GET /runs/{run_id}/evidence
    ev_resp = client.get(f"/api/v1/runs/{run_id}/evidence", headers=user_a_headers)
    assert ev_resp.status_code == 200
    assert len(ev_resp.json()) > 0

    # 5. Cross-user isolation: User B cannot access run
    cross_resp = client.get(f"/api/v1/runs/{run_id}", headers=user_b_headers)
    assert cross_resp.status_code == 404
