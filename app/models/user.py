"""SQLAlchemy ORM User model."""
from datetime import datetime, date
from typing import Optional
import hashlib
import bcrypt
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session
from ..config.database import Base, SessionLocal, init_db as init_database


class User(Base):
    """SQLAlchemy ORM User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    birthday = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        return bcrypt.checkpw(sha256_hash.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA256 + bcrypt."""
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(sha256_hash.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'birthday': self.birthday,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_db():
    """Initialize the database with all tables."""
    init_database()


def save_user(username: str, email: str, password_hash: str, birthday: str) -> int:
    """Save a new user to the database."""
    db = SessionLocal()
    try:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            birthday=birthday if isinstance(birthday, str) else birthday.isoformat()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    except Exception as e:
        db.rollback()
        if "UNIQUE constraint failed" in str(e):
            raise ValueError("Пользователь с таким именем или email уже существует")
        raise
    finally:
        db.close()


def find_user_by_username(username: str) -> Optional[dict]:
    """Find a user by username."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def find_user_by_email(email: str) -> Optional[dict]:
    """Find a user by email."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def find_user_by_id(user_id: int) -> Optional[dict]:
    """Find a user by ID."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.to_dict() if user else None
    finally:
        db.close()


def get_all_users() -> list:
    """Get all users from the database."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [user.to_dict() for user in users]
    finally:
        db.close()


def update_user_password(user_id: int, new_password_hash: str) -> bool:
    """Update a user's password."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.password_hash = new_password_hash
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()