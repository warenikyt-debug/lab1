# LAB2 и LAB3 - Разделение кода

## Цветовое обозначение:
- <span style="background-color: #99CCFF;">LAB2 (Синий)</span> - Аутентификация
- <span style="background-color: #99FF99;">LAB3 (Зелёный)</span> - RBAC система

---

## СТРУКТУРА ПРОЕКТА

### LAB2 - Аутентификация и управление профилем

```python
# <span style="background-color: #99CCFF;">LAB2</span>
app/
├── models/
│   └── user.py              # User модель (id, username, email, password, birthday)
├── controllers/
│   └── auth_controller.py   # Все endpoints аутентификации
├── services/
│   ├── auth_service.py      # Логика логина/регистрации
│   └── token_service.py     # JWT токены (access + refresh)
├── middlewares/
│   └── auth_middleware.py   # Проверка токенов
└── main.py                  # Маршруты: /login, /register, /profile, /docs

# Endpoints LAB2:
POST   /api/auth/register    # Регистрация
POST   /api/auth/login       # Логин
GET    /api/auth/me          # Получить профиль
POST   /api/auth/refresh     # Обновить токены
GET    /api/auth/tokens      # Список активных токенов
POST   /api/auth/logout      # Выход
POST   /api/auth/out_all     # Выход со всех устройств
```

### LAB3 - RBAC система (Управление ролями и разрешениями)

```python
# <span style="background-color: #99FF99;">LAB3</span>
app/
├── models/
│   ├── role.py              # Role модель (id, name, slug, description)
│   ├── permission.py        # Permission модель (id, name, slug, description)
│   ├── role_user.py         # RoleUser модель (связь User-Role)
│   └── permission_role.py   # PermissionRole модель (связь Role-Permission)
├── controllers/
│   ├── role_controller.py       # 7 endpoints для управления ролями
│   ├── permission_controller.py # 7 endpoints для управления разрешениями
│   └── user_role_controller.py  # 5 endpoints для управления user-role
├── requests/
│   └── rbac_requests.py     # Form Requests (валидация)
└── services/
    └── permission_service.py    # Проверка разрешений (авторизация)

# Endpoints LAB3:
GET    /api/ref/policy/role                    # Получить все роли
POST   /api/ref/policy/role                    # Создать роль
PUT    /api/ref/policy/role/{id}               # Обновить роль
DELETE /api/ref/policy/role/{id}               # Удалить роль
DELETE /api/ref/policy/role/{id}/soft          # Мягко удалить роль
POST   /api/ref/policy/role/{id}/restore       # Восстановить роль

GET    /api/ref/policy/permission              # Получить все разрешения
POST   /api/ref/policy/permission              # Создать разрешение
PUT    /api/ref/policy/permission/{id}         # Обновить разрешение
DELETE /api/ref/policy/permission/{id}         # Удалить разрешение
DELETE /api/ref/policy/permission/{id}/soft    # Мягко удалить разрешение
POST   /api/ref/policy/permission/{id}/restore # Восстановить разрешение

GET    /api/ref/user                           # Получить всех пользователей
GET    /api/ref/user/{id}/role                 # Получить роли пользователя
POST   /api/ref/user/{id}/role/{role_id}       # Присвоить роль
DELETE /api/ref/user/{id}/role/{role_id}       # Удалить роль
DELETE /api/ref/user/{id}/role/{role_id}/soft  # Мягко удалить роль
POST   /api/ref/user/{id}/role/{role_id}/restore # Восстановить роль
```

---

## LAB2 - ДЕТАЛЬНОЕ ОПИСАНИЕ

### 1. User Model (LAB2)

```python
# <span style="background-color: #99CCFF;">LAB2</span>
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    birthday = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # LAB3 добавит:
    # roles = relationship("Role", secondary="role_user", back_populates="users")
```

### 2. Auth Controller (LAB2)

```python
# <span style="background-color: #99CCFF;">LAB2</span>
# Основные endpoints:

@router.post("/register")
def register(request: RegisterRequest, db: Session):
    """Создать новый аккаунт"""
    # Валидация данных
    # Хеширование пароля
    # Сохранение в БД
    # Возврат UserDTO

@router.post("/login")
def login(request: LoginRequest, db: Session):
    """Логин пользователя"""
    # Поиск пользователя
    # Проверка пароля
    # Создание JWT токенов (access + refresh)
    # Возврат токенов и данных пользователя

@router.get("/me")
def get_me(token_payload: dict, db: Session):
    """Получить данные текущего пользователя"""
    # Используется из middleware
    # user_id из token_payload['user_id']

@router.post("/refresh")
def refresh(token_payload: dict):
    """Обновить пару токенов"""
    # Обмен refresh_token на новую пару access+refresh

@router.get("/tokens")
def get_tokens(token_payload: dict):
    """Получить список активных токенов"""
    # Показать все токены пользователя

@router.post("/logout")
def logout(token_payload: dict):
    """Выход с текущего устройства"""
    # Добавить текущий токен в blacklist

@router.post("/out_all")
def logout_all(token_payload: dict):
    """Выход со всех устройств"""
    # Добавить все токены в blacklist
```

