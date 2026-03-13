from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from app.services.token_service import TokenService

security = HTTPBearer()
token_service = TokenService()

async def get_current_user(token: str = Depends(security)) -> Dict:
    """
    Получение текущего пользователя из токена
    """
    payload = token_service.verify_token(token.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload

async def get_current_user_optional(request: Request) -> Optional[Dict]:
    """
    Опциональное получение пользователя (для публичных маршрутов)
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    return token_service.verify_token(token, "access")