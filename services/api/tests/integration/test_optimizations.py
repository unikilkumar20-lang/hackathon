import os
import json
import pytest

CYCLONEDX_FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "fixtures", "cyclonedx", "valid_cyclonedx.json")
)


def test_optimization_and_export(client, user_a_headers):
    # 1. Setup project & snapshot
    proj_resp = client.post("/api/v1/projects", json={"name": "Opt Project"}, headers=user_a_headers)
    proj_id = proj_resp.json()["id"]

    with open(CYCLONEDX_FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        f"/api/v1/projects/{proj_id}/snapshots",
        files={"file": ("valid_cyclonedx.json", file_bytes, "application/json")},
        headers=user_a_headers,
    )
    snap_id = upload_resp.json()["id"]

    # 2. Run scenario
    run_resp = client.post(
        "/api/v1/runs",
        json={
            "snapshot_id": snap_id,
            "source": {"kind": "occurrence", "id": "qs@6.11.0"},
            "mode": "runtime",
        },
        headers=user_a_headers,
    )
    run_id = run_resp.json()["id"]

    # 3. POST /runs/{id}/optimizations
    opt_resp = client.post(
        f"/api/v1/runs/{run_id}/optimizations",
        json={
            "budget": 3,
            "candidate_controls": [
                {
                    "id": "ctrl-replace-qs",
                    "label": "Replace qs parser",
                    "cost": 2,
                    "control_type": "replace_occurrence",
                    "parameters": {"occurrence_ref": "qs@6.11.0"},
                    "mechanism_scope": "global",
                }
            ],
        },
        headers=user_a_headers,
    )
    assert opt_resp.status_code == 201
    opt_data = opt_resp.json()
    assert opt_data["budget"] == 3
    assert opt_data["total_cost"] == 2
    assert len(opt_data["chosen_controls"]) == 1
    assert opt_data["optimized_upper"] <= opt_data["baseline_upper"]

    # 4. GET /runs/{id}/export
    export_resp = client.get(f"/api/v1/runs/{run_id}/export", headers=user_a_headers)
    assert export_resp.status_code == 200
    assert "attachment" in export_resp.headers.get("content-disposition", "")
    report = export_resp.json()
    assert report["rippleguard_report_version"] == "1.0.0"
    assert "provenance" in report
    assert "exposure_metrics" in report
    assert "counterfactual_optimization" in report
