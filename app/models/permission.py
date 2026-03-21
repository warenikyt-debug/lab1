"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🟢 LAB3: RBAC - Permission Model                                            ║
║                                                                              ║
║ Модель разрешения (Permission) для управления доступом к ресурсам           ║
║ Связь с ролями через таблицу permission_role                                ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship

from app.config.database import Base


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    
    roles = relationship(
        "Role",
        secondary="permission_role",
        back_populates="permissions",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_permission_created_by", "created_by"),
        Index("idx_permission_deleted_at", "deleted_at"),
    )
