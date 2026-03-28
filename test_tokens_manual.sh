#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🔍 ТЕСТИРОВАНИЕ СИСТЕМЫ ТОКЕНОВ"
echo ""

# 1. Вход (используя существующего пользователя)
echo "1️⃣ Вход в систему..."
LOGIN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Admin123",
    "password": "Admin@123"
  }')

echo "Результат: $LOGIN"

ACCESS_TOKEN=$(echo $LOGIN | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)
REFRESH_TOKEN=$(echo $LOGIN | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('refresh_token', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Ошибка при входе"
    exit 1
fi

echo "Access Token: ${ACCESS_TOKEN:0:20}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."
echo ""

# 2. Получение списка токенов
echo "2️⃣ Получение списка активных токенов..."
TOKENS=$(curl -s -X GET "$BASE_URL/api/auth/tokens" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Результат: $TOKENS"
echo ""

# 3. Выход
echo "3️⃣ Выход из системы..."
LOGOUT=$(curl -s -X POST "$BASE_URL/api/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Результат: $LOGOUT"
echo ""

# 4. Попытка использовать токен после выхода (должна вернуть ошибку)
echo "4️⃣ Попытка использовать access token после выхода (должна вернуть 401)..."
ME=$(curl -s -w "\nHTTP Status: %{http_code}\n" -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Результат: $ME"
echo ""

echo "✅ Тестирование завершено!"
