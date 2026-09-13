import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.schemas.run import RunRead
from app.schemas.optimization import OptimizationRead


class ReportExporter:
    """Exports self-contained, immutable JSON analysis reports (PRD Section 10 & 16)."""

    REPORT_SPEC_VERSION = "1.0.0"

    @classmethod
    def export_run_report(
        cls,
        run_data: Dict[str, Any],
        snapshot_metadata: Dict[str, Any],
        optimization_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Construct deterministic, sanitized JSON report export."""
        export_id = str(uuid.uuid4())
        exported_at = datetime.now(timezone.utc).isoformat()

        report: Dict[str, Any] = {
            "rippleguard_report_version": cls.REPORT_SPEC_VERSION,
            "export_id": export_id,
            "exported_at": exported_at,
            "provenance": {
                "system": "RippleGuard",
                "model_version": run_data.get("model_version", "1.0.0"),
                "optimizer_version": optimization_data.get("optimizer_version", "1.0.0") if optimization_data else None,
                "snapshot_id": run_data.get("snapshot_id"),
                "snapshot_content_hash": snapshot_metadata.get("content_hash"),
                "snapshot_created_at": snapshot_metadata.get("created_at"),
                "topology_status": snapshot_metadata.get("topology_status", "complete"),
                "topology_warnings": snapshot_metadata.get("warnings", []),
            },
            "scenario": run_data.get("scenario", {}),
            "exposure_metrics": {
                "total_scoped_weight": run_data.get("total_scoped_weight", 0),
                "baseline_lower_exposure_percent": run_data.get("lower_index", 0.0),
                "baseline_upper_exposure_percent": run_data.get("upper_index", 0.0),
                "reached_assets": run_data.get("reached_assets", []),
                "witness_paths": run_data.get("witness_paths", []),
            },
            "assumptions_and_caveats": run_data.get("assumptions", []) + [
                "Conditional exposure indices are mathematical reachability bounds under stated gates.",
                "Zero exposure means 'no modeled exposure under this scenario', not a guarantee of total safety.",
                "Witness paths are deterministic shortest paths and may not be exhaustive.",
            ],
        }

        if optimization_data:
            report["counterfactual_optimization"] = {
                "optimization_id": optimization_data.get("id"),
                "budget": optimization_data.get("budget"),
                "total_effort_cost": optimization_data.get("total_cost"),
                "chosen_controls": optimization_data.get("chosen_controls", []),
                "optimized_lower_exposure_percent": optimization_data.get("optimized_lower"),
                "optimized_upper_exposure_percent": optimization_data.get("optimized_upper"),
                "absolute_exposure_reduction_points": optimization_data.get("absolute_reduction"),
                "relative_exposure_reduction_percent": optimization_data.get("relative_reduction"),
                "residual_assets": optimization_data.get("residual_assets", []),
                "residual_paths": optimization_data.get("residual_paths", []),
                "side_effects": optimization_data.get("side_effects", []),
            }

        return report