### 3. Token Service (LAB2)

```python
# <span style="background-color: #99CCFF;">LAB2</span>
class TokenService:
    @staticmethod
    def create_tokens(user_id: int):
        """Создать пару токенов"""
        access_payload = {
            "user_id": user_id,
            "type": "access",
            "token_id": str(uuid.uuid4()),
            "exp": datetime.now() + timedelta(hours=1)
        }
        refresh_payload = {
            "user_id": user_id,
            "type": "refresh",
            "token_id": str(uuid.uuid4()),
            "exp": datetime.now() + timedelta(days=7)
        }
        # Создать и подписать JWT
        return access_token, refresh_token

    @staticmethod
    def verify_token(token: str):
        """Проверить и декодировать токен"""
        # Проверить подпись
        # Проверить срок действия
        # Проверить blacklist
        return payload
```

### 4. Auth Middleware (LAB2)

```python
# <span style="background-color: #99CCFF;">LAB2</span>
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Проверить токен в заголовке Authorization"""
    # Получить "Bearer <token>" из заголовка
    # Декодировать токен
    # Проверить в blacklist
    # Сохранить payload в request.state
    # Передать далее
```

### 5. Pages (LAB2)

```html
<!-- <span style="background-color: #99CCFF;">LAB2</span> -->
/register      - Страница регистрации (форма на HTML)
/login         - Страница логина (форма на HTML)
/profile       - Страница профиля (требует access_token)
```

---

## LAB3 - ДЕТАЛЬНОЕ ОПИСАНИЕ

### 1. Role Model (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
from sqlalchemy import Column, Integer, String, DateTime

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    deleted_by = Column(Integer, nullable=True)   # Soft delete
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    users = relationship("User", secondary="role_user", back_populates="roles")
    permissions = relationship("Permission", secondary="permission_role", back_populates="roles")
```

### 2. Permission Model (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    deleted_by = Column(Integer, nullable=True)   # Soft delete
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    roles = relationship("Role", secondary="permission_role", back_populates="permissions")
```

### 3. RoleUser Model (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
class RoleUser(Base):
    __tablename__ = "role_user"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    deleted_by = Column(Integer, nullable=True)   # Soft delete
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    role = relationship("Role", lazy="joined")  # Eager loading
```

### 4. PermissionRole Model (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
class PermissionRole(Base):
    __tablename__ = "permission_role"
    
    id = Column(Integer, primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

### 5. Role Controller (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
@router.get("/role")
def get_roles(token_payload: dict, db: Session):
    """Получить все роли"""
    # Проверить разрешение 'get-list-role'
    # Вернуть список ролей (где deleted_at IS NULL)

@router.post("/role")
def create_role(request: StoreRoleRequest, token_payload: dict, db: Session):
    """Создать роль"""
    # Проверить разрешение 'create-role'
    # Валидировать slug уникальность
    # Создать роль
    # Вернуть 201 Created

@router.put("/role/{id}")
def update_role(id: int, request: UpdateRoleRequest, token_payload: dict, db: Session):
    """Обновить роль"""
    # Проверить разрешение 'update-role'
    # Обновить роль
    # Вернуть 200 OK

@router.delete("/role/{id}")
def delete_role(id: int, token_payload: dict, db: Session):
    """Жестко удалить роль"""
    # Проверить разрешение 'delete-role'
    # Удалить из БД полностью
    # Вернуть 204 No Content

@router.delete("/role/{id}/soft")
def soft_delete_role(id: int, token_payload: dict, db: Session):
    """Мягко удалить роль (сохранить в БД)"""
    # Проверить разрешение 'delete-role'
    # Установить deleted_at = NOW()
    # Вернуть 204 No Content

@router.post("/role/{id}/restore")
def restore_role(id: int, token_payload: dict, db: Session):
    """Восстановить мягко удаленную роль"""
    # Проверить разрешение 'restore-role'
    # Установить deleted_at = NULL
    # Вернуть 200 OK
```

### 6. Permission Controller (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
# Аналогично Role Controller, но для разрешений
# Методы: get_permissions, create_permission, update_permission, delete_permission, 
#         soft_delete_permission, restore_permission
```

### 7. User Role Controller (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
@router.get("/{user_id}/role")
def get_user_roles(user_id: int, token_payload: dict, db: Session):
    """Получить роли пользователя"""
    # Проверить разрешение 'get-user-role'
    # Вернуть роли юзера

@router.post("/{user_id}/role/{role_id}")
def assign_role(user_id: int, role_id: int, token_payload: dict, db: Session):
    """Присвоить роль пользователю"""
    # Проверить разрешение 'create-user-role'
    # Создать запись RoleUser
    # Вернуть 201 Created

@router.delete("/{user_id}/role/{role_id}")
def remove_role(user_id: int, role_id: int, token_payload: dict, db: Session):
    """Удалить роль пользователя"""
    # Проверить разрешение 'delete-user-role'
    # Удалить запись RoleUser
    # Вернуть 204 No Content

@router.delete("/{user_id}/role/{role_id}/soft")
def soft_remove_role(user_id: int, role_id: int, token_payload: dict, db: Session):
    """Мягко удалить роль пользователя"""
    # Проверить разрешение 'delete-user-role'
    # Установить deleted_at = NOW()
    # Вернуть 204 No Content

@router.post("/{user_id}/role/{role_id}/restore")
def restore_user_role(user_id: int, role_id: int, token_payload: dict, db: Session):
    """Восстановить роль пользователя"""
    # Проверить разрешение 'restore-user-role'
    # Установить deleted_at = NULL
    # Вернуть 200 OK
```

