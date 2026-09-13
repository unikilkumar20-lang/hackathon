import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger("rippleguard.osv")


@dataclass
class OSVAdvisoryMatch:
    external_id: str
    aliases: List[str]
    summary: Optional[str]
    details: Dict[str, Any]
    source_url: Optional[str]
    severity: Optional[str]
    modified: Optional[str]


@dataclass
class OSVPackageResult:
    ecosystem: str
    name: str
    version: str
    canonical_purl: Optional[str]
    status: str  # "matches_found" | "no_known_matches" | "failed" | "unsupported"
    advisories: List[OSVAdvisoryMatch] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class OSVEnrichmentReport:
    provider: str
    status: str  # "complete" | "partial" | "failed"
    checked_count: int
    matched_count: int
    failed_count: int
    unsupported_count: int
    started_at: datetime
    finished_at: datetime
    results: List[OSVPackageResult]
    error: Optional[str] = None


class OSVClient:
    """Official OSV (Open Source Vulnerabilities) API integration client (PRD Section 8)."""

    OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
    OSV_QUERY_URL = "https://api.osv.dev/v1/query"

    # In-memory LRU-like cache: (ecosystem, name, version) -> (timestamp, OSVPackageResult)
    _cache: Dict[Tuple[str, str, str], Tuple[datetime, OSVPackageResult]] = {}

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    async def check_packages(
        self,
        packages: List[Dict[str, Any]],
    ) -> OSVEnrichmentReport:
        """Query OSV for a batch of package identities. Deduplicates and caches results."""
        started_at = datetime.now(timezone.utc)
        now = started_at

        # 1. Deduplicate input packages by (ecosystem, name, version)
        unique_pkgs: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for p in packages:
            eco = str(p.get("ecosystem", "generic")).lower()
            name = str(p.get("name", ""))
            ver = str(p.get("version", ""))
            if name:
                unique_pkgs[(eco, name, ver)] = p

        results: List[OSVPackageResult] = []
        to_fetch: List[Tuple[Tuple[str, str, str], Dict[str, Any]]] = []

        # 2. Check cache
        for key, pdata in unique_pkgs.items():
            if key in self._cache:
                cached_time, cached_res = self._cache[key]
                if (now - cached_time).total_seconds() < settings.OSV_CACHE_TTL_SECONDS:
                    results.append(cached_res)
                    continue
            to_fetch.append((key, pdata))

        # 3. Query OSV API in batches
        failed_count = 0
        overall_error = None

        if to_fetch:
            queries = []
            for (eco, name, ver), pdata in to_fetch:
                q: Dict[str, Any] = {"version": ver}
                purl = pdata.get("canonical_purl")
                if purl:
                    q["package"] = {"purl": purl}
                else:
                    q["package"] = {"name": name, "ecosystem": eco}
                queries.append(q)

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.OSV_BATCH_URL, json={"queries": queries})
                    if resp.status_code == 200:
                        batch_data = resp.json().get("results", [])
                        for idx, ((eco, name, ver), pdata) in enumerate(to_fetch):
                            res_item = batch_data[idx] if idx < len(batch_data) else {}
                            vulns = res_item.get("vulns", [])

                            advisories: List[OSVAdvisoryMatch] = []
                            for v in vulns:
                                adv_id = v.get("id", "UNKNOWN")
                                aliases = v.get("aliases", [])
                                summary = v.get("summary")
                                severity = None
                                sev_list = v.get("severity", [])
                                if sev_list and isinstance(sev_list, list):
                                    severity = sev_list[0].get("score") if isinstance(sev_list[0], dict) else None

                                advisories.append(
                                    OSVAdvisoryMatch(
                                        external_id=adv_id,
                                        aliases=aliases,
                                        summary=summary,
                                        details=v,
                                        source_url=f"https://osv.dev/vulnerability/{adv_id}",
                                        severity=severity,
                                        modified=v.get("modified"),
                                    )
                                )

                            status = "matches_found" if advisories else "no_known_matches"
                            pkg_res = OSVPackageResult(
                                ecosystem=eco,
                                name=name,
                                version=ver,
                                canonical_purl=pdata.get("canonical_purl"),
                                status=status,
                                advisories=advisories,
                            )
                            # Cache result
                            self._cache[(eco, name, ver)] = (now, pkg_res)
                            results.append(pkg_res)
                    else:
                        overall_error = f"OSV HTTP {resp.status_code}: {resp.text[:200]}"
                        failed_count += len(to_fetch)
                        for (eco, name, ver), pdata in to_fetch:
                            results.append(
                                OSVPackageResult(
                                    ecosystem=eco,
                                    name=name,
                                    version=ver,
                                    canonical_purl=pdata.get("canonical_purl"),
                                    status="failed",
                                    error=overall_error,
                                )
                            )
            except Exception as e:
                logger.warning(f"OSV query error: {e}")
                overall_error = str(e)
                failed_count += len(to_fetch)
                for (eco, name, ver), pdata in to_fetch:
                    results.append(
                        OSVPackageResult(
                            ecosystem=eco,
                            name=name,
                            version=ver,
                            canonical_purl=pdata.get("canonical_purl"),
                            status="failed",
                            error=str(e),
                        )
                    )

        finished_at = datetime.now(timezone.utc)
        checked_count = len(results)
        matched_count = sum(1 for r in results if r.status == "matches_found")
        unsupported_count = sum(1 for r in results if r.status == "unsupported")

        if failed_count == 0:
            check_status = "complete"
        elif failed_count < checked_count:
            check_status = "partial"
        else:
            check_status = "failed"

        return OSVEnrichmentReport(
            provider="osv",
            status=check_status,
            checked_count=checked_count,
            matched_count=matched_count,
            failed_count=failed_count,
            unsupported_count=unsupported_count,
            started_at=started_at,
            finished_at=finished_at,
            results=results,
            error=overall_error,
        )
