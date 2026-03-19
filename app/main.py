from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, date, timedelta
import json
import os
import bcrypt
import uuid
import jwt
import logging
from typing import Optional, Dict, List
from app.models.user import init_db
from app.controllers.auth_controller import router as auth_router

# ==================== НАСТРОЙКИ ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lab2")

# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================
init_db()
logger.info("✅ База данных инициализирована")

# ==================== НАСТРОЙКИ ====================
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 10080
MAX_ACTIVE_TOKENS = 5  # ← ЛИМИТ ТОКЕНОВ

logger.info("🚀 Сервер запускается...")
logger.info(f"🔑 Максимум токенов на пользователя: {MAX_ACTIVE_TOKENS}")

# ==================== ХРАНИЛИЩЕ ====================
DATA_FILE = "/workspaces/lab1/data/users.json"
TOKENS_FILE = "/workspaces/lab1/data/tokens.json"

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)
    logger.info(f"💾 Сохранено {len(users)} пользователей")

def load_tokens():
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"active": {}, "blacklist": [], "user_tokens": {}}
    return {"active": {}, "blacklist": [], "user_tokens": {}}

def save_tokens(tokens_data):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens_data, f, indent=2)

# Загружаем данные
users_db = load_users()
tokens_db = load_tokens()
logger.info(f"📊 Загружено пользователей: {len(users_db)}")
logger.info(f"📊 Активных токенов: {len(tokens_db['active'])}")
logger.info(f"📊 Токенов в черном списке: {len(tokens_db['blacklist'])}")

