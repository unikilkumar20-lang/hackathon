import pytest

def test_public_synthetic_demo_fixture_parity(client):
    """PRD Section 17 & Milestone 6 Acceptance Test:
    Verify exact numbers of the synthetic multi-app fixture:
    5 assets, total weight 18, baseline lower = 66.7%, baseline upper = 72.2%.
    """
    resp = client.get("/api/v1/demo/fixture")
    assert resp.status_code == 200
    data = resp.json()

    assert "Synthetic scenario" in data["disclaimer"]
    assert len(data["assets"]) == 5

    metrics = data["baseline_metrics"]
    assert metrics["total_scoped_weight"] == 18
    assert metrics["lower_index"] == pytest.approx(66.7, abs=0.1)  # 12 / 18 = 66.67%
    assert metrics["upper_index"] == pytest.approx(72.2, abs=0.1)  # 13 / 18 = 72.22%

    # Verify root endpoint alias /demo/fixture
    root_resp = client.get("/demo/fixture")
    assert root_resp.status_code == 200
    assert root_resp.json()["baseline_metrics"]["total_scoped_weight"] == 18


def test_public_demo_evaluate_and_optimize(client):
    # Interactive scenario evaluation
    eval_resp = client.post(
        "/api/v1/demo/evaluate",
        json={
            "mode": "runtime",
            "source_ref": "tiny-parse@1.0.0",
            "gate_overrides": [
                {
                    "target_type": "edge",
                    "target_id": "edge-docs-theme",
                    "value": "false",
                    "reason": "Docs route verified blocked",
                }
            ],
        },
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    # When Docs is blocked, upper exposure drops to 66.7%!
    assert eval_data["lower_index"] == pytest.approx(66.7, abs=0.1)
    assert eval_data["upper_index"] == pytest.approx(66.7, abs=0.1)

    # Public mitigation optimization
    opt_resp = client.post("/api/v1/demo/optimize?budget=4&mode=runtime")
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()
    assert opt_data["budget"] == 4
    assert opt_data["total_cost"] <= 4
    assert opt_data["optimized_upper"] < opt_data["baseline_upper"]
