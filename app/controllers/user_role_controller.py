"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - User Role Controller                                        ║
║                                                                              ║
║ Контроллер для управления ролями пользователей.                             ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.config.database import get_db
from app.middlewares.auth_middleware import get_current_user
from app.models.user import User
from app.models.role import Role
from app.models.role_user import RoleUser
from app.dto.rbac_dto import UserDTO, RoleDTO
from app.services.permission_service import PermissionService

router = APIRouter(tags=["users"])


@router.get("", response_model=list[UserDTO])
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """GET /api/ref/user - Получение списка пользователей (ТОЛЬКО ДЛЯ ADMIN/MANAGER)"""
    user_id = current_user.get("user_id")
    
    # Проверка права на просмотр списка пользователей
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "get-list-user"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: get-list-user"}
        )
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserDTO.model_validate(u) for u in users]


@router.get("/{user_id}/role", response_model=list[RoleDTO])
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """GET /api/ref/user/{user}/role - Получение ролей пользователя"""
    auth_user_id = current_user.get("user_id")
    
    # Проверка: пользователь может видеть ТОЛЬКО свои роли
    # Или админ/менеджер может видеть роли других
    if auth_user_id != user_id:
        # Если пытается посмотреть чужие роли - проверяем право
        if auth_user_id != 1 and not PermissionService.check_permission(db, auth_user_id, "read-user"):
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied. You can only view your own roles"}
            )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role_users = db.query(RoleUser).filter(
        RoleUser.user_id == user_id,
        RoleUser.deleted_at == None
    ).all()
    
    roles = [ru.role for ru in role_users if ru.role]
    return [RoleDTO.model_validate(r) for r in roles]


@router.post("/{user_id}/role/{role_id}", status_code=201)
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/user/{user}/role/{role} - Присвоение роли пользователю"""
    auth_user_id = current_user.get("user_id")
    
    # Только админ или пользователь с правом assign-role-to-user
    if auth_user_id != 1 and not PermissionService.check_permission(db, auth_user_id, "assign-role-to-user"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: assign-role-to-user"}
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    existing = db.query(RoleUser).filter(
        RoleUser.user_id == user_id,
        RoleUser.role_id == role_id
    ).first()
    
    if existing and existing.deleted_at is None:
        raise HTTPException(status_code=400, detail="User already has this role")
    
    if existing and existing.deleted_at is not None:
        existing.deleted_at = None
        existing.deleted_by = None
        db.commit()
        return {"message": f"Role {role.name} restored for user {user.username}"}
    
    role_user = RoleUser(
        user_id=user_id,
        role_id=role_id,
        created_by=auth_user_id
    )
    db.add(role_user)
    db.commit()
    
    return {"message": f"Role {role.name} assigned to user {user.username}"}


@router.delete("/{user_id}/role/{role_id}", status_code=204)
def hard_delete_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/user/{user}/role/{role} - Удаление роли у пользователя"""
    auth_user_id = current_user.get("user_id")
    
    if auth_user_id != 1 and not PermissionService.check_permission(db, auth_user_id, "delete-user-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: delete-user-role"}
        )
    
    role_user = db.query(RoleUser).filter(
        RoleUser.user_id == user_id,
        RoleUser.role_id == role_id
    ).first()
    
    if not role_user:
        raise HTTPException(status_code=404, detail="User does not have this role")
    
    db.delete(role_user)
    db.commit()


@router.delete("/{user_id}/role/{role_id}/soft", status_code=204)
def soft_delete_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/user/{user}/role/{role}/soft - Мягкое удаление роли у пользователя"""
    auth_user_id = current_user.get("user_id")
    
    if auth_user_id != 1 and not PermissionService.check_permission(db, auth_user_id, "delete-user-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: delete-user-role"}
        )
    
    role_user = db.query(RoleUser).filter(
        RoleUser.user_id == user_id,
        RoleUser.role_id == role_id,
        RoleUser.deleted_at == None
    ).first()
    
    if not role_user:
        raise HTTPException(status_code=404, detail="User does not have this role")
    
    role_user.deleted_at = datetime.utcnow()
    role_user.deleted_by = auth_user_id
    db.commit()


@router.post("/{user_id}/role/{role_id}/restore", status_code=200)
def restore_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/user/{user}/role/{role}/restore - Восстановление роли"""
    auth_user_id = current_user.get("user_id")
    
    if auth_user_id != 1 and not PermissionService.check_permission(db, auth_user_id, "restore-user-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: restore-user-role"}
        )
    
    role_user = db.query(RoleUser).filter(
        RoleUser.user_id == user_id,
        RoleUser.role_id == role_id,
        RoleUser.deleted_at != None
    ).first()
    
    if not role_user:
        raise HTTPException(status_code=404, detail="Deleted role not found")
    
    role_user.deleted_at = None
    role_user.deleted_by = None
    db.commit()
    
    return {"message": "Role restored"}