# ==================== МОДЕЛИ ====================
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    c_password: str
    birthday: date
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v) < 7:
            raise ValueError('Минимум 7 символов')
        if not v[0].isupper():
            raise ValueError('Первая буква заглавная')
        if not v.isalnum():
            raise ValueError('Только буквы и цифры')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        errors = []
        if len(v) < 8: errors.append('8+ символов')
        if not any(c.isdigit() for c in v): errors.append('цифру')
        if not any(not c.isalnum() for c in v): errors.append('спецсимвол')
        if not any(c.isupper() for c in v): errors.append('заглавную букву')
        if errors:
            raise ValueError(f'Пароль должен содержать: {", ".join(errors)}')
        return v
    
    @validator('c_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    birthday: str
    created_at: str

# ==================== ТОКЕН СЕРВИС ====================
class TokenService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_ttl = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_ttl = REFRESH_TOKEN_EXPIRE_MINUTES
        self.max_tokens = MAX_ACTIVE_TOKENS
        
        # Загружаем данные из файла
        self.active_tokens = tokens_db.get("active", {})
        self.blacklist = set(tokens_db.get("blacklist", []))
        self.user_tokens = tokens_db.get("user_tokens", {})
        
        # Преобразуем ключи user_tokens в int
        self.user_tokens = {int(k): v for k, v in self.user_tokens.items()}
        
        logger.info(f"🔧 TokenService инициализирован")
    
    def _save(self):
        """Сохраняем состояние в файл"""
        tokens_db["active"] = self.active_tokens
        tokens_db["blacklist"] = list(self.blacklist)
        tokens_db["user_tokens"] = self.user_tokens
        save_tokens(tokens_db)
    
    def _generate_token_id(self) -> str:
        return str(uuid.uuid4())
    
    def _create_jwt_token(self, user_id: int, token_type: str, ttl_minutes: int, token_id: str) -> str:
        expires = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        payload = {
            "user_id": user_id,
            "type": token_type,
            "token_id": token_id,
            "exp": expires.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _revoke_oldest_token(self, user_id: int):
        """Отзыв самого старого токена пользователя"""
        if str(user_id) not in self.user_tokens:
            return
        
        # Получаем все access токены пользователя
        user_token_ids = self.user_tokens[str(user_id)]
        access_tokens = []
        
        for token_id in user_token_ids:
            if token_id in self.active_tokens and token_id not in self.blacklist:
                token_info = self.active_tokens[token_id]
                if token_info["type"] == "access":
                    created = datetime.fromisoformat(token_info["created_at"])
                    access_tokens.append((created, token_id))
        
        # Сортируем по дате создания (самые старые первые)
        access_tokens.sort(key=lambda x: x[0])
        
        # Если превышен лимит, отзываем самые старые
        while len(access_tokens) >= self.max_tokens:
            oldest_created, oldest_token = access_tokens.pop(0)
            logger.warning(f"⚠️ Отзываем старый токен: {oldest_token[:8]}... (создан: {oldest_created})")
            self.revoke_token(oldest_token)
    
    def create_token_pair(self, user_id: int, ip_address: str = None) -> Dict[str, str]:
        logger.info(f"🔑 Создание токенов для user {user_id}")
        
        # Проверка и отзыв старых токенов при превышении лимита
        self._revoke_oldest_token(user_id)
        
        # Генерация ID токенов
        access_token_id = self._generate_token_id()
        refresh_token_id = self._generate_token_id()
        
        access_token = self._create_jwt_token(user_id, "access", self.access_ttl, access_token_id)
        refresh_token = self._create_jwt_token(user_id, "refresh", self.refresh_ttl, refresh_token_id)
        
        now = datetime.utcnow()
        
        # Сохраняем access токен
        self.active_tokens[access_token_id] = {
            "user_id": user_id,
            "type": "access",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=self.access_ttl)).isoformat(),
            "ip_address": ip_address
        }
        
        # Сохраняем refresh токен
        self.active_tokens[refresh_token_id] = {
            "user_id": user_id,
            "type": "refresh",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=self.refresh_ttl)).isoformat(),
            "ip_address": ip_address
        }
        
        # Обновляем список токенов пользователя
        user_key = str(user_id)
        if user_key not in self.user_tokens:
            self.user_tokens[user_key] = []
        
        self.user_tokens[user_key].extend([access_token_id, refresh_token_id])
        
        self._save()
        logger.info(f"✅ Токены созданы: access={access_token_id[:8]}..., refresh={refresh_token_id[:8]}...")
        logger.info(f"📊 У пользователя {user_id} теперь {len([t for t in self.user_tokens[user_key] if t in self.active_tokens and t not in self.blacklist])} активных токенов")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    def verify_token(self, token: str, expected_type: str = None) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("token_id")
            token_type = payload.get("type")
            
            logger.debug(f"🔍 Проверка токена: {token_id[:8]}...")
            
            # Проверка черного списка
            if token_id in self.blacklist:
                logger.warning(f"❌ Токен в черном списке: {token_id[:8]}...")
                return None
            
            if expected_type and token_type != expected_type:
                logger.warning(f"❌ Неверный тип токена")
                return None
            
            if token_id not in self.active_tokens:
                logger.warning(f"❌ Токен не найден: {token_id[:8]}...")
                return None
            
            exp = datetime.fromtimestamp(payload.get("exp"))
            if exp < datetime.utcnow():
                logger.warning(f"❌ Токен истек")
                self.revoke_token(token_id)
                return None
            
            return payload
            
        except jwt.PyJWTError as e:
            logger.error(f"❌ Ошибка JWT: {e}")
            return None
    
    def revoke_token(self, token_id: str):
        """Отзыв токена"""
        logger.info(f"🔴 Отзыв токена: {token_id[:8]}...")
        
        # Добавляем в черный список
        self.blacklist.add(token_id)
        
        # Удаляем из активных
        if token_id in self.active_tokens:
            user_id = self.active_tokens[token_id]["user_id"]
            del self.active_tokens[token_id]
            
            # Удаляем из списка пользователя
            user_key = str(user_id)
            if user_key in self.user_tokens and token_id in self.user_tokens[user_key]:
                self.user_tokens[user_key].remove(token_id)
            
            logger.info(f"✅ Токен удален из активных")
        
        self._save()
    
    def revoke_token_by_value(self, token_value: str):
        """Отзыв токена по его значению"""
        try:
            payload = jwt.decode(token_value, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("token_id")
            self.revoke_token(token_id)
            return True
        except:
            return False
    
    def get_user_tokens(self, user_id: int) -> List[Dict]:
        """Получение списка активных токенов пользователя"""
        tokens = []
        user_key = str(user_id)
        
        if user_key in self.user_tokens:
            for token_id in self.user_tokens[user_key]:
                if token_id in self.active_tokens and token_id not in self.blacklist:
                    token_data = self.active_tokens[token_id]
                    if token_data["type"] == "access":  # Показываем только access токены
                        tokens.append({
                            "id": token_id[:8] + "...",
                            "created_at": token_data["created_at"],
                            "expires_at": token_data["expires_at"],
                            "ip": token_data.get("ip_address", "unknown"),
                            "type": token_data["type"]
                        })
        
        # Сортируем по дате создания (новые первые)
        tokens.sort(key=lambda x: x["created_at"], reverse=True)
        return tokens

# Создаем сервис
token_service = TokenService()
security = HTTPBearer()

# ==================== MIDDLEWARE ====================
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = token_service.verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return payload

# ==================== API РОУТЕР ====================
# Импортирован из app.controllers.auth_controller


# ==================== HTML СТРАНИЦЫ ====================
app = FastAPI(title="Lab2 - Авторизация с лимитом токенов")
app.include_router(auth_router)

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Лабораторная работа №2</title>
        <style>
            body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; }}
            .links {{ margin: 20px 0; }}
            .links a {{ 
                display: inline-block; 
                margin: 10px; 
                padding: 10px 20px; 
                background: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px; 
            }}
            .stats {{ 
                background: #f5f5f5; 
                padding: 20px; 
                border-radius: 10px; 
                margin-top: 20px; 
            }}
            .limit-info {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
                color: #856404;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <h1>🔐 Лабораторная работа №2</h1>
        <h2>Авторизация с лимитом токенов (макс {MAX_ACTIVE_TOKENS})</h2>
        
        <div class="limit-info">
            <strong>ℹ️ Лимит активных сессий:</strong> Не более {MAX_ACTIVE_TOKENS} одновременных входов
        </div>
        
        <div class="links">
            <a href="/register">📝 Регистрация</a>
            <a href="/login">🔑 Вход</a>
            <a href="/profile">👤 Профиль</a>
            <a href="/docs">📚 Swagger</a>
        </div>
        
        <div class="stats">
            <h3>📊 Статистика</h3>
            <p>Пользователей: <span id="users">{len(users_db)}</span></p>
            <p>Активных токенов: <span id="active">{len(token_service.active_tokens)}</span></p>
            <p>Отозвано токенов: <span id="blacklisted">{len(token_service.blacklist)}</span></p>
        </div>
        
        <script>
            setInterval(async () => {{
                const res = await fetch('/stats');
                const data = await res.json();
                document.getElementById('users').textContent = data.users;
                document.getElementById('active').textContent = data.active_tokens;
                document.getElementById('blacklisted').textContent = data.blacklisted;
            }}, 5000);
        </script>
    </body>
    </html>
    """)

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Регистрация</title>
        <style>
            body {{ font-family: Arial; max-width: 400px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; text-align: center; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
            button {{ 
                width: 100%; 
                padding: 12px; 
                background: #28a745; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px; 
            }}
            button:hover {{ background: #218838; }}
            .error {{ color: #dc3545; margin: 10px 0; display: none; }}
            .success {{ color: #28a745; margin: 10px 0; display: none; }}
            .info {{ 
                background: #e7f3ff; 
                padding: 15px; 
                border-radius: 5px; 
                margin-bottom: 20px; 
                font-size: 14px; 
            }}
        </style>
    </head>
    <body>
        <h1>📝 Регистрация</h1>
        
        <div class="info">
            <strong>Требования:</strong><br>
            • Имя: минимум 7 символов, с заглавной буквы<br>
            • Пароль: 8+ символов, цифра, спецсимвол, заглавная буква<br>
            • Возраст: 14+ лет
        </div>
        
        <form id="registerForm">
            <input type="text" id="username" placeholder="Имя пользователя" value="TestUser" required>
            <input type="email" id="email" placeholder="Email" value="test@test.com" required>
            <input type="password" id="password" placeholder="Пароль" value="Test123!@#" required>
            <input type="password" id="c_password" placeholder="Подтверждение" value="Test123!@#" required>
            <input type="date" id="birthday" value="2000-01-01" required>
            <button type="submit">Зарегистрироваться</button>
        </form>
        
        <div id="error" class="error"></div>
        <div id="success" class="success"></div>
        
        <p style="text-align: center; margin-top: 20px;">
            <a href="/login">Уже есть аккаунт? Войти</a>
        </p>
        
        <script>
            document.getElementById('registerForm').onsubmit = async (e) => {{
                e.preventDefault();
                
                const errorDiv = document.getElementById('error');
                const successDiv = document.getElementById('success');
                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';
                
                const data = {{
                    username: document.getElementById('username').value,
                    email: document.getElementById('email').value,
                    password: document.getElementById('password').value,
                    c_password: document.getElementById('c_password').value,
                    birthday: document.getElementById('birthday').value
                }};
                
                try {{
                    const res = await fetch('/api/auth/register', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await res.json();
                    
                    if (res.ok) {{
                        successDiv.textContent = '✅ Регистрация успешна! Перенаправление...';
                        successDiv.style.display = 'block';
                        setTimeout(() => window.location.href = '/login', 2000);
                    }} else {{
                        errorDiv.textContent = '❌ ' + (result.detail || 'Ошибка регистрации');
                        errorDiv.style.display = 'block';
                    }}
                }} catch (err) {{
                    errorDiv.textContent = '❌ Ошибка соединения';
                    errorDiv.style.display = 'block';
                }}
            }};
        </script>
    </body>
    </html>
    """)

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Вход</title>
        <style>
            body {{ font-family: Arial; max-width: 400px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; text-align: center; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
            button {{ 
                width: 100%; 
                padding: 12px; 
                background: #007bff; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px; 
            }}
            button:hover {{ background: #0056b3; }}
            .error {{ color: #dc3545; margin: 10px 0; display: none; }}
            .success {{ color: #28a745; margin: 10px 0; display: none; }}
            .token-info {{ 
                background: #e7f3ff; 
                padding: 15px; 
                border-radius: 5px; 
                margin-top: 20px; 
                display: none; 
                word-break: break-all; 
            }}
            .limit-info {{
                background: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                font-size: 14px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>🔑 Вход в систему</h1>
        
        <div class="limit-info">
            ⚠️ Максимум {MAX_ACTIVE_TOKENS} активных сессий
        </div>
        
        <form id="loginForm">
            <input type="text" id="username" placeholder="Имя пользователя" value="TestUser" required>
            <input type="password" id="password" placeholder="Пароль" value="Test123!@#" required>
            <button type="submit">Войти</button>
        </form>
        
        <div id="error" class="error"></div>
        <div id="success" class="success"></div>
        
        <div id="tokenInfo" class="token-info">
            <h3>✅ Вход выполнен!</h3>
            <p><strong>Access Token:</strong></p>
            <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 12px; word-break: break-all;" id="accessToken"></div>
            
            <p><strong style="margin-top: 15px; display: block;">Refresh Token:</strong></p>
            <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 12px; word-break: break-all;" id="refreshToken"></div>
            
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button onclick="copyAccessToken()" style="flex: 1; background: #28a745;">📋 Access</button>
                <button onclick="copyRefreshToken()" style="flex: 1; background: #17a2b8;">🔄 Refresh</button>
                <button onclick="goToProfile()" style="flex: 1; background: #007bff;">👤 Профиль</button>
            </div>
            
            <div style="margin-top: 15px;">
                <button onclick="testRefresh()" style="background: #ffc107; color: #000;">🔄 Тест Refresh</button>
                <button onclick="logout()" style="background: #dc3545;">🚪 Выйти</button>
            </div>
            
            <div id="refreshResult" style="margin-top: 15px; display: none;">
                <h4>Результат refresh:</h4>
                <pre id="refreshData" style="background: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 11px;"></pre>
            </div>
        </div>
        
        <p style="text-align: center; margin-top: 20px;">
            <a href="/register">Нет аккаунта? Зарегистрироваться</a>
        </p>
        
        <script>
            let currentTokens = null;
            
            document.getElementById('loginForm').onsubmit = async (e) => {{
                e.preventDefault();
                
                const errorDiv = document.getElementById('error');
                const successDiv = document.getElementById('success');
                const tokenInfo = document.getElementById('tokenInfo');
                const refreshResult = document.getElementById('refreshResult');
                
                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';
                tokenInfo.style.display = 'none';
                refreshResult.style.display = 'none';
                
                const data = {{
                    username: document.getElementById('username').value,
                    password: document.getElementById('password').value
                }};
                
                try {{
                    const res = await fetch('/api/auth/login', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await res.json();
                    
                    if (res.ok) {{
                        currentTokens = result;
                        
                        // Сохраняем в localStorage
                        localStorage.setItem('access_token', result.access_token);
                        localStorage.setItem('refresh_token', result.refresh_token);
                        
                        document.getElementById('accessToken').textContent = result.access_token;
                        document.getElementById('refreshToken').textContent = result.refresh_token;
                        
                        tokenInfo.style.display = 'block';
                        successDiv.textContent = '✅ Вход выполнен!';
                        successDiv.style.display = 'block';
                    }} else {{
                        errorDiv.textContent = '❌ ' + (result.detail || 'Ошибка входа');
                        errorDiv.style.display = 'block';
                    }}
                }} catch (err) {{
                    errorDiv.textContent = '❌ Ошибка соединения';
                    errorDiv.style.display = 'block';
                }}
            }};
            
            function copyAccessToken() {{
                const token = document.getElementById('accessToken').textContent;
                navigator.clipboard.writeText(token);
                alert('Access token скопирован!');
            }}
            
            function copyRefreshToken() {{
                const token = document.getElementById('refreshToken').textContent;
                navigator.clipboard.writeText(token);
                alert('Refresh token скопирован!');
            }}
            
            async function testRefresh() {{
                const refreshToken = localStorage.getItem('refresh_token');
                if (!refreshToken) {{
                    alert('Нет refresh токена');
                    return;
                }}
                
                try {{
                    const res = await fetch('/api/auth/refresh', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{refresh_token: refreshToken}})
                    }});
                    
                    const result = await res.json();
                    
                    const refreshResult = document.getElementById('refreshResult');
                    const refreshData = document.getElementById('refreshData');
                    
                    refreshData.textContent = JSON.stringify(result, null, 2);
                    refreshResult.style.display = 'block';
                    
                    if (res.ok) {{
                        // Обновляем сохраненные токены
                        localStorage.setItem('access_token', result.access_token);
                        localStorage.setItem('refresh_token', result.refresh_token);
                        
                        document.getElementById('accessToken').textContent = result.access_token;
                        document.getElementById('refreshToken').textContent = result.refresh_token;
                        
                        alert('✅ Токены обновлены!');
                    }}
                }} catch (err) {{
                    alert('❌ Ошибка: ' + err);
                }}
            }}
            
            async function logout() {{
                const token = localStorage.getItem('access_token');
                if (token) {{
                    await fetch('/api/auth/out', {{
                        method: 'POST',
                        headers: {{'Authorization': `Bearer ${{token}}`}}
                    }});
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                }}
                document.getElementById('tokenInfo').style.display = 'none';
                document.getElementById('success').textContent = '✅ Вы вышли из системы';
                document.getElementById('success').style.display = 'block';
            }}
            
            function goToProfile() {{
                window.location.href = '/profile';
            }}
            
            // Проверяем есть ли сохраненный токен
            if (localStorage.getItem('access_token')) {{
                document.getElementById('accessToken').textContent = localStorage.getItem('access_token');
                document.getElementById('refreshToken').textContent = localStorage.getItem('refresh_token');
                document.getElementById('tokenInfo').style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/profile", response_class=HTMLResponse)
async def profile_page():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Профиль</title>
        <style>
            body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #333; text-align: center; }}
            .card {{ 
                background: #f5f5f5; 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0; 
            }}
            .info {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
            button {{ 
                padding: 10px 20px; 
                margin: 5px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 14px; 
            }}
            .logout {{ background: #dc3545; color: white; }}
            .tokens {{ background: #007bff; color: white; }}
            .refresh {{ background: #ffc107; color: black; }}
            .error {{ color: #dc3545; margin: 10px 0; display: none; }}
            pre {{ background: white; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            .token-item {{
                background: white;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }}
            .limit-info {{
                background: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>👤 Профиль пользователя</h1>
        
        <div class="limit-info">
            ⚠️ Максимальное количество активных сессий: {MAX_ACTIVE_TOKENS}
        </div>
        
        <div id="profile" class="card" style="display: none;">
            <h2>Информация</h2>
            <div id="userInfo" class="info"></div>
            
            <h3>Активные сессии</h3>
            <div id="tokensList"></div>
            <p id="tokenCount"></p>
            
            <div style="margin-top: 20px;">
                <button onclick="refreshTokens()" class="refresh">🔄 Обновить токен</button>
                <button onclick="showTokens()" class="tokens">🔑 Показать токены</button>
                <button onclick="logout()" class="logout">🚪 Выйти</button>
                <button onclick="logoutAll()" style="background: #6c757d; color: white;">🚪 Выйти везде</button>
            </div>
        </div>
        
        <div id="tokens" class="card" style="display: none;">
            <h2>Информация о токенах</h2>
            <pre id="tokensData"></pre>
            <button onclick="hideTokens()">Назад</button>
        </div>
        
        <div id="error" class="error"></div>
        
        <p style="text-align: center;">
            <a href="/">На главную</a>
        </p>
        
        <script>
            const token = localStorage.getItem('access_token');
            
            if (!token) {{
                window.location.href = '/login';
            }}
            
            async function loadProfile() {{
                try {{
                    const res = await fetch('/api/auth/me', {{
                        headers: {{'Authorization': `Bearer ${{token}}`}}
                    }});
                    
                    if (res.ok) {{
                        const user = await res.json();
                        document.getElementById('profile').style.display = 'block';
                        document.getElementById('userInfo').innerHTML = `
                            <p><strong>ID:</strong> ${{user.id}}</p>
                            <p><strong>Имя:</strong> ${{user.username}}</p>
                            <p><strong>Email:</strong> ${{user.email}}</p>
                            <p><strong>Дата рождения:</strong> ${{user.birthday}}</p>
                            <p><strong>Дата регистрации:</strong> ${{new Date(user.created_at).toLocaleString()}}</p>
                        `;
                        
                        // Загружаем токены
                        await loadTokens();
                        
                    }} else if (res.status === 401) {{
                        // Пробуем обновить токен
                        const refresh = localStorage.getItem('refresh_token');
                        if (refresh) {{
                            const refreshRes = await fetch('/api/auth/refresh', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{refresh_token: refresh}})
                            }});
                            
                            if (refreshRes.ok) {{
                                const newTokens = await refreshRes.json();
                                localStorage.setItem('access_token', newTokens.access_token);
                                localStorage.setItem('refresh_token', newTokens.refresh_token);
                                window.location.reload();
                            }} else {{
                                window.location.href = '/login';
                            }}
                        }} else {{
                            window.location.href = '/login';
                        }}
                    }}
                }} catch (err) {{
                    document.getElementById('error').textContent = '❌ Ошибка загрузки';
                    document.getElementById('error').style.display = 'block';
                }}
            }}
            
            async function loadTokens() {{
                try {{
                    const res = await fetch('/api/auth/tokens', {{
                        headers: {{'Authorization': `Bearer ${{token}}`}}
                    }});
                    
                    if (res.ok) {{
                        const data = await res.json();
                        const tokensList = document.getElementById('tokensList');
                        const tokenCount = document.getElementById('tokenCount');
                        
                        tokensList.innerHTML = '';
                        data.tokens.forEach(t => {{
                            tokensList.innerHTML += `
                                <div class="token-item">
                                    <strong>ID:</strong> ${{t.id}}<br>
                                    <strong>Создан:</strong> ${{new Date(t.created_at).toLocaleString()}}<br>
                                    <strong>Истекает:</strong> ${{new Date(t.expires_at).toLocaleString()}}<br>
                                    <strong>IP:</strong> ${{t.ip}}
                                </div>
                            `;
                        }});
                        
                        tokenCount.innerHTML = `<strong>Активных сессий:</strong> ${{data.total}} из ${{data.limit}}`;
                    }}
                }} catch (err) {{
                    console.error(err);
                }}
            }}
            
            async function refreshTokens() {{
                const refresh = localStorage.getItem('refresh_token');
                if (!refresh) {{
                    alert('Нет refresh токена');
                    return;
                }}
                
                try {{
                    const res = await fetch('/api/auth/refresh', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{refresh_token: refresh}})
                    }});
                    
                    if (res.ok) {{
                        const newTokens = await res.json();
                        localStorage.setItem('access_token', newTokens.access_token);
                        localStorage.setItem('refresh_token', newTokens.refresh_token);
                        alert('✅ Токены обновлены!');
                        window.location.reload();
                    }} else {{
                        alert('❌ Ошибка обновления');
                    }}
                }} catch (err) {{
                    alert('❌ Ошибка: ' + err);
                }}
            }}
            
            async function logout() {{
                await fetch('/api/auth/out', {{
                    method: 'POST',
                    headers: {{'Authorization': `Bearer ${{token}}`}}
                }});
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
            }}
            
            async function logoutAll() {{
                if (confirm('Выйти со всех устройств? Будут отозваны все токены кроме текущего.')) {{
                    await fetch('/api/auth/out_all', {{
                        method: 'POST',
                        headers: {{'Authorization': `Bearer ${{token}}`}}
                    }});
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                }}
            }}
            
            function showTokens() {{
                document.getElementById('profile').style.display = 'none';
                document.getElementById('tokens').style.display = 'block';
                
                const tokens = {{
                    access: localStorage.getItem('access_token'),
                    refresh: localStorage.getItem('refresh_token')
                }};
                document.getElementById('tokensData').textContent = JSON.stringify(tokens, null, 2);
            }}
            
            function hideTokens() {{
                document.getElementById('tokens').style.display = 'none';
                document.getElementById('profile').style.display = 'block';
            }}
            
            loadProfile();
        </script>
    </body>
    </html>
    """)

@app.get("/stats")
async def stats():
    return {
        "users": len(users_db),
        "active_tokens": len(token_service.active_tokens),
        "blacklisted": len(token_service.blacklist)
    }

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}