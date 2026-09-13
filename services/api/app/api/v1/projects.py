import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.auth import get_current_user
from app.core.errors import NotFoundException, ValidationException
from app.db.session import get_db
from app.db.models import User, Project, Asset, Snapshot
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.schemas.asset import AssetCreate, AssetUpdate, AssetRead
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_user_project(project_id: uuid.UUID, user: User, db: Session) -> Project:
    """Retrieve project by ID, verifying that current_user is the owner.
    Fails closed with 404 to avoid leaking existence of foreign projects.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_user_id == user.id)
        .first()
    )
    if not project:
        raise NotFoundException(message=f"Project '{project_id}' not found.")
    return project


@router.get("", response_model=PaginatedResponse[ProjectRead])
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List projects owned by the authenticated user with pagination and asset/snapshot counts."""
    query = db.query(Project).filter(Project.owner_user_id == current_user.id)
    total = query.count()
    offset = (page - 1) * page_size
    projects = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for p in projects:
        asset_count = db.query(func.count(Asset.id)).filter(Asset.project_id == p.id).scalar() or 0
        snapshot_count = db.query(func.count(Snapshot.id)).filter(Snapshot.project_id == p.id).scalar() or 0
        read_obj = ProjectRead(
            id=p.id,
            owner_user_id=p.owner_user_id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            asset_count=asset_count,
            snapshot_count=snapshot_count,
        )
        items.append(read_obj)

    return PaginatedResponse[ProjectRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project owned by the current user and initialize a default asset."""
    project = Project(
        owner_user_id=current_user.id,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
    )
    db.add(project)
    db.flush()

    # Automatically add a default asset to represent the project's primary application
    default_asset = Asset(
        project_id=project.id,
        name=f"{project.name} Core",
        environment="production",
        default_weight=3,
    )
    db.add(default_asset)
    db.commit()
    db.refresh(project)

    return ProjectRead(
        id=project.id,
        owner_user_id=project.owner_user_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        asset_count=1,
        snapshot_count=0,
    )


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of an owned project."""
    project = get_user_project(project_id, current_user, db)
    asset_count = db.query(func.count(Asset.id)).filter(Asset.project_id == project.id).scalar() or 0
    snapshot_count = db.query(func.count(Snapshot.id)).filter(Snapshot.project_id == project.id).scalar() or 0
    assets = db.query(Asset).filter(Asset.project_id == project.id).order_by(Asset.created_at.asc()).all()

    return ProjectRead(
        id=project.id,
        owner_user_id=project.owner_user_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        asset_count=asset_count,
        snapshot_count=snapshot_count,
        assets=[AssetRead.model_validate(a) for a in assets],
    )


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update project name or description."""
    project = get_user_project(project_id, current_user, db)
    if data.name is not None:
        project.name = data.name.strip()
    if data.description is not None:
        project.description = data.description.strip()
    db.commit()
    db.refresh(project)

    asset_count = db.query(func.count(Asset.id)).filter(Asset.project_id == project.id).scalar() or 0
    snapshot_count = db.query(func.count(Snapshot.id)).filter(Snapshot.project_id == project.id).scalar() or 0

    return ProjectRead(
        id=project.id,
        owner_user_id=project.owner_user_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        asset_count=asset_count,
        snapshot_count=snapshot_count,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete project and associated resources."""
    project = get_user_project(project_id, current_user, db)
    db.delete(project)
    db.commit()
    return None


# --- Project Assets ---

@router.get("/{project_id}/assets", response_model=list[AssetRead])
def list_project_assets(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all assets for a project."""
    project = get_user_project(project_id, current_user, db)
    assets = db.query(Asset).filter(Asset.project_id == project.id).order_by(Asset.created_at.asc()).all()
    return [AssetRead.model_validate(a) for a in assets]


@router.post("/{project_id}/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_project_asset(
    project_id: uuid.UUID,
    data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new asset for an owned project."""
    project = get_user_project(project_id, current_user, db)
    asset = Asset(
        project_id=project.id,
        name=data.name.strip(),
        environment=data.environment.strip(),
        default_weight=data.default_weight,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.patch("/{project_id}/assets/{asset_id}", response_model=AssetRead)
def update_project_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    data: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update asset name, environment, or weight."""
    project = get_user_project(project_id, current_user, db)
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.project_id == project.id).first()
    if not asset:
        raise NotFoundException(message=f"Asset '{asset_id}' not found.")

    if data.name is not None:
        asset.name = data.name.strip()
    if data.environment is not None:
        asset.environment = data.environment.strip()
    if data.default_weight is not None:
        asset.default_weight = data.default_weight

    db.commit()
    db.refresh(asset)
    return AssetRead.model_validate(asset)


@router.delete("/{project_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an asset from a project."""
    project = get_user_project(project_id, current_user, db)
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.project_id == project.id).first()
    if not asset:
        raise NotFoundException(message=f"Asset '{asset_id}' not found.")

    db.delete(asset)
    db.commit()
    return None
