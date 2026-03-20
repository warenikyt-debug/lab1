from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.role import Role
from app.dto.rbac_dto import RoleDTO, RoleCollectionDTO
from app.services.permission_service import PermissionService
from app.middlewares.auth_middleware import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/ref/policy/role", tags=["roles"])


@router.get("", response_model=RoleCollectionDTO)
def list_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    roles = db.query(Role).filter(Role.deleted_at == None).offset(skip).limit(limit).all()
    total = db.query(Role).filter(Role.deleted_at == None).count()
    
    return RoleCollectionDTO(
        items=[RoleDTO.from_orm(role) for role in roles],
        total=total,
        count=len(roles)
    )


@router.get("/{role_id}", response_model=RoleDTO)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.deleted_at == None
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    return RoleDTO.from_orm(role)


@router.post("", response_model=RoleDTO, status_code=201)
def create_role(
    name: str,
    slug: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "create-role"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    existing = db.query(Role).filter(Role.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Роль с таким slug уже существует")
    
    role = PermissionService.create_role(db, name, slug, description, user_id)
    return RoleDTO.from_orm(role)


@router.put("/{role_id}", response_model=RoleDTO)
def update_role(
    role_id: int,
    name: str,
    slug: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "update-role"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    role = PermissionService.update_role(db, role_id, name, slug, description)
    
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    return RoleDTO.from_orm(role)


@router.delete("/{role_id}/permanent", status_code=204)
def hard_delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "delete-role"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    success = PermissionService.hard_delete_role(db, role_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    return None


@router.delete("/{role_id}", status_code=204)
def soft_delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "delete-role"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    success = PermissionService.soft_delete_role(db, role_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    return None


@router.post("/{role_id}/restore", status_code=200)
def restore_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = int(current_user.get("sub"))
    
    if not PermissionService.check_permission(db, user_id, "restore-role"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    success = PermissionService.restore_role(db, role_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    return {"message": "Роль восстановлена"}
