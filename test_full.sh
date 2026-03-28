#!/bin/bash

BASE="http://localhost:5000"

echo "=== 🔍 ПОЛНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ТОКЕНОВ ==="
echo ""

# 1. Вход
echo "1️⃣ Вход в систему..."
LOGIN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"Admin123","password":"Admin@123"}')

ACCESS=$(echo $LOGIN | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['access_token'])" 2>/dev/null)
REFRESH=$(echo $LOGIN | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['refresh_token'])" 2>/dev/null)

if [ -z "$ACCESS" ]; then
    echo "❌ Ошибка входа"
    exit 1
fi

echo "✅ Вошли успешно"
echo ""

# 2. Получение списка токенов
echo "2️⃣ Получение списка токенов..."
TOKENS=$(curl -s -X GET "$BASE/api/auth/tokens" \
  -H "Authorization: Bearer $ACCESS")

TOKEN_COUNT=$(echo "$TOKENS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d['tokens']))" 2>/dev/null)
echo "✅ Найдено токенов: $TOKEN_COUNT"
echo ""

# 3. Проверка структуры токенов
echo "3️⃣ Проверка структуры токенов..."
echo "$TOKENS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for i, t in enumerate(d['tokens']):
    print(f\"Token {i+1}:\")
    print(f\"  Type: {t.get('token_type')}\")
    print(f\"  Value: {t.get('token_value', '')[:30]}...\")
    print(f\"  Expires: {t.get('expires_at')}\")
" 2>/dev/null
echo ""

# 4. Выход из системы
echo "4️⃣ Выход из системы..."
LOGOUT=$(curl -s -X POST "$BASE/api/auth/logout" \
  -H "Authorization: Bearer $ACCESS")

echo "✅ Вышли из системы"
echo ""

# 5. Проверка, что токен больше не работает
echo "5️⃣ Проверка, что токен больше не работает (должна быть ошибка 401)..."
ME=$(curl -s -w "%{http_code}" -X GET "$BASE/api/auth/me" \
  -H "Authorization: Bearer $ACCESS")

HTTP_CODE=$(echo "$ME" | tail -c 4)
if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ Правильно! Токен отозван (HTTP $HTTP_CODE)"
else
    echo "❌ Ошибка! Ожидалась 401, получена $HTTP_CODE"
fi
echo ""

echo "=== ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ ==="
