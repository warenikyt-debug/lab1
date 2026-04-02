"""Сервис для работы с токенами в БД"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.token import Token, TokenPair


class TokenRepository:
    """Репозиторий для работы с токенами в БД"""
    
    @staticmethod
    def create_token(db: Session, token_id: str, token_value: str, token_type: str,
                     user_id: int, expires_at: datetime, ip_address: Optional[str] = None) -> Token:
        """Создать токен в БД"""
        token = Token(
            id=token_id,
            token_value=token_value,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token
    
    @staticmethod
    def create_token_pair(db: Session, access_token_id: str, refresh_token_id: str, 
                         user_id: int) -> TokenPair:
        """Связать access и refresh токены"""
        pair = TokenPair(
            access_token_id=access_token_id,
            refresh_token_id=refresh_token_id,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        db.add(pair)
        db.commit()
        db.refresh(pair)
        return pair
    
    @staticmethod
    def get_token_by_id(db: Session, token_id: str) -> Optional[Token]:
        """Получить токен по ID"""
        return db.query(Token).filter(Token.id == token_id).first()
    
    @staticmethod
    def get_active_tokens(db: Session, user_id: int) -> List[Token]:
        """Получить все активные токены пользователя"""
        return db.query(Token).filter(
            Token.user_id == user_id,
            Token.is_blacklisted == False,
            Token.expires_at > datetime.utcnow()
        ).all()
    
    @staticmethod
    def get_active_token_pairs(db: Session, user_id: int) -> List[TokenPair]:
        """Получить все активные пары токенов пользователя"""
        return db.query(TokenPair).join(Token, Token.id == TokenPair.access_token_id).filter(
            TokenPair.user_id == user_id,
            Token.is_blacklisted == False,
            Token.expires_at > datetime.utcnow()
        ).all()
    
    @staticmethod
    def blacklist_token(db: Session, token_id: str):
        """Добавить токен в черный список"""
        token = db.query(Token).filter(Token.id == token_id).first()
        if token:
            token.is_blacklisted = True
            token.blacklisted_at = datetime.utcnow()
            db.commit()
        return token
    
    @staticmethod
    def blacklist_token_pair(db: Session, pair_id: int):
        """Добавить обе токена пары в черный список"""
        pair = db.query(TokenPair).filter(TokenPair.id == pair_id).first()
        if pair:
            TokenRepository.blacklist_token(db, pair.access_token_id)
            TokenRepository.blacklist_token(db, pair.refresh_token_id)
        return pair
    
    @staticmethod
    def get_oldest_token_pair(db: Session, user_id: int) -> Optional[TokenPair]:
        """Получить самую старую пару токенов"""
        pair = db.query(TokenPair).filter(
            TokenPair.user_id == user_id
        ).join(Token, Token.id == TokenPair.access_token_id).filter(
            Token.is_blacklisted == False,
            Token.expires_at > datetime.utcnow()
        ).order_by(TokenPair.created_at).first()
        return pair
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """Очистить истекшие токены"""
        now = datetime.utcnow()
        expired = db.query(Token).filter(Token.expires_at < now).all()
        count = len(expired)
        for token in expired:
            db.delete(token)
        db.commit()
        return count
