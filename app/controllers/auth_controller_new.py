from fastapi import APIRouter, HTTPException, Request, status
from ..requests.auth_requests import LoginRequest, RegisterRequest, ChangePasswordRequest
from ..services.auth_service import AuthService
from ..services.token_service import TokenService
from ..dto.auth_dto import AuthSuccessDTO, UserDTO
from datetime import date

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()
token_service = TokenService()

@router.post("/login", response_model=AuthSuccessDTO)
async def login(request: Request, login_data: LoginRequest):
    """Login endpoint"""
    dto = login_data.to_dto()
    
    result = auth_service.login(
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
        return auth_service.register(register_data.to_dto())
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
    payload = token_service.verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный или истекший токен")
    
    user_id = payload.get("user_id")
    
    # Get user data
    user_data = auth_service.get_user_by_id(user_id)
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
        
        result = token_service.refresh_tokens(
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
    """Logout endpoint - revoke access token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нет токена")
    
    token = auth_header.replace("Bearer ", "")
    
    # Verify and revoke token
    payload = token_service.verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Недействительный или истекший токен")
    
    token_id = payload.get("token_id")
    token_service.revoke_token(token_id)
    
    return {"message": "Успешно вышли из системы"}
