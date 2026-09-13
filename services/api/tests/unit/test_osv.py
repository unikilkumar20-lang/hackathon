import pytest
from app.enrichment.osv_client import OSVClient, OSVPackageResult


@pytest.mark.asyncio
async def test_osv_cache_and_deduplication(monkeypatch):
    OSVClient.clear_cache()
    client = OSVClient()

    call_count = 0

    async def mock_post(self, url, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        class MockResp:
            status_code = 200
            def json(self):
                return {
                    "results": [
                        {
                            "vulns": [
                                {
                                    "id": "GHSA-1234",
                                    "aliases": ["CVE-2023-9999"],
                                    "summary": "Sample advisory",
                                }
                            ]
                        }
                    ]
                }
        return MockResp()

    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    # 1. Provide duplicates in batch
    pkgs = [
        {"ecosystem": "npm", "name": "lodash", "version": "4.17.20"},
        {"ecosystem": "npm", "name": "lodash", "version": "4.17.20"},  # duplicate
    ]

    report = await client.check_packages(pkgs)
    assert report.status == "complete"
    assert report.checked_count == 1  # Deduplicated!
    assert report.matched_count == 1
    assert call_count == 1

    # 2. Query again -> should hit cache!
    report_cached = await client.check_packages(pkgs)
    assert report_cached.status == "complete"
    assert call_count == 1  # No additional network call made!
