import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "telegram_preview.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
MIN_SCORE = 70
SENT_LINKS_FILE = "sent_links.txt"

def load_sent_links():
    if not os.path.exists(SENT_LINKS_FILE): return set()
    with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_sent_link(link):
    with open(SENT_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML", # ВКЛЮЧАЕМ КРАСИВЫЙ ШРИФТ И ССЫЛКИ
        "disable_web_page_preview": True # Выключаем огромную превьюшку Авито снизу, чтобы пост был компактным
    }
    try:
        response = requests.post(url, data=data, timeout=15)
        return response.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

def run():
    if not os.path.exists(INPUT_FILE):
        print("Нет файла:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    sent_links = load_sent_links()
    sent = 0

    for item in posts:
        link = item.get("link")
        if not link: continue
        
        # Очистка хвоста урла для базы данных
        if "?" in link: link = link.split("?")[0]

        if link in sent_links:
            print("⏩ Уже было отправлено:", item.get("title"))
            continue

        if item.get("score", 0) < MIN_SCORE:
            continue

        # Берем красивый HTML-пост, собранный на прошлом шаге
        post_text = item.get("post")
        if not post_text:
            continue

        result = send_message(post_text)

        if result.get("ok"):
            print("✅ Успешно опубликовано в ТГ:", item.get("title"))
            save_sent_link(link)
            sent += 1
        else:
            print("❌ Ошибка отправки:", result.get("description", result))

    print("====================")
    print("Итого отправлено новых постов:", sent)

if __name__ == "__main__":
    run()