# Лабораторная работа №3: RBAC система

## ✅ Статус: ЗАВЕРШЕНА

Создана ветка **lb3** на основе **lb2** с полной системой управления ролями и разрешениями (RBAC).

## 📋 Что включено

### Сохранено из lb2
- Полная система аутентификации (login, register, logout)
- JWT токены (access + refresh)
- Все HTML страницы (регистрация, логин, профиль)
- 7 endpoints для аутентификации
- Хеширование паролей bcrypt

### Добавлено в lb3
- **4 новые модели БД:**
  - Role (роли с мягким удалением)
  - Permission (разрешения с мягким удалением)
  - RoleUser (назначение ролей пользователям)
  - PermissionRole (назначение разрешений ролям)

- **14 новых API endpoints:**
  - 7 для управления ролями
  - 7 для управления разрешениями

- **Система разрешений:**
  - check_permission() для проверки доступа
  - Иерархическая проверка: User -> Role -> Permission
  - Мягкое удаление с возможностью восстановления

- **Начальные данные (seeders):**
  - 3 роли: Admin, User, Guest
  - 18 разрешений
  - Назначение разрешений ролям

- **Документация:**
  - RBAC_README.md - полное описание
  - Комментарии в коде с указанием источников

## 📁 Структура

```
app/
  models/
    role.py
    permission.py
    role_user.py
    permission_role.py
  services/
    permission_service.py
  controllers/
    role_controller.py
    permission_controller.py
  dto/
    rbac_dto.py
  utils/
    seeders.py
RBAC_README.md
```

## 🔐 Как использовать

1. **Запустить сервер:**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Регистрация и вход** (из lb2):
   ```bash
   POST /api/auth/register
   POST /api/auth/login
   ```

3. **Управление ролями:**
   ```bash
   GET /api/ref/policy/role
   POST /api/ref/policy/role
   PUT /api/ref/policy/role/{id}
   DELETE /api/ref/policy/role/{id}
   ```

4. **Управление разрешениями:**
   ```bash
   GET /api/ref/policy/permission
   POST /api/ref/policy/permission
   PUT /api/ref/policy/permission/{id}
   DELETE /api/ref/policy/permission/{id}
   ```

## 🔑 Ключевые особенности

- ✅ Мягкое удаление (soft delete) с восстановлением
- ✅ Проверка разрешений на каждый запрос
- ✅ Интегрировано с существующей JWT аутентификацией
- ✅ Иерархическая система разрешений
- ✅ Полная документация с примерами
- ✅ Готовые seeders для начальных данных

## 📝 Коммиты

1. **1757082** - "Add RBAC system to Lab3 based on Lab2 authentication"
   - Все модели, сервисы, контроллеры
   - Документация и seeders

## 🌳 Ветки

- **main** - исходная ветка
- **lb2** - Lab2 с аутентификацией
- **lb3** - Lab3 с RBAC системой ← **ВЫ ЗДЕСЬ**

Система полностью готова к использованию и демонстрации!
