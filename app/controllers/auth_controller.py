"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🔵 LAB2: AUTHENTICATION & JWT - Auth Controller                              ║
║                                                                              ║
║ API контроллер для управления аутентификацией пользователей                 ║
║ Эндпоинты: login, register, me, refresh, logout, tokens, out_all            ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import APIRouter, HTTPException, Request, status
from ..requests.auth_requests import LoginRequest, RegisterRequest, ChangePasswordRequest
from ..services.auth_service import AuthService
from ..services.token_service import TokenService
from ..dto.auth_dto import AuthSuccessDTO, UserDTO, TokenListDTO
from datetime import date

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Ленивые инициализаторы (создаются при первом обращении после инициализации БД)
_auth_service_instance = None
_token_service_instance = None

def get_auth_service():
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance

def get_token_service():
    global _token_service_instance
    if _token_service_instance is None:
        _token_service_instance = TokenService()
    return _token_service_instance

@router.post("/login", response_model=AuthSuccessDTO)
async def login(request: Request, login_data: LoginRequest):
    """Login endpoint"""
    dto = login_data.to_dto()
    
    result = get_auth_service().login(
        username=dto.username,
        password=dto.password,
        ip_address=request.client.host if request.client else None
    )
    
    if not result:
        raise HTTPException(status_code=401, detail="Неверное имя или пароль")
    
    return AuthSuccessDTO(**result)

@router.post("/register", status_code=201, response_model=UserDTO)
async def register(register_data: RegisterRequest):
    """Register endpoint"""
    try:
        user_data = get_auth_service().register(register_data.to_dto())
        return UserDTO(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            birthday=date.fromisoformat(user_data['birthday']),
            created_at=user_data['created_at']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserDTO)
async def get_me(request: Request):
    """Get current user profile"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = auth_header.replace("Bearer ", "")
    
    # Verify token
    payload = get_token_service().verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный или истекший токен")
    
    user_id = payload.get("user_id")
    
    # Get user data
    user_data = get_auth_service().get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserDTO(
        id=user_data['id'],
        username=user_data['username'],
        email=user_data['email'],
        birthday=date.fromisoformat(user_data['birthday']),
        created_at=user_data['created_at']
    )

@router.post("/refresh")
async def refresh(request: Request):
    """Refresh token pair"""
    try:
        data = await request.json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token не предоставлен")
        
        result = get_token_service().refresh_tokens(
            refresh_token=refresh_token,
            ip_address=request.client.host if request.client else None
        )
        
        if not result:
            raise HTTPException(status_code=401, detail="Недействительный refresh token")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
async def logout(request: Request):
    """Logout endpoint - revoke access token and paired refresh token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = auth_header.replace("Bearer ", "")
    
    # Verify token
    payload = get_token_service().verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный или истекший токен")
    
    token_id = payload.get("token_id")
    # Revoke both access and refresh tokens
    get_token_service().revoke_token_pair(token_id)
    
    return {"message": "Успешно вышли из системы"}

@router.get("/tokens", response_model=TokenListDTO)
async def get_tokens(request: Request):
    """
    Получение списка активных токенов пользователя
    
    ИСТОЧНИК: app/services/get_token_service().py::get_user_active_tokens()
    Возвращает: TokenListDTO с метаданными всех активных токенов (без самих токенов)
    """
    # Проверка авторизации - извлечение токена из заголовка
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = auth_header.replace("Bearer ", "")
    
    # Проверка действительности токена
    payload = get_token_service().verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный или истекший токен")
    
    user_id = payload.get("user_id")
    
    # Получение всех активных токенов пользователя
    tokens = get_token_service().get_user_active_tokens(user_id)
    
    return TokenListDTO(tokens=tokens)

@router.post("/out_all")
async def logout_all(request: Request):
    """
    Разлогирование со всех устройств (отзыв всех активных токенов)
    
    ИСТОЧНИК: app/services/get_token_service().py::revoke_all_user_tokens()
    Отзывает: все access и refresh токены для текущего пользователя
    Безопасность: используется для выхода из всех сессий одновременно
    """
    # Проверка авторизации - извлечение токена из заголовка
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = auth_header.replace("Bearer ", "")
    
    # Проверка действительности токена
    payload = get_token_service().verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный или истекший токен")
    
    user_id = payload.get("user_id")
    
    # Отзываем все токены пользователя (включая текущий)
    get_token_service().revoke_all_user_tokens(user_id)
    
    return {"message": "Вы вышли со всех устройств"}
