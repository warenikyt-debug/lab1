from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.permission import Permission
from app.dto.rbac_dto import PermissionDTO, PermissionCollectionDTO
from app.services.permission_service import PermissionService
from app.middlewares.auth_middleware import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/ref/policy/permission", tags=["permissions"])


@router.get("", response_model=PermissionCollectionDTO)
def list_permissions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    permissions = db.query(Permission).filter(Permission.deleted_at == None).offset(skip).limit(limit).all()
    total = db.query(Permission).filter(Permission.deleted_at == None).count()
    
    return PermissionCollectionDTO(
        items=[PermissionDTO.from_orm(p) for p in permissions],
        total=total,
        count=len(permissions)
    )


@router.get("/{permission_id}", response_model=PermissionDTO)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    permission = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.deleted_at == None
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")
    
    return PermissionDTO.from_orm(permission)


@router.post("", response_model=PermissionDTO, status_code=201)
def create_permission(
    name: str,
    slug: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "create-permission"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    existing = db.query(Permission).filter(Permission.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Разрешение с таким slug уже существует")
    
    permission = Permission(
        name=name,
        slug=slug,
        description=description,
        created_by=user_id
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return PermissionDTO.from_orm(permission)


@router.put("/{permission_id}", response_model=PermissionDTO)
def update_permission(
    permission_id: int,
    name: str,
    slug: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "update-permission"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.deleted_at == None
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")
    
    permission.name = name
    permission.slug = slug
    permission.description = description
    permission.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(permission)
    
    return PermissionDTO.from_orm(permission)


@router.delete("/{permission_id}/permanent", status_code=204)
def hard_delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "delete-permission"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")
    
    db.delete(permission)
    db.commit()
    
    return None


@router.delete("/{permission_id}", status_code=204)
def soft_delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "delete-permission"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.deleted_at == None
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")
    
    permission.deleted_at = datetime.utcnow()
    permission.deleted_by = user_id
    db.commit()
    
    return None


@router.post("/{permission_id}/restore", status_code=200)
def restore_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "restore-permission"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")
    
    permission.deleted_at = None
    permission.deleted_by = None
    db.commit()
    
    return {"message": "Разрешение восстановлено"}
