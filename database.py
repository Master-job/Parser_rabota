import os
import psycopg2

# Render сам выдаст эту переменную, когда ты привяжешь базу данных
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица постов (в PostgreSQL используем SERIAL вместо AUTOINCREMENT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        post_id TEXT UNIQUE,
        post_type TEXT,
        channel TEXT,
        text TEXT,
        url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблица каналов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE
    )
    """)

    # Автозаполнение базовыми каналами при первом старте
    cursor.execute("SELECT COUNT(*) FROM channels")
    if cursor.fetchone()[0] == 0:
        default_channels = ["poisk_masterov", "rabota_sbor_mebel"]
        for ch in default_channels:
            cursor.execute("INSERT INTO channels (username) VALUES (%s) ON CONFLICT (username) DO NOTHING", (ch,))
            
    conn.commit()
    cursor.close()
    conn.close()

def post_exists(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM posts WHERE post_id = %s", (post_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def save_post(post_id, post_type, channel, text, url):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO posts (post_id, post_type, channel, text, url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (post_id) DO NOTHING
        """, (post_id, post_type, channel, text, url))
        conn.commit()
    except Exception as e:
        print(f"[!] Ошибка сохранения поста в Postgres: {e}", flush=True)
    finally:
        cursor.close()
        conn.close()

def get_posts(post_type=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if post_type:
        cursor.execute("SELECT post_id, post_type, channel, text, url FROM posts WHERE post_type = %s ORDER BY id DESC LIMIT 500", (post_type,))
    else:
        cursor.execute("SELECT post_id, post_type, channel, text, url FROM posts ORDER BY id DESC LIMIT 500")
    
    rows = cursor.fetchall()
    
    # Формируем список словарей, чтобы main.py читал поля по именам
    posts = []
    for row in rows:
        posts.append({
            "post_id": row[0],
            "post_type": row[1],
            "channel": row[2],
            "text": row[3],
            "url": row[4]
        })
        
    cursor.close()
    conn.close()
    return posts

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM posts")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type='ORDER'")
    orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type='VACANCY'")
    vacancies = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return {"total": total, "orders": orders, "vacancies": vacancies}

def get_channels():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM channels ORDER BY id DESC")
    channels = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return channels

def add_channel(username):
    username = username.strip().replace("@", "").replace("https://t.me/s/", "").replace("https://t.me/", "")
    if not username:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO channels (username) VALUES (%s) ON CONFLICT (username) DO NOTHING", (username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()
        def delete_channel(username):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM channels WHERE username = %s", (username,))
        conn.commit()
    except Exception as e:
        print(f"[!] Ошибка удаления канала: {e}")
    finally:
        cursor.close()
        conn.close()