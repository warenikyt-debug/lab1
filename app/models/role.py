from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.config.database import Base


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    
    permissions = relationship(
        "Permission",
        secondary="permission_role",
        back_populates="roles",
        lazy="selectin",
        overlaps="role,users"
    )
    
    users = relationship(
        "User",
        secondary="role_user",
        back_populates="roles",
        lazy="selectin",
        overlaps="role,users"
    )
    
    __table_args__ = (
        Index("idx_role_created_by", "created_by"),
        Index("idx_role_deleted_at", "deleted_at"),
    )
