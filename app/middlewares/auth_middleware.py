from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from app.services.token_service import token_service  # ← тот же экземпляр!

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Получение текущего пользователя из токена
    """
    print(f"\n🔍 MIDDLEWARE: проверка токена {credentials.credentials[:20]}...")
    
    payload = token_service.verify_token(credentials.credentials, "access")
    if not payload:
        print("❌ MIDDLEWARE: токен недействителен")
        raise HTTPException(
            status_code=401,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    print(f"✅ MIDDLEWARE: токен действителен, user_id: {payload.get('user_id')}")
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