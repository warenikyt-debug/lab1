"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - Role Controller                                             ║
║                                                                              ║
║ Контроллер для управления ролями (RBAC).                                    ║
║ Реализует CRUD операции с ролями и поддерживает мягкое удаление.            ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.role import Role
from app.dto.rbac_dto import RoleDTO, RoleCollectionDTO
from app.services.permission_service import PermissionService
from app.middlewares.auth_middleware import get_current_user
from app.requests.rbac_requests import StoreRoleRequest, UpdateRoleRequest
from datetime import datetime

router = APIRouter(tags=["roles"])


@router.get("", response_model=RoleCollectionDTO)
def list_roles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """GET /api/ref/policy/role - Получение списка ролей (только активные)"""
    try:
        roles = db.query(Role).filter(Role.deleted_at == None).offset(skip).limit(limit).all()
        total = db.query(Role).filter(Role.deleted_at == None).count()
        
        return RoleCollectionDTO(
            items=[RoleDTO.from_orm(role) for role in roles],
            total=total,
            count=len(roles)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")


@router.get("/{role_id}", response_model=RoleDTO)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """GET /api/ref/policy/role/{role} - Получение конкретной роли"""
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.deleted_at == None
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    return RoleDTO.from_orm(role)


@router.post("", response_model=RoleDTO, status_code=201)
def create_role(
    request: StoreRoleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/policy/role - Создание роли"""
    user_id = current_user.get("user_id")
    
    # Проверка разрешения (create-role)
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "create-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: create-role"}
        )
    
    # Проверка уникальности slug
    existing = db.query(Role).filter(Role.slug == request.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Роль с таким slug уже существует")
    
    # Проверка уникальности name
    existing_name = db.query(Role).filter(Role.name == request.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")
    
    role = PermissionService.create_role(db, request.name, request.slug, request.description, user_id)
    return RoleDTO.from_orm(role)


@router.put("/{role_id}", response_model=RoleDTO)
def update_role(
    role_id: int,
    request: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """PUT /api/ref/policy/role/{role} - Обновление роли"""
    user_id = current_user.get("user_id")
    
    # Проверка разрешения (update-role)
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "update-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: update-role"}
        )
    
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.deleted_at == None
    ).first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    # Проверка уникальности slug при обновлении
    if request.slug and request.slug != role.slug:
        existing = db.query(Role).filter(Role.slug == request.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Роль с таким slug уже существует")
    
    # Проверка уникальности name при обновлении
    if request.name and request.name != role.name:
        existing = db.query(Role).filter(Role.name == request.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")
    
    # Обновление только переданных полей
    if request.name:
        role.name = request.name
    if request.slug:
        role.slug = request.slug
    if request.description is not None:
        role.description = request.description
    
    role.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(role)
    
    return RoleDTO.from_orm(role)


@router.delete("/{role_id}", status_code=204)
def hard_delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/policy/role/{role} - Жёсткое удаление роли"""
    user_id = current_user.get("user_id")
    
    # Проверка разрешения (delete-role)
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "delete-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: delete-role"}
        )
    
    success = PermissionService.hard_delete_role(db, role_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Роль не найдена")


@router.delete("/{role_id}/soft", status_code=204)
def soft_delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/policy/role/{role}/soft - Мягкое удаление роли"""
    user_id = current_user.get("user_id")
    
    # Проверка разрешения (delete-role)
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "delete-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: delete-role"}
        )
    
    success = PermissionService.soft_delete_role(db, role_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Роль не найдена")


@router.post("/{role_id}/restore", status_code=200)
def restore_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/policy/role/{role}/restore - Восстановление мягко удалённой роли"""
    user_id = current_user.get("user_id")
    
    # Проверка разрешения (restore-role)
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "restore-role"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: restore-role"}
        )
    
    success = PermissionService.restore_role(db, role_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Удалённая роль не найдена")
    
    return {"message": "Роль восстановлена"}
