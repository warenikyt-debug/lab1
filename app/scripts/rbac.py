#!/usr/bin/env python
"""
Initialize RBAC system with default roles and permissions
Run: python -m app.scripts.init_rbac
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.database import SessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.models.permission_role import PermissionRole
from app.models.user import User
from app.models.role_user import RoleUser

def init_rbac():
    db = SessionLocal()
    
    try:
        print("=" * 50)
        print("RBAC INITIALIZATION")
        print("=" * 50)
        
        # Create default roles
        roles_data = [
            {"name": "Admin", "slug": "admin", "description": "Full system access"},
            {"name": "Manager", "slug": "manager", "description": "Manage users and roles"},
            {"name": "User", "slug": "user", "description": "Regular user access"},
            {"name": "Guest", "slug": "guest", "description": "Read-only access"}
        ]
        
        created_roles = {}
        for role_data in roles_data:
            existing = db.query(Role).filter(Role.slug == role_data["slug"]).first()
            if not existing:
                role = Role(
                    name=role_data["name"],
                    slug=role_data["slug"],
                    description=role_data["description"],
                    created_by=1
                )
                db.add(role)
                db.flush()
                created_roles[role_data["slug"]] = role
                print(f"  Created role: {role_data['name']}")
            else:
                created_roles[role_data["slug"]] = existing
                print(f"  Role exists: {role_data['name']}")
        
        # Create default permissions
        entities = ["user", "role", "permission"]
        actions = ["get-list", "read", "create", "update", "delete", "restore"]
        
        permissions_data = []
        for entity in entities:
            for action in actions:
                permissions_data.append({
                    "name": f"{action.capitalize()} {entity.capitalize()}",
                    "slug": f"{action}-{entity}",
                    "description": f"Permission to {action} {entity}"
                })
        
        created_permissions = {}
        for perm_data in permissions_data:
            existing = db.query(Permission).filter(Permission.slug == perm_data["slug"]).first()
            if not existing:
                perm = Permission(
                    name=perm_data["name"],
                    slug=perm_data["slug"],
                    description=perm_data["description"],
                    created_by=1
                )
                db.add(perm)
                db.flush()
                created_permissions[perm_data["slug"]] = perm
                print(f"  Created permission: {perm_data['name']}")
            else:
                created_permissions[perm_data["slug"]] = existing
        
        db.commit()
        
        # Assign permissions to roles
        admin_role = created_roles.get("admin")
        manager_role = created_roles.get("manager")
        user_role = created_roles.get("user")
        guest_role = created_roles.get("guest")
        
        all_permissions = db.query(Permission).all()
        
        # Admin gets all permissions
        if admin_role:
            for perm in all_permissions:
                existing = db.query(PermissionRole).filter(
                    PermissionRole.role_id == admin_role.id,
                    PermissionRole.permission_id == perm.id
                ).first()
                if not existing:
                    pr = PermissionRole(role_id=admin_role.id, permission_id=perm.id, created_by=1)
                    db.add(pr)
            print("  Admin: assigned all permissions")
        
        # Manager gets user and role management permissions
        if manager_role:
            manager_perms = ["get-list-user", "read-user", "create-user", "update-user", 
                            "get-list-role", "read-role", "assign-role-to-user"]
            for perm_slug in manager_perms:
                perm = db.query(Permission).filter(Permission.slug == perm_slug).first()
                if perm:
                    existing = db.query(PermissionRole).filter(
                        PermissionRole.role_id == manager_role.id,
                        PermissionRole.permission_id == perm.id
                    ).first()
                    if not existing:
                        pr = PermissionRole(role_id=manager_role.id, permission_id=perm.id, created_by=1)
                        db.add(pr)
            print("  Manager: assigned management permissions")
        
        # User gets basic self-management permissions
        if user_role:
            user_perms = ["get-list-user", "read-user", "update-user"]
            for perm_slug in user_perms:
                perm = db.query(Permission).filter(Permission.slug == perm_slug).first()
                if perm:
                    existing = db.query(PermissionRole).filter(
                        PermissionRole.role_id == user_role.id,
                        PermissionRole.permission_id == perm.id
                    ).first()
                    if not existing:
                        pr = PermissionRole(role_id=user_role.id, permission_id=perm.id, created_by=1)
                        db.add(pr)
            print("  User: assigned basic permissions")
        
        # Guest gets read-only permissions
        if guest_role:
            guest_perms = ["get-list-user", "read-user"]
            for perm_slug in guest_perms:
                perm = db.query(Permission).filter(Permission.slug == perm_slug).first()
                if perm:
                    existing = db.query(PermissionRole).filter(
                        PermissionRole.role_id == guest_role.id,
                        PermissionRole.permission_id == perm.id
                    ).first()
                    if not existing:
                        pr = PermissionRole(role_id=guest_role.id, permission_id=perm.id, created_by=1)
                        db.add(pr)
            print("  Guest: assigned read-only permissions")
        
        db.commit()
        
        # Assign admin role to existing admin user (id=1)
        admin_user = db.query(User).filter(User.id == 1).first()
        if admin_user and admin_role:
            existing = db.query(RoleUser).filter(
                RoleUser.user_id == admin_user.id,
                RoleUser.role_id == admin_role.id
            ).first()
            if not existing:
                ru = RoleUser(user_id=admin_user.id, role_id=admin_role.id, created_by=1)
                db.add(ru)
                print(f"  Assigned Admin role to user: {admin_user.username}")
        
        db.commit()
        
        print("=" * 50)
        print("RBAC initialization complete!")
        print("=" * 50)
        
        # Summary
        print(f"\nRoles: {db.query(Role).count()}")
        print(f"Permissions: {db.query(Permission).count()}")
        print(f"Role-Permission assignments: {db.query(PermissionRole).count()}")
        print(f"User-Role assignments: {db.query(RoleUser).count()}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_rbac()