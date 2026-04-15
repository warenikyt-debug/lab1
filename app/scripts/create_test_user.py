#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.role_user import RoleUser
import hashlib
import bcrypt

def create_test_user():
    db = SessionLocal()
    
    try:
        username = "TestUser1"
        email = "testuser@example.com"
        password = "Test123!@#"
        
        # Hash password
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(sha256_hash.encode('utf-8'), salt).decode('utf-8')
        
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User {username} already exists")
            return
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            birthday="2000-01-01"
        )
        db.add(user)
        db.flush()
        
        # Assign User role
        user_role = db.query(Role).filter(Role.slug == "user").first()
        if user_role:
            ru = RoleUser(user_id=user.id, role_id=user_role.id, created_by=user.id)
            db.add(ru)
            print(f"Assigned User role to {username}")
        
        db.commit()
        print(f"Test user created: {username} / {password}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
