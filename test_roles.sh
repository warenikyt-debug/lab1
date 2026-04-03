#!/bin/bash

BASE_URL="http://localhost:8000"
ADMIN_USER="Admin123"
ADMIN_PASS="Admin@123"
USER_USER="TestUser1"
USER_PASS="Test123!@#"

echo "🔍 ТЕСТИРОВАНИЕ СИСТЕМЫ РОЛЕЙ"
echo "================================"

# Логин админа
echo -e "\n1️⃣ Логин админом ($ADMIN_USER)..."
ADMIN_LOGIN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}")

ADMIN_TOKEN=$(echo $ADMIN_LOGIN | grep -o '"access_token":"[^"]*' | head -1 | cut -d'"' -f4)
echo "Token: ${ADMIN_TOKEN:0:30}..."
if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ Ошибка логина админа"
  echo "Ответ: $ADMIN_LOGIN"
  exit 1
fi

# Логин юзера
echo -e "\n2️⃣ Логин юзером ($USER_USER)..."
USER_LOGIN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER_USER\",\"password\":\"$USER_PASS\"}")

USER_TOKEN=$(echo $USER_LOGIN | grep -o '"access_token":"[^"]*' | head -1 | cut -d'"' -f4)
echo "Token: ${USER_TOKEN:0:30}..."
if [ -z "$USER_TOKEN" ]; then
  echo "❌ Ошибка логина юзера"
  echo "Ответ: $USER_LOGIN"
  exit 1
fi

# Проверка профиля админа
echo -e "\n3️⃣ Профиль админа..."
ADMIN_PROFILE=$(curl -s -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
echo "$ADMIN_PROFILE" | grep -o '"username":"[^"]*' || echo "Ошибка"

# Проверка профиля юзера
echo -e "\n4️⃣ Профиль юзера..."
USER_PROFILE=$(curl -s -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $USER_TOKEN")
echo "$USER_PROFILE" | grep -o '"username":"[^"]*' || echo "Ошибка"

# Список пользователей (admin endpoint)
echo -e "\n5️⃣ GET /api/users (админ должен видеть)..."
USERS_ADMIN=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$USERS_ADMIN" | tail -1)
echo "HTTP $CODE"

# Список пользователей (юзер endpoint)
echo -e "\n6️⃣ GET /api/users (юзер должен получить 403)..."
USERS_USER=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/users" \
  -H "Authorization: Bearer $USER_TOKEN")
CODE=$(echo "$USERS_USER" | tail -1)
echo "HTTP $CODE"

echo -e "\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО"
