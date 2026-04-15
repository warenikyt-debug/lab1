"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - Role Permission Controller                                  ║
║                                                                              ║
║ Контроллер для управления разрешениями ролей (many-to-many)                 ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.config.database import get_db
from app.middlewares.auth_middleware import get_current_user
from app.models.role import Role
from app.models.permission import Permission
from app.models.permission_role import PermissionRole
from app.services.permission_service import PermissionService
from app.dto.rbac_dto import PermissionDTO

router = APIRouter(prefix="/api/ref/policy/role", tags=["role-permissions"])


@router.get("/{role_id}/permissions")
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """GET /api/ref/policy/role/{role}/permissions - Получение разрешений роли"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permissions = db.query(Permission).join(
        PermissionRole,
        Permission.id == PermissionRole.permission_id
    ).filter(
        PermissionRole.role_id == role_id,
        PermissionRole.deleted_at == None,
        Permission.deleted_at == None
    ).all()
    
    return [PermissionDTO.model_validate(p) for p in permissions]


@router.post("/{role_id}/permission/{permission_id}", status_code=201)
def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/policy/role/{role}/permission/{permission} - Назначение разрешения роли"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "assign-permission-to-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: assign-permission-to-role"}
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    existing = db.query(PermissionRole).filter(
        PermissionRole.role_id == role_id,
        PermissionRole.permission_id == permission_id
    ).first()
    
    if existing and existing.deleted_at is None:
        raise HTTPException(status_code=400, detail="Permission already assigned to this role")
    
    if existing and existing.deleted_at is not None:
        existing.deleted_at = None
        existing.deleted_by = None
        db.commit()
        return {"message": f"Permission {permission.name} restored for role {role.name}"}
    
    perm_role = PermissionRole(
        role_id=role_id,
        permission_id=permission_id,
        created_by=user_id
    )
    db.add(perm_role)
    db.commit()
    
    return {"message": f"Permission {permission.name} assigned to role {role.name}"}


@router.delete("/{role_id}/permission/{permission_id}", status_code=204)
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/policy/role/{role}/permission/{permission} - Удаление разрешения у роли"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "remove-permission-from-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: remove-permission-from-role"}
        )
    
    perm_role = db.query(PermissionRole).filter(
        PermissionRole.role_id == role_id,
        PermissionRole.permission_id == permission_id
    ).first()
    
    if not perm_role:
        raise HTTPException(status_code=404, detail="Permission not assigned to this role")
    
    db.delete(perm_role)
    db.commit()
