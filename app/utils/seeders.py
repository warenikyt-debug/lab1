from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.permission import Permission
from app.models.permission_role import PermissionRole


def seed_roles(db: Session):
    admin_role = Role(
        name="Admin",
        slug="admin",
        description="Administrator with full access",
        created_by=1
    )
    user_role = Role(
        name="User",
        slug="user",
        description="Regular user with limited access",
        created_by=1
    )
    guest_role = Role(
        name="Guest",
        slug="guest",
        description="Guest user with minimal access",
        created_by=1
    )
    
    db.add(admin_role)
    db.add(user_role)
    db.add(guest_role)
    db.commit()


def seed_permissions(db: Session):
    actions = ["get-list", "read", "create", "update", "delete", "restore"]
    entities = ["user", "role", "permission"]
    
    permissions = []
    for entity in entities:
        for action in actions:
            permission = Permission(
                name=f"{action.capitalize()} {entity.capitalize()}",
                slug=f"{action}-{entity}",
                description=f"Permission to {action} {entity}",
                created_by=1
            )
            permissions.append(permission)
    
    db.add_all(permissions)
    db.commit()


def seed_role_permissions(db: Session):
    admin_role = db.query(Role).filter(Role.slug == "admin").first()
    user_role = db.query(Role).filter(Role.slug == "user").first()
    guest_role = db.query(Role).filter(Role.slug == "guest").first()
    
    all_permissions = db.query(Permission).all()
    
    for permission in all_permissions:
        admin_permission = PermissionRole(
            role_id=admin_role.id,
            permission_id=permission.id,
            created_by=1
        )
        db.add(admin_permission)
    
    user_permissions = db.query(Permission).filter(
        Permission.slug.in_([
            "get-list-user",
            "read-user",
            "update-user"
        ])
    ).all()
    
    for permission in user_permissions:
        user_permission = PermissionRole(
            role_id=user_role.id,
            permission_id=permission.id,
            created_by=1
        )
        db.add(user_permission)
    
    guest_permissions = db.query(Permission).filter(
        Permission.slug.in_(["get-list-user"])
    ).all()
    
    for permission in guest_permissions:
        guest_permission = PermissionRole(
            role_id=guest_role.id,
            permission_id=permission.id,
            created_by=1
        )
        db.add(guest_permission)
    
    db.commit()
