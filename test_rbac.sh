#!/bin/bash

# 🧪 СКРИПТ ДЛЯ ТЕСТИРОВАНИЯ RBAC СИСТЕМЫ

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         ТЕСТИРОВАНИЕ RBAC СИСТЕМЫ                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверить что сервер работает
echo -e "${BLUE}🔍 Проверка что сервер работает...${NC}"
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${RED}❌ Сервер не работает!${NC}"
    echo "Запустите в другом терминале:"
    echo "  cd /workspaces/lab1"
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi
echo -e "${GREEN}✅ Сервер работает${NC}"
echo ""

# Получить токен
echo -e "${BLUE}📝 Получение токена...${NC}"
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Admin123","password":"Admin@123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Не удалось получить токен!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Токен получен${NC}"
echo ""

# Функция для красивого вывода результата
test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    
    echo -e "${BLUE}📌 ${name}${NC}"
    
    if [ -n "$data" ]; then
        RESPONSE=$(curl -s -X $method "http://localhost:8000${url}" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        RESPONSE=$(curl -s -X $method "http://localhost:8000${url}" \
            -H "Authorization: Bearer $TOKEN")
    fi
    
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""
}

# ТЕСТЫ

echo "════════════════════════════════════════════════════════════════"
echo "1️⃣  ПОЛУЧЕНИЕ РОЛЕЙ"
echo "════════════════════════════════════════════════════════════════"
test_endpoint "GET /api/ref/policy/role" "GET" "/api/ref/policy/role?limit=3"

echo "════════════════════════════════════════════════════════════════"
echo "2️⃣  ПОЛУЧЕНИЕ РАЗРЕШЕНИЙ"
echo "════════════════════════════════════════════════════════════════"
test_endpoint "GET /api/ref/policy/permission" "GET" "/api/ref/policy/permission?limit=3"

echo "════════════════════════════════════════════════════════════════"
echo "3️⃣  ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЕЙ"
echo "════════════════════════════════════════════════════════════════"
test_endpoint "GET /api/ref/user" "GET" "/api/ref/user"

echo "════════════════════════════════════════════════════════════════"
echo "4️⃣  ПОЛУЧЕНИЕ РОЛЕЙ ПОЛЬЗОВАТЕЛЯ (ID=1)"
echo "════════════════════════════════════════════════════════════════"
test_endpoint "GET /api/ref/user/1/role" "GET" "/api/ref/user/1/role"

echo "════════════════════════════════════════════════════════════════"
echo "5️⃣  СОЗДАНИЕ НОВОЙ РОЛИ"
echo "════════════════════════════════════════════════════════════════"
test_endpoint "POST /api/ref/policy/role" "POST" "/api/ref/policy/role" \
    '{"name":"TestRole","slug":"test-role","description":"Test role for testing"}'

echo "════════════════════════════════════════════════════════════════"
echo "6️⃣  СОЗДАНИЕ НОВОГО РАЗРЕШЕНИЯ"
echo "════════════════════════════════════════════════════════════════"
test_endpoint "POST /api/ref/policy/permission" "POST" "/api/ref/policy/permission" \
    '{"name":"Test Permission","slug":"test-perm","description":"Test permission"}'

echo "════════════════════════════════════════════════════════════════"
echo "7️⃣  ТЕСТИРОВАНИЕ 403 ОШИБКИ (без разрешения)"
echo "════════════════════════════════════════════════════════════════"

# Получить токен ограниченного пользователя
echo -e "${BLUE}Получение токена ограниченного пользователя...${NC}"
LIMITED_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"LimitedUser","password":"LimitedPass123!@#"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -n "$LIMITED_TOKEN" ]; then
    echo -e "${BLUE}📌 Попытка создать роль без разрешения (должна быть ошибка 403)${NC}"
    RESPONSE=$(curl -s -X POST "http://localhost:8000/api/ref/policy/role" \
        -H "Authorization: Bearer $LIMITED_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name":"Should Fail","slug":"should-fail"}')
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    echo ""
else
    echo -e "${YELLOW}⚠️  Не удалось получить токен ограниченного пользователя${NC}"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════"
echo "✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 Советы:"
echo "  • Для веб-интерфейса откройте: http://localhost:8000/docs"
echo "  • Сохраните этот токен для дальнейшего тестирования:"
echo "    TOKEN=$TOKEN"
echo ""
echo "📖 Полное руководство в файле: TESTING_GUIDE.md"
