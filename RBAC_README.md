# RBAC система (Role-Based Access Control) для FastAPI

## Описание

Это расширение Lab2 на основе системы аутентификации добавляет управление ролями и разрешениями.

## Архитектура

### Модели БД

1. **User** (существующая) - пользователи
   - id, username, email, password_hash, birthday, created_at
   - relationships: roles (many-to-many через role_user)

2. **Role** (новая) - роли
   - id, name, slug, description
   - created_at, created_by, updated_at, deleted_at, deleted_by
   - relationships: permissions (many-to-many через permission_role)
   - relationships: users (many-to-many через role_user)

3. **Permission** (новая) - разрешения
   - id, name, slug, description
   - created_at, created_by, updated_at, deleted_at, deleted_by
   - relationships: roles (many-to-many через permission_role)

4. **RoleUser** (новая) - назначение ролей пользователям
   - id, user_id, role_id, created_at, created_by, deleted_at, deleted_by

5. **PermissionRole** (новая) - назначение разрешений ролям
   - id, role_id, permission_id, created_at, created_by, deleted_at, deleted_by

## Мягкое удаление (Soft Delete)

Все модели поддерживают мягкое удаление:
- deleted_at: время удаления (NULL если активно)
- deleted_by: user_id удалившего
- Восстановление: deleted_at = NULL

При запросе всегда фильтруются только активные записи (deleted_at IS NULL).

## API Endpoints

### Роли (/api/ref/policy/role)

- GET / - список ролей
- GET /{role_id} - получить роль
- POST / - создать роль (требует permission: create-role)
- PUT /{role_id} - обновить роль (требует permission: update-role)
- DELETE /{role_id} - мягко удалить роль (требует permission: delete-role)
- DELETE /{role_id}/permanent - физически удалить роль
- POST /{role_id}/restore - восстановить роль (требует permission: restore-role)

### Разрешения (/api/ref/policy/permission)

- GET / - список разрешений
- GET /{permission_id} - получить разрешение
- POST / - создать разрешение (требует permission: create-permission)
- PUT /{permission_id} - обновить разрешение (требует permission: update-permission)
- DELETE /{permission_id} - мягко удалить разрешение
- DELETE /{permission_id}/permanent - физически удалить разрешение
- POST /{permission_id}/restore - восстановить разрешение

## Начальные данные (Seeders)

Используйте seed_db.py для загрузки начальных данных:

```bash
python seed_db.py
```

Создает:

**Роли (3):**
- Admin - полный доступ
- User - ограниченный доступ
- Guest - минимальный доступ

**Разрешения (18):**
- get-list-user, read-user, create-user, update-user, delete-user, restore-user
- get-list-role, read-role, create-role, update-role, delete-role, restore-role
- get-list-permission, read-permission, create-permission, update-permission, delete-permission, restore-permission

**Назначения:**
- Admin: все разрешения
- User: get-list-user, read-user, update-user
- Guest: get-list-user

## Проверка разрешений

```python
# В контроллере
user_id = int(current_user.get("sub"))

if not PermissionService.check_permission(db, user_id, "create-role"):
    raise HTTPException(status_code=403, detail="Недостаточно прав")

# Алгоритм:
# 1. Найти пользователя по user_id
# 2. Получить все его роли (не удаленные)
# 3. Получить все разрешения для каждой роли (не удаленные)
# 4. Проверить есть ли нужное разрешение
```

## Примеры использования

### Создание новой роли

```bash
curl -X POST http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manager",
    "slug": "manager",
    "description": "Manager role"
  }'
```

### Получение списка ролей

```bash
curl -X GET http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer <access_token>"
```

### Удаление роли

```bash
curl -X DELETE http://localhost:8000/api/ref/policy/role/1 \
  -H "Authorization: Bearer <access_token>"
```

### Восстановление роли

```bash
curl -X POST http://localhost:8000/api/ref/policy/role/1/restore \
  -H "Authorization: Bearer <access_token>"
```

## Интеграция с существующей аутентификацией

- Все endpoints требуют валидный access_token
- Token передается в заголовке: Authorization: Bearer <token>
- Извлечение user_id из токена: `int(current_user.get("sub"))`
- Проверка разрешений на каждый запрос

## Файловая структура

```
app/
  models/
    role.py - модель Role
    permission.py - модель Permission
    role_user.py - таблица role_user
    permission_role.py - таблица permission_role
  services/
    permission_service.py - PermissionService с check_permission
  controllers/
    role_controller.py - endpoints для ролей
    permission_controller.py - endpoints для разрешений
  dto/
    rbac_dto.py - RoleDTO, PermissionDTO и т.д.
  utils/
    seeders.py - функции для посева данных
seed_db.py - скрипт посева
```

## Безопасность

- Все операции требуют валидный access_token
- Разрешения проверяются перед каждой операцией
- Мягкое удаление позволяет восстановить данные
- created_by и deleted_by отслеживают кто создал/удалил

## Расширение

Для добавления новых разрешений:

1. Добавьте новое разрешение через API
2. Или добавьте в seeders.py и пересоздайте БД
3. Назначьте разрешение ролям
4. Проверьте в контроллере: `PermissionService.check_permission(...)`
