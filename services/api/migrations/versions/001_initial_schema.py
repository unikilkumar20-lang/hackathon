"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-11 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from app.db.types import GUID, JSONType

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])

    # Projects
    op.create_table(
        "projects",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("owner_user_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_owner_user_id", "projects", ["owner_user_id"])

    # Assets
    op.create_table(
        "assets",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("default_weight", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assets_project_id", "assets", ["project_id"])

    # Snapshots
    op.create_table(
        "snapshots",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("project_id", GUID(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("topology_status", sa.String(length=32), nullable=False),
        sa.Column("warnings", JSONType(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshots_project_id", "snapshots", ["project_id"])

    # Inventories
    op.create_table(
        "inventories",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("asset_id", GUID(), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_content", JSONType(), nullable=False),
        sa.Column("warnings", JSONType(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventories_snapshot_id", "inventories", ["snapshot_id"])

    # Package Identities
    op.create_table(
        "package_identities",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("ecosystem", sa.String(length=64), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=128), nullable=False),
        sa.Column("canonical_purl", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ecosystem", "namespace", "name", "version", name="uq_package_identity"),
    )
    op.create_index("ix_pkg_eco_name_ver", "package_identities", ["ecosystem", "name", "version"])

    # Occurrences
    op.create_table(
        "occurrences",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("inventory_id", GUID(), nullable=True),
        sa.Column("package_identity_id", GUID(), nullable=True),
        sa.Column("local_ref", sa.String(length=512), nullable=False),
        sa.Column("metadata_json", JSONType(), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_identity_id"], ["package_identities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_occurrences_snapshot_id", "occurrences", ["snapshot_id"])

    # Edges
    op.create_table(
        "edges",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("from_ref", sa.String(length=512), nullable=False),
        sa.Column("to_ref", sa.String(length=512), nullable=False),
        sa.Column("context", JSONType(), nullable=False),
        sa.Column("gate_default", sa.String(length=16), nullable=False),
        sa.Column("provenance", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edges_snapshot_id", "edges", ["snapshot_id"])

    # Snapshot Assets
    op.create_table(
        "snapshot_assets",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("asset_id", GUID(), nullable=False),
        sa.Column("root_ref", sa.String(length=512), nullable=False),
        sa.Column("captured_weight", sa.Integer(), nullable=False),
        sa.Column("environment_context", JSONType(), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Enrichment Checks
    op.create_table(
        "enrichment_checks",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("coverage", JSONType(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Advisories
    op.create_table(
        "advisories",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("aliases", JSONType(), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("details", JSONType(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_advisory_provider_external_id"),
    )

    # Findings
    op.create_table(
        "findings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("check_id", GUID(), nullable=False),
        sa.Column("package_identity_id", GUID(), nullable=False),
        sa.Column("advisory_id", GUID(), nullable=False),
        sa.Column("match_details", JSONType(), nullable=False),
        sa.ForeignKeyConstraint(["check_id"], ["enrichment_checks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["package_identity_id"], ["package_identities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["advisory_id"], ["advisories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Evidence
    op.create_table(
        "evidence",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("trust_label", sa.String(length=64), nullable=False),
        sa.Column("details", JSONType(), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Runs
    op.create_table(
        "runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("snapshot_id", GUID(), nullable=False),
        sa.Column("scenario_json", JSONType(), nullable=False),
        sa.Column("result_json", JSONType(), nullable=False),
        sa.Column("graph_model_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Controls
    op.create_table(
        "controls",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("edit_json", JSONType(), nullable=False),
        sa.Column("mechanism_scope", sa.String(length=64), nullable=False),
        sa.Column("assumptions", JSONType(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Optimization Runs
    op.create_table(
        "optimization_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("run_id", GUID(), nullable=False),
        sa.Column("budget", sa.Integer(), nullable=False),
        sa.Column("candidate_set_hash", sa.String(length=64), nullable=False),
        sa.Column("chosen_controls", JSONType(), nullable=False),
        sa.Column("result_json", JSONType(), nullable=False),
        sa.Column("optimizer_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("optimization_runs")
    op.drop_table("controls")
    op.drop_table("runs")
    op.drop_table("evidence")
    op.drop_table("findings")
    op.drop_table("advisories")
    op.drop_table("enrichment_checks")
    op.drop_table("snapshot_assets")
    op.drop_table("edges")
    op.drop_table("occurrences")
    op.drop_table("package_identities")
    op.drop_table("inventories")
    op.drop_table("snapshots")
    op.drop_table("assets")
    op.drop_table("projects")
    op.drop_table("users")
