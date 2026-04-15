"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - Permission Controller                                       ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.permission import Permission
from app.dto.rbac_dto import PermissionDTO, PermissionCollectionDTO
from app.services.permission_service import PermissionService
from app.middlewares.auth_middleware import get_current_user
from app.requests.rbac_requests import StorePermissionRequest, UpdatePermissionRequest
from datetime import datetime

router = APIRouter(tags=["permissions"])


@router.get("", response_model=PermissionCollectionDTO)
def list_permissions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """GET /api/ref/policy/permission - Получение списка разрешений (ТОЛЬКО ДЛЯ ADMIN/MANAGER)"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "get-list-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: get-list-permission"}
        )
    
    permissions = db.query(Permission).filter(Permission.deleted_at == None).offset(skip).limit(limit).all()
    total = db.query(Permission).filter(Permission.deleted_at == None).count()
    
    return PermissionCollectionDTO(
        items=[PermissionDTO.model_validate(p) for p in permissions],
        total=total,
        count=len(permissions)
    )


@router.get("/{permission_id}", response_model=PermissionDTO)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """GET /api/ref/policy/permission/{permission} - Получение конкретного разрешения"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "read-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: read-permission"}
        )
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.deleted_at == None
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return PermissionDTO.model_validate(permission)


@router.post("", response_model=PermissionDTO, status_code=201)
def create_permission(
    request: StorePermissionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/policy/permission - Создание разрешения"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "create-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: create-permission"}
        )
    
    existing = db.query(Permission).filter(Permission.slug == request.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission with this slug already exists")
    
    existing_name = db.query(Permission).filter(Permission.name == request.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Permission with this name already exists")
    
    permission = Permission(
        name=request.name,
        slug=request.slug,
        description=request.description,
        created_by=user_id
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return PermissionDTO.model_validate(permission)


@router.put("/{permission_id}", response_model=PermissionDTO)
def update_permission(
    permission_id: int,
    request: UpdatePermissionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """PUT /api/ref/policy/permission/{permission} - Обновление разрешения"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "update-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: update-permission"}
        )
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.deleted_at == None
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    if request.slug and request.slug != permission.slug:
        existing = db.query(Permission).filter(Permission.slug == request.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Permission with this slug already exists")
    
    if request.name and request.name != permission.name:
        existing = db.query(Permission).filter(Permission.name == request.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Permission with this name already exists")
    
    if request.name:
        permission.name = request.name
    if request.slug:
        permission.slug = request.slug
    if request.description is not None:
        permission.description = request.description
    
    permission.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(permission)
    
    return PermissionDTO.model_validate(permission)


@router.delete("/{permission_id}", status_code=204)
def hard_delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/policy/permission/{permission} - Удаление разрешения"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "delete-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: delete-permission"}
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()


@router.delete("/{permission_id}/soft", status_code=204)
def soft_delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/ref/policy/permission/{permission}/soft - Мягкое удаление разрешения"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "delete-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: delete-permission"}
        )
    
    permission = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.deleted_at == None
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    permission.deleted_at = datetime.utcnow()
    permission.deleted_by = user_id
    db.commit()


@router.post("/{permission_id}/restore", status_code=200)
def restore_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/ref/policy/permission/{permission}/restore - Восстановление разрешения"""
    user_id = current_user.get("user_id")
    
    if user_id != 1 and not PermissionService.check_permission(db, user_id, "restore-permission"):
        return JSONResponse(
            status_code=403,
            content={"error": "Access denied. Required permission: restore-permission"}
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    permission.deleted_at = None
    permission.deleted_by = None
    db.commit()
    
    return {"message": "Permission restored"}
