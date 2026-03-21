#!/bin/bash

echo "🧪 Тестирование RBAC консоли..."
echo ""

# Тест 1: Попытка логина
echo "✅ Тест 1: Логин"
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Admin123","password":"Admin@123"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$TOKEN" ]; then
  echo "   ✓ Токен получен: ${TOKEN:0:20}..."
else
  echo "   ✗ Ошибка получения токена"
  exit 1
fi

echo ""
echo "✅ Тест 2: Получение профиля"
PROFILE=$(curl -s -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)

if [ "$PROFILE" = "Admin123" ]; then
  echo "   ✓ Профиль загружен: $PROFILE"
else
  echo "   ✗ Ошибка загрузки профиля"
  exit 1
fi

echo ""
echo "✅ Тест 3: Получение ролей"
ROLES=$(curl -s -X GET http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $TOKEN" | grep -o '"id":[0-9]*' | wc -l)

if [ $ROLES -gt 0 ]; then
  echo "   ✓ Получено $ROLES ролей"
else
  echo "   ✗ Ошибка получения ролей"
  exit 1
fi

echo ""
echo "✅ Тест 4: Получение разрешений"
PERMS=$(curl -s -X GET http://localhost:8000/api/ref/policy/permission \
  -H "Authorization: Bearer $TOKEN" | grep -o '"id":[0-9]*' | wc -l)

if [ $PERMS -gt 0 ]; then
  echo "   ✓ Получено $PERMS разрешений"
else
  echo "   ✗ Ошибка получения разрешений"
  exit 1
fi

echo ""
echo "✅ Тест 5: Получение пользователей"
USERS=$(curl -s -X GET http://localhost:8000/api/ref/user \
  -H "Authorization: Bearer $TOKEN" | grep -o '"id":[0-9]*' | wc -l)

if [ $USERS -gt 0 ]; then
  echo "   ✓ Получено $USERS пользователей"
else
  echo "   ✗ Ошибка получения пользователей"
  exit 1
fi

echo ""
echo "✅ Тест 6: Проверка 403 ошибки (ограниченный пользователь)"
LIMITED_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"LimitedUser","password":"LimitedPass123!@#"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/ref/policy/role \
  -H "Authorization: Bearer $LIMITED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","slug":"test","description":"Test"}')

STATUS=$(echo "$RESPONSE" | tail -n1)
if [ "$STATUS" = "403" ]; then
  echo "   ✓ Получена ошибка 403 FORBIDDEN (правильно!)"
else
  echo "   ✗ Ожидалась 403, получено $STATUS"
  exit 1
fi

echo ""
echo "🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!"
echo ""
echo "КОНСОЛЬ ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНА!"
