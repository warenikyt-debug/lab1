from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base


class Token(Base):
    """Модель для хранения токенов в БД"""
    __tablename__ = "tokens"
    
    id = Column(String(36), primary_key=True)  # UUID
    token_value = Column(String(500), nullable=False, unique=True)
    token_type = Column(String(10), nullable=False)  # 'access' или 'refresh'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(50))
    is_blacklisted = Column(Boolean, default=False)
    blacklisted_at = Column(DateTime)
    
    user = relationship("User", back_populates="tokens")
    
    __table_args__ = (
        Index('idx_tokens_user_id', 'user_id'),
        Index('idx_tokens_expires_at', 'expires_at'),
        Index('idx_tokens_is_blacklisted', 'is_blacklisted'),
    )


class TokenPair(Base):
    """Модель для связи access и refresh токенов"""
    __tablename__ = "token_pairs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    access_token_id = Column(String(36), ForeignKey('tokens.id'), nullable=False)
    refresh_token_id = Column(String(36), ForeignKey('tokens.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    access_token = relationship("Token", foreign_keys=[access_token_id])
    refresh_token = relationship("Token", foreign_keys=[refresh_token_id])
    user = relationship("User", back_populates="token_pairs")
    
    __table_args__ = (
        Index('idx_token_pairs_user_id', 'user_id'),
    )
