import psycopg2

PASSWORD = "poker123"

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password=PASSWORD
    )
    print(f"✅ Подключено!")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE DATABASE poker_assistant")
    print("✅ База данных poker_assistant создана!")
    cur.close()
    conn.close()
except Exception as e:
    if "already exists" in str(e):
        print("✅ База уже существует!")
    else:
        print(f"❌ Ошибка: {e}")