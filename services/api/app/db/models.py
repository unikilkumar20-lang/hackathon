import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.types import GUID, JSONType


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", back_populates="projects")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="project", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    environment = Column(String(64), nullable=False, default="production")  # e.g., production, staging, internal
    default_weight = Column(Integer, nullable=False, default=3)  # 1 to 5 integer weight
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("Project", back_populates="assets")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False)
    parser_version = Column(String(32), nullable=False, default="1.0.0")
    topology_status = Column(String(32), nullable=False, default="complete")  # complete / incomplete / degraded
    warnings = Column(JSONType, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("Project", back_populates="snapshots")
    inventories = relationship("Inventory", back_populates="snapshot", cascade="all, delete-orphan")
    occurrences = relationship("Occurrence", back_populates="snapshot", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="snapshot", cascade="all, delete-orphan")
    snapshot_assets = relationship("SnapshotAsset", back_populates="snapshot", cascade="all, delete-orphan")
    enrichment_checks = relationship("EnrichmentCheck", back_populates="snapshot", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="snapshot", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="snapshot", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventories"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(GUID, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = Column(String(64), nullable=False, default="cyclonedx-json")
    source_ref = Column(String(255), nullable=True)
    source_hash = Column(String(64), nullable=False)
    raw_content = Column(JSONType, nullable=False)
    warnings = Column(JSONType, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    snapshot = relationship("Snapshot", back_populates="inventories")
    occurrences = relationship("Occurrence", back_populates="inventory")


class PackageIdentity(Base):
    __tablename__ = "package_identities"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    ecosystem = Column(String(64), nullable=False)
    namespace = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    version = Column(String(128), nullable=False)
    canonical_purl = Column(String(512), nullable=True)

    __table_args__ = (
        UniqueConstraint("ecosystem", "namespace", "name", "version", name="uq_package_identity"),
        Index("ix_pkg_eco_name_ver", "ecosystem", "name", "version"),
    )


class Occurrence(Base):
    __tablename__ = "occurrences"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id = Column(GUID, ForeignKey("inventories.id", ondelete="CASCADE"), nullable=True, index=True)
    package_identity_id = Column(GUID, ForeignKey("package_identities.id", ondelete="SET NULL"), nullable=True, index=True)
    local_ref = Column(String(512), nullable=False)  # bom-ref or manifest ref
    metadata_json = Column(JSONType, nullable=False, default=dict)

    snapshot = relationship("Snapshot", back_populates="occurrences")
    inventory = relationship("Inventory", back_populates="occurrences")
    package_identity = relationship("PackageIdentity")


class Edge(Base):
    __tablename__ = "edges"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    from_ref = Column(String(512), nullable=False, index=True)  # consumer occurrence or root
    to_ref = Column(String(512), nullable=False, index=True)    # dependency occurrence
    context = Column(JSONType, nullable=False, default=dict)
    gate_default = Column(String(16), nullable=False, default="unknown")  # true, false, unknown
    provenance = Column(String(64), nullable=False, default="cyclonedx-manifest")

    snapshot = relationship("Snapshot", back_populates="edges")


class SnapshotAsset(Base):
    __tablename__ = "snapshot_assets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(GUID, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    root_ref = Column(String(512), nullable=False)
    captured_weight = Column(Integer, nullable=False, default=3)
    environment_context = Column(JSONType, nullable=False, default=dict)

    snapshot = relationship("Snapshot", back_populates="snapshot_assets")
    asset = relationship("Asset")


class EnrichmentCheck(Base):
    __tablename__ = "enrichment_checks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(64), nullable=False, default="osv")
    status = Column(String(32), nullable=False, default="pending")  # pending/complete/partial/failed
    coverage = Column(JSONType, nullable=False, default=dict)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

    snapshot = relationship("Snapshot", back_populates="enrichment_checks")
    findings = relationship("Finding", back_populates="check", cascade="all, delete-orphan")


class Advisory(Base):
    __tablename__ = "advisories"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    provider = Column(String(64), nullable=False, default="osv")
    external_id = Column(String(128), nullable=False, index=True)
    aliases = Column(JSONType, nullable=False, default=list)
    source_url = Column(String(512), nullable=True)
    details = Column(JSONType, nullable=False, default=dict)
    retrieved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_advisory_provider_external_id"),
    )


class Finding(Base):
    __tablename__ = "findings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    check_id = Column(GUID, ForeignKey("enrichment_checks.id", ondelete="CASCADE"), nullable=False, index=True)
    package_identity_id = Column(GUID, ForeignKey("package_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    advisory_id = Column(GUID, ForeignKey("advisories.id", ondelete="CASCADE"), nullable=False, index=True)
    match_details = Column(JSONType, nullable=False, default=dict)

    check = relationship("EnrichmentCheck", back_populates="findings")
    package_identity = relationship("PackageIdentity")
    advisory = relationship("Advisory")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(64), nullable=False)  # osv_advisory, witness_path, scenario_assumption, gate_proof
    source_ref = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    content_hash = Column(String(64), nullable=True)
    trust_label = Column(String(64), nullable=False, default="official_provider")
    details = Column(JSONType, nullable=False, default=dict)

    snapshot = relationship("Snapshot", back_populates="evidence")


class Run(Base):
    __tablename__ = "runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(GUID, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_json = Column(JSONType, nullable=False)
    result_json = Column(JSONType, nullable=False)
    graph_model_version = Column(String(32), nullable=False, default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    snapshot = relationship("Snapshot", back_populates="runs")
    controls = relationship("Control", back_populates="run", cascade="all, delete-orphan")
    optimizations = relationship("OptimizationRun", back_populates="run", cascade="all, delete-orphan")


class Control(Base):
    __tablename__ = "controls"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    cost = Column(Integer, nullable=False, default=1)
    edit_json = Column(JSONType, nullable=False)
    mechanism_scope = Column(String(64), nullable=False)
    assumptions = Column(JSONType, nullable=False, default=list)

    run = relationship("Run", back_populates="controls")


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    budget = Column(Integer, nullable=False)
    candidate_set_hash = Column(String(64), nullable=False)
    chosen_controls = Column(JSONType, nullable=False, default=list)
    result_json = Column(JSONType, nullable=False)
    optimizer_version = Column(String(32), nullable=False, default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    run = relationship("Run", back_populates="optimizations")
