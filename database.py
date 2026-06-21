import sqlite3

DB_NAME = "furniture.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица постов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT UNIQUE,
        post_type TEXT,
        channel TEXT,
        text TEXT,
        url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблица каналов для парсинга
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )
    """)

    # Проверяем, если каналов ноль — заполняем базовыми (наш дефолтный список)
    cursor.execute("SELECT COUNT(*) FROM channels")
    if cursor.fetchone()[0] == 0:
        default_channels = ["poisk_masterov", "rabota_sbor_mebel"]
        for ch in default_channels:
            cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES (?)", (ch,))
            
    conn.commit()
    conn.close()

def post_exists(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM posts WHERE post_id = ?", (post_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_post(post_id, post_type, channel, text, url):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO posts (post_id, post_type, channel, text, url)
        VALUES (?, ?, ?, ?, ?)
        """, (post_id, post_type, channel, text, url))
        conn.commit()
    except:
        pass
    finally:
        conn.close()

def get_posts(post_type=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if post_type:
        cursor.execute("SELECT * FROM posts WHERE post_type = ? ORDER BY id DESC LIMIT 500", (post_type,))
    else:
        cursor.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 500")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM posts")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type='ORDER'")
    orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type='VACANCY'")
    vacancies = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "orders": orders, "vacancies": vacancies}

# --- НОВЫЕ ФУНКЦИИ ДЛЯ КАНАЛОВ ---

def get_channels():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM channels ORDER BY id DESC")
    channels = [row[0] for row in cursor.fetchall()]
    conn.close()
    return channels

def add_channel(username):
    # Лютую ссылку превращаем в чистый юзернейм канала
    username = username.strip().replace("@", "").replace("https://t.me/s/", "").replace("https://t.me/", "")
    if not username:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES (?)", (username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()