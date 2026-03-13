from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from ..requests.auth_requests import LoginRequest, RegisterRequest, ChangePasswordRequest
from ..services.auth_service import AuthService
from ..services.token_service import TokenService
from ..dto.auth_dto import AuthSuccessDTO, TokenListDTO
from ..dto.user_dto import UserDTO
from ..middlewares.auth_middleware import get_current_user, get_current_user_optional

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()
token_service = TokenService()

@router.post("/login", response_model=AuthSuccessDTO)
async def login(request: Request, login_data: LoginRequest):
    """
    Авторизация пользователя
    POST /api/auth/login
    Доступ: открыто для всех
    """
    dto = login_data.to_dto()
    
    result = auth_service.login(
        username=dto.username,
        password=dto.password,
        ip_address=request.client.host if request.client else None
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    return AuthSuccessDTO(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=result["user"]
    )

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserDTO)
async def register(register_data: RegisterRequest):
    """
    Регистрация нового пользователя
    POST /api/auth/register
    Доступ: только для неавторизованных
    """
    try:
        dto = register_data.to_dto()
        user = auth_service.register(dto)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserDTO)
async def get_me(user_data: dict = Depends(get_current_user)):
    """
    Информация о текущем пользователе
    GET /api/auth/me
    Доступ: только для авторизованных
    """
    user_id = user_data.get("user_id")
    db_user = auth_service.get_user_by_id(user_id)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return UserDTO(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        birthday=db_user.birthday,
        created_at=db_user.created_at
    )

@router.post("/out")
async def logout(request: Request, user_data: dict = Depends(get_current_user)):
    """
    Разлогирование (выход)
    POST /api/auth/out
    Доступ: только для авторизованных
    """
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "")
    
    payload = token_service.verify_token(token, "access")
    if payload:
        token_id = payload.get("token_id")
        token_service.revoke_token(token_id)
    
    return {"message": "Успешный выход из системы"}

@router.get("/tokens", response_model=TokenListDTO)
async def get_tokens(user_data: dict = Depends(get_current_user)):
    """
    Список активных токенов пользователя
    GET /api/auth/tokens
    Доступ: только для авторизованных
    """
    user_id = user_data.get("user_id")
    tokens = token_service.get_user_active_tokens(user_id)
    
    return TokenListDTO(tokens=tokens)

@router.post("/out_all")
async def logout_all(request: Request, user_data: dict = Depends(get_current_user)):
    """
    Разлогирование со всех устройств
    POST /api/auth/out_all
    Доступ: только для авторизованных
    """
    user_id = user_data.get("user_id")
    
    auth_header = request.headers.get("Authorization")
    current_token = auth_header.replace("Bearer ", "")
    current_payload = token_service.verify_token(current_token, "access")
    current_token_id = current_payload.get("token_id") if current_payload else None
    
    token_service.revoke_all_user_tokens(user_id, current_token_id)
    
    return {"message": "Все сеансы, кроме текущего, завершены"}

@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Обновление токена доступа
    POST /api/auth/refresh
    Доступ: только с действительным refresh токеном
    """
    data = await request.json()
    refresh_token = data.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указан refresh токен"
        )
    
    result = token_service.refresh_tokens(
        refresh_token,
        ip_address=request.client.host if request.client else None
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный refresh токен"
        )
    
    return result

@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    user_data: dict = Depends(get_current_user)
):
    """
    Изменение пароля
    POST /api/auth/change-password
    Доступ: только для авторизованных
    """
    user_id = user_data.get("user_id")
    
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль и подтверждение не совпадают"
        )
    
    success = auth_service.change_password(
        user_id,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    auth_header = request.headers.get("Authorization")
    current_token = auth_header.replace("Bearer ", "")
    current_payload = token_service.verify_token(current_token, "access")
    current_token_id = current_payload.get("token_id") if current_payload else None
    
    token_service.revoke_all_user_tokens(user_id, current_token_id)
    
    return {"message": "Пароль успешно изменен"}