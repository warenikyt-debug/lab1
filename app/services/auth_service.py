"""
╔═════════════════════════════════════════════════════════════════════════════╗
║ 🔵 LAB2: AUTHENTICATION & JWT - Auth Service                                ║
║                                                                              ║
║ Сервис для управления аутентификацией пользователей                        ║
║ Включает логику login, register, password change                            ║
╚═════════════════════════════════════════════════════════════════════════════╝
"""
from datetime import datetime, date
from typing import Optional, Dict
from ..models.user import (
    save_user, 
    find_user_by_username, 
    find_user_by_email, 
    find_user_by_id,
    get_all_users,
    update_user_password,
    init_db,
    User
)
from .token_service import TokenService

print(f"\n🔧 ЗАГРУЗКА AUTH_SERVICE.PY")

class AuthService:
    def __init__(self):
        self.token_service = TokenService()
        print("✅ AuthService инициализирован")
    
    def register(self, data) -> dict:
        print(f"\n🔵🔵🔵 РЕГИСТРАЦИЯ: {data.username}")
        print(f"📧 Email: {data.email}")
        
        try:
            # Проверка существования
            existing = find_user_by_username(data.username)
            if existing:
                print(f"❌ Пользователь {data.username} уже существует")
                raise ValueError("Пользователь с таким именем уже существует")
            
            existing = find_user_by_email(data.email)
            if existing:
                print(f"❌ Email {data.email} уже существует")
                raise ValueError("Пользователь с таким email уже существует")
            
            # Хешируем пароль
            print("🔐 Хешируем пароль...")
            password_hash = User.hash_password(data.password)
            print("✅ Пароль захeширован")
            
            # Сохраняем в JSON
            print("💾 Вызываем save_user...")
            user_id = save_user(
                username=data.username,
                email=data.email,
                password_hash=password_hash,
                birthday=data.birthday
            )
            print(f"✅ save_user вернул ID: {user_id}")
            
            # Получаем созданного пользователя
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("Ошибка при получении данных пользователя")
            
            print(f"✅ Регистрация успешна для ID {user_id}")
            
            # Показываем всех пользователей
            all_users = get_all_users()
            print(f"📊 Всего пользователей в БД: {len(all_users)}")
            
            return {
                'id': user_data['id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'birthday': user_data['birthday'],
                'created_at': user_data['created_at']
            }
            
        except ValueError as e:
            print(f"❌ Ошибка: {e}")
            raise
        except Exception as e:
            print(f"❌ Непредвиденная ошибка: {e}")
            raise ValueError(f"Ошибка при регистрации: {str(e)}")
    
    def login(self, username: str, password: str, ip_address: str = None) -> Optional[Dict]:
        print(f"\n🔵 ВХОД: {username}")
        
        try:
            user_data = find_user_by_username(username)
            if not user_data:
                print("❌ Пользователь не найден")
                return None
            
            print(f"✅ Пользователь найден: ID={user_data['id']}")
            
            # Create temporary User object for password verification
            temp_user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                birthday=user_data['birthday']
            )
            
            if not temp_user.verify_password(password):
                print("❌ Неверный пароль")
                return None
            
            print("✅ Пароль верный")
            
            tokens = self.token_service.create_token_pair(user_data['id'], ip_address)
            print("✅ Токены созданы")
            
            return {
                **tokens,
                "user": {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'birthday': user_data['birthday'],
                    'created_at': user_data['created_at']
                }
            }
            
        except Exception as e:
            print(f"❌ Ошибка при входе: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        return find_user_by_id(user_id)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        print(f"\n🔵 СМЕНА ПАРОЛЯ ДЛЯ ID {user_id}")
        
        try:
            user_data = find_user_by_id(user_id)
            if not user_data:
                print("❌ Пользователь не найден")
                return False
            
            # Create temporary User object for password verification
            temp_user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                birthday=user_data['birthday']
            )
            
            if not temp_user.verify_password(current_password):
                print("❌ Неверный текущий пароль")
                return False
            
            new_hash = User.hash_password(new_password)
            result = update_user_password(user_id, new_hash)
            
            if result:
                print("✅ Пароль изменен")
            else:
                print("❌ Ошибка при изменении пароля")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при смене пароля: {e}")
            return False
