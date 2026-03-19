import sqlite3
import os

print("🔍 ТЕСТИРОВАНИЕ БД")
print(f"Текущая папка: {os.getcwd()}")

# Пробуем создать БД в разных местах
test_paths = [
    "users.db",
    "/workspaces/lab1/users.db",
    "./users.db",
    os.path.join(os.getcwd(), "users.db")
]

for path in test_paths:
    try:
        print(f"\n--- Тестируем: {path} ---")
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        cursor.execute("INSERT INTO test (name) VALUES ('test')")
        conn.commit()
        
        cursor.execute("SELECT * FROM test")
        print(f"✅ Запись: {cursor.fetchall()}")
        
        cursor.execute("DROP TABLE test")
        conn.commit()
        conn.close()
        
        print(f"✅ УСПЕХ! Можно писать в {path}")
        print(f"   Абсолютный путь: {os.path.abspath(path)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n" + "="*50)
print("Проверка существующих .db файлов:")
os.system("find /workspaces/lab1 -name '*.db' -ls")
