import os
import json
import pytest
import httpx
from app.enrichment.osv_client import OSVClient

CYCLONEDX_FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "fixtures", "cyclonedx", "valid_cyclonedx.json")
)


def test_enrichment_check_and_findings(client, user_a_headers, monkeypatch):
    OSVClient.clear_cache()

    # Mock OSV HTTP response
    async def mock_post(self, url, *args, **kwargs):
        class MockResp:
            status_code = 200
            def json(self):
                body = kwargs.get("json", {})
                queries = body.get("queries", [])
                results = []
                for q in queries:
                    pkg = q.get("package", {})
                    pkg_id = pkg.get("name", "") or pkg.get("purl", "")
                    if "express" in pkg_id or "qs" in pkg_id:
                        results.append(
                            {
                                "vulns": [
                                    {
                                        "id": f"GHSA-{pkg_id}-vuln",
                                        "aliases": [f"CVE-2024-{pkg_id}"],
                                        "summary": f"Known security advisory for {pkg_id}",
                                        "severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}],
                                    }
                                ]
                            }
                        )
                    else:
                        results.append({"vulns": []})
                return {"results": results}
        return MockResp()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    # 1. Setup project & snapshot
    proj_resp = client.post("/api/v1/projects", json={"name": "Enrichment Project"}, headers=user_a_headers)
    proj_id = proj_resp.json()["id"]

    with open(CYCLONEDX_FIXTURE_PATH, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post(
        f"/api/v1/projects/{proj_id}/snapshots",
        files={"file": ("valid_cyclonedx.json", file_bytes, "application/json")},
        headers=user_a_headers,
    )
    snap_id = upload_resp.json()["id"]

    # 2. Trigger enrichment check
    check_resp = client.post(
        f"/api/v1/snapshots/{snap_id}/enrichment-checks",
        headers=user_a_headers,
    )
    assert check_resp.status_code == 201
    check_data = check_resp.json()
    assert check_data["status"] == "complete"
    assert check_data["findings_count"] >= 1

    # 3. Retrieve findings
    findings_resp = client.get(
        f"/api/v1/snapshots/{snap_id}/findings",
        headers=user_a_headers,
    )
    assert findings_resp.status_code == 200
    findings_data = findings_resp.json()
    assert findings_data["total"] >= 1
    first_finding = findings_data["items"][0]
    assert "package_name" in first_finding
    assert "advisory" in first_finding
    assert first_finding["advisory"]["provider"] == "osv"
