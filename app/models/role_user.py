from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, UniqueConstraint

from app.config.database import Base


class RoleUser(Base):
    __tablename__ = "role_user"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        Index("idx_role_user_user_id", "user_id"),
        Index("idx_role_user_role_id", "role_id"),
        Index("idx_role_user_deleted_at", "deleted_at"),
    )
