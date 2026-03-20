from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, UniqueConstraint

from app.config.database import Base


class PermissionRole(Base):
    __tablename__ = "permission_role"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("idx_permission_role_role_id", "role_id"),
        Index("idx_permission_role_permission_id", "permission_id"),
        Index("idx_permission_role_deleted_at", "deleted_at"),
    )
