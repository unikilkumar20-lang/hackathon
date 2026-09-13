import os
import json
import pytest

CYCLONEDX_FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "fixtures", "cyclonedx", "valid_cyclonedx.json")
)


def test_snapshot_upload_and_graph(client, user_a_headers, user_b_headers):
    # 1. Create project for user A
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Alpha Web Service"},
        headers=user_a_headers,
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # 2. Upload CycloneDX JSON
    with open(CYCLONEDX_FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        f"/api/v1/projects/{proj_id}/snapshots",
        files={"file": ("valid_cyclonedx.json", file_bytes, "application/json")},
        headers=user_a_headers,
    )
    assert upload_resp.status_code == 201
    snap_data = upload_resp.json()
    snap_id = snap_data["id"]

    assert snap_data["topology_status"] == "complete"
    assert snap_data["occurrence_count"] >= 5
    assert snap_data["edge_count"] >= 4

    # 3. Retrieve Snapshot
    get_snap = client.get(f"/api/v1/snapshots/{snap_id}", headers=user_a_headers)
    assert get_snap.status_code == 200
    assert get_snap.json()["id"] == snap_id

    # 4. Retrieve Cytoscape Graph
    graph_resp = client.get(f"/api/v1/snapshots/{snap_id}/graph", headers=user_a_headers)
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["edges"]) > 0

    # 5. Verify Cross-User Isolation: User B cannot access User A's snapshot
    cross_resp = client.get(f"/api/v1/snapshots/{snap_id}", headers=user_b_headers)
    assert cross_resp.status_code == 404  # Fails closed with 404
