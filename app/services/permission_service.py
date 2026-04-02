"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - Permission Service                                          ║
║                                                                              ║
║ Сервис для проверки разрешений пользователей (Authorization)                ║
║ Основная логика: User → Roles → Permissions                                 ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_user import RoleUser
from app.models.permission_role import PermissionRole
from datetime import datetime


class PermissionService:
    
    @staticmethod
    def check_permission(db: Session, user_id: int, permission_slug: str) -> bool:
        user = db.query(__import__('app.models.user', fromlist=['User']).User).filter(
            __import__('app.models.user', fromlist=['User']).User.id == user_id
        ).first()
        
        if not user:
            return False
        
        permission = db.query(Permission).filter(
            and_(
                Permission.slug == permission_slug,
                Permission.deleted_at == None
            )
        ).first()
        
        if not permission:
            return False
        
        user_role_ids = db.query(RoleUser.role_id).filter(
            and_(
                RoleUser.user_id == user_id,
                RoleUser.deleted_at == None
            )
        ).all()
        
        if not user_role_ids:
            return False
        
        role_ids = [r[0] for r in user_role_ids]
        
        has_permission = db.query(PermissionRole).filter(
            and_(
                PermissionRole.role_id.in_(role_ids),
                PermissionRole.permission_id == permission.id,
                PermissionRole.deleted_at == None
            )
        ).first()
        
        return has_permission is not None
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> list:
        permissions = db.query(Permission).join(
            PermissionRole,
            Permission.id == PermissionRole.permission_id
        ).join(
            Role,
            PermissionRole.role_id == Role.id
        ).join(
            RoleUser,
            Role.id == RoleUser.role_id
        ).filter(
            and_(
                RoleUser.user_id == user_id,
                RoleUser.deleted_at == None,
                Permission.deleted_at == None,
                PermissionRole.deleted_at == None
            )
        ).distinct().all()
        
        return permissions
    
    @staticmethod
    def create_role(db: Session, name: str, slug: str, description: str, created_by: int):
        role = Role(
            name=name,
            slug=slug,
            description=description,
            created_by=created_by
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def update_role(db: Session, role_id: int, name: str, slug: str, description: str):
        role = db.query(Role).filter(
            and_(
                Role.id == role_id,
                Role.deleted_at == None
            )
        ).first()
        
        if not role:
            return None
        
        role.name = name
        role.slug = slug
        role.description = description
        role.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def soft_delete_role(db: Session, role_id: int, user_id: int):
        role = db.query(Role).filter(
            and_(
                Role.id == role_id,
                Role.deleted_at == None
            )
        ).first()
        
        if not role:
            return False
        
        role.deleted_at = datetime.utcnow()
        role.deleted_by = user_id
        db.commit()
        return True
    
    @staticmethod
    def restore_role(db: Session, role_id: int):
        role = db.query(Role).filter(Role.id == role_id).first()
        
        if not role:
            return False
        
        role.deleted_at = None
        role.deleted_by = None
        db.commit()
        return True
    
    @staticmethod
    def hard_delete_role(db: Session, role_id: int):
        role = db.query(Role).filter(Role.id == role_id).first()
        
        if not role:
            return False
        
        db.delete(role)
        db.commit()
        return True