### 8. Permission Service (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
class PermissionService:
    @staticmethod
    def check_permission(db: Session, user_id: int, permission_slug: str) -> bool:
        """
        Проверить есть ли у пользователя разрешение
        
        Цепочка проверок:
        User -> RoleUser -> Role -> PermissionRole -> Permission
        """
        # Получить роли пользователя (активные)
        # Для каждой роли получить разрешения (активные)
        # Проверить есть ли нужное разрешение
        # Вернуть True/False
        
        # Admin bypass: если user_id == 1, вернуть True
```

### 9. Form Requests (LAB3)

```python
# <span style="background-color: #99FF99;">LAB3</span>
from pydantic import BaseModel, validator

class StoreRoleRequest(BaseModel):
    name: str
    slug: str
    description: str = None
    
    @validator('slug')
    def validate_slug(cls, v):
        # Проверить формат: только a-z, 0-9, -, _
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Invalid slug format')
        return v

class UpdateRoleRequest(StoreRoleRequest):
    pass

class StorePermissionRequest(BaseModel):
    name: str
    slug: str
    description: str = None
    
    @validator('slug')
    def validate_slug(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Invalid slug format')
        return v

class UpdatePermissionRequest(StorePermissionRequest):
    pass

class AttachUserRoleRequest(BaseModel):
    user_id: int
    role_id: int
```

### 10. RBAC Testing Console (LAB3)

```html
<!-- <span style="background-color: #99FF99;">LAB3</span> -->
/rbac-testing  - Интерактивная консоль для тестирования всех 27 endpoints

Позволяет:
- Авторизоваться как Admin или User
- Тестировать все операции CRUD
- Видеть результаты API запросов
- Проверять разрешения (403 ошибки)
- Управлять ролями и разрешениями
- Управлять ролями пользователей
```

---

## СРАВНЕНИЕ LAB2 vs LAB3

| Функция | LAB2 | LAB3 |
|---------|------|------|
| Аутентификация | ✅ | ✓ (использует LAB2) |
| Регистрация | ✅ | ✓ (использует LAB2) |
| JWT Токены | ✅ | ✓ (использует LAB2) |
| Логин/Выход | ✅ | ✓ (использует LAB2) |
| **Роли** | ❌ | ✅ |
| **Разрешения** | ❌ | ✅ |
| **Авторизация** | ❌ | ✅ |
| **RBAC** | ❌ | ✅ |
| **Soft Delete** | ❌ | ✅ |
| **Управление ролями** | ❌ | ✅ |

---

## ФАЙЛЫ ПРОЕКТА ПО ЛАБОРАТОРИЯМ

### LAB2 FILES:

```
<span style="background-color: #99CCFF;">
app/
├── models/user.py
├── controllers/auth_controller.py
├── services/auth_service.py
├── services/token_service.py
├── middlewares/auth_middleware.py
├── dto/user_dto.py
├── main.py (routes: /login, /register, /profile)
templates/
├── login.html
├── register.html
├── profile.html
requirements.txt (основные зависимости)
</span>
```

### LAB3 FILES (НОВЫЕ):

```
<span style="background-color: #99FF99;">
app/
├── models/
│   ├── role.py (НОВЫЙ)
│   ├── permission.py (НОВЫЙ)
│   ├── role_user.py (НОВЫЙ)
│   └── permission_role.py (НОВЫЙ)
├── controllers/
│   ├── role_controller.py (НОВЫЙ)
│   ├── permission_controller.py (НОВЫЙ)
│   └── user_role_controller.py (НОВЫЙ)
├── requests/rbac_requests.py (НОВЫЙ)
├── services/permission_service.py (НОВЫЙ)
└── main.py (ОБНОВЛЕН - добавлены новые маршруты)
templates/
└── rbac_testing.html (НОВЫЙ)
docs/
└── RBAC_TESTING_CONSOLE.md (НОВЫЙ)
</span>
```

---

## ИТОГО

**LAB2** обеспечивает базовую аутентификацию и управление пользователями.

**LAB3** добавляет полноценную RBAC систему с ролями, разрешениями и авторизацией, которая работает поверх LAB2.

Все части LAB2 остаются работающими и используются LAB3.
