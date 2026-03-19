import sqlite3

print("📦 Подключаюсь к users.db...")
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

print("📝 Создаю таблицу users...")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        birthday TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
''')

conn.commit()
print("✅ Таблица users создана!")

# Проверим что таблица есть
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if cursor.fetchone():
    print("✅ Таблица users существует в БД")

conn.close()
