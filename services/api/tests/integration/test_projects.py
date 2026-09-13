import uuid
import pytest


def test_create_and_list_projects(client, user_a_headers):
    # 1. Create project
    create_resp = client.post(
        "/api/v1/projects",
        json={"name": "Alpha Service", "description": "Primary backend application"},
        headers=user_a_headers,
    )
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["name"] == "Alpha Service"
    assert data["description"] == "Primary backend application"
    assert data["asset_count"] == 1  # Default asset automatically created
    project_id = data["id"]

    # 2. List projects
    list_resp = client.get("/api/v1/projects", headers=user_a_headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    found = [p for p in list_data["items"] if p["id"] == project_id]
    assert len(found) == 1
    assert found[0]["name"] == "Alpha Service"


def test_cross_user_isolation(client, user_a_headers, user_b_headers):
    # User A creates a project
    create_resp = client.post(
        "/api/v1/projects",
        json={"name": "Secret Project A", "description": "Confidential"},
        headers=user_a_headers,
    )
    assert create_resp.status_code == 201
    proj_a_id = create_resp.json()["id"]

    # User B tries to read User A's project -> MUST return 404, not 403 (PRD Section 4)
    get_resp = client.get(f"/api/v1/projects/{proj_a_id}", headers=user_b_headers)
    assert get_resp.status_code == 404
    assert get_resp.json()["error"]["code"] == "NOT_FOUND"

    # User B tries to update User A's project -> 404
    patch_resp = client.patch(
        f"/api/v1/projects/{proj_a_id}",
        json={"name": "Hijacked"},
        headers=user_b_headers,
    )
    assert patch_resp.status_code == 404

    # User B tries to delete User A's project -> 404
    del_resp = client.delete(f"/api/v1/projects/{proj_a_id}", headers=user_b_headers)
    assert del_resp.status_code == 404

    # Verify project A was not altered
    check_resp = client.get(f"/api/v1/projects/{proj_a_id}", headers=user_a_headers)
    assert check_resp.status_code == 200
    assert check_resp.json()["name"] == "Secret Project A"


def test_asset_crud_and_weight_validation(client, user_a_headers, user_b_headers):
    # Create project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Multi-Tier Web App"},
        headers=user_a_headers,
    )
    project_id = proj_resp.json()["id"]

    # Add custom asset with weight 5
    asset_resp = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={"name": "Payment Gateway", "environment": "production", "default_weight": 5},
        headers=user_a_headers,
    )
    assert asset_resp.status_code == 201
    asset_data = asset_resp.json()
    assert asset_data["name"] == "Payment Gateway"
    assert asset_data["default_weight"] == 5
    asset_id = asset_data["id"]

    # Reject invalid weight (< 1 or > 5)
    bad_weight_resp = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={"name": "Invalid Asset", "environment": "staging", "default_weight": 8},
        headers=user_a_headers,
    )
    assert bad_weight_resp.status_code == 422

    # User B cannot add assets to User A's project
    foreign_add_resp = client.post(
        f"/api/v1/projects/{project_id}/assets",
        json={"name": "Injected Asset", "environment": "prod", "default_weight": 3},
        headers=user_b_headers,
    )
    assert foreign_add_resp.status_code == 404

    # Update asset
    update_resp = client.patch(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        json={"default_weight": 4, "environment": "critical-production"},
        headers=user_a_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["default_weight"] == 4
    assert update_resp.json()["environment"] == "critical-production"

    # Delete asset
    del_resp = client.delete(
        f"/api/v1/projects/{project_id}/assets/{asset_id}",
        headers=user_a_headers,
    )
    assert del_resp.status_code == 204
