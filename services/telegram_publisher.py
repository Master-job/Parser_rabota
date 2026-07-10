import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "telegram_preview.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

MIN_SCORE = 70

# Простое хранилище уже отправленных ссылок (в памяти)
# В реальном проекте лучше сохранять в файл / БД
SENT_LINKS_FILE = "sent_links.txt"


def load_sent_links():
    if not os.path.exists(SENT_LINKS_FILE):
        return set()
    with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_sent_link(link):
    with open(SENT_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def already_sent(link):
    sent = load_sent_links()
    return link in sent


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "disable_web_page_preview": False,
    }

    response = requests.post(url, data=data, timeout=15)
    return response.json()


def run():
    if not os.path.exists(INPUT_FILE):
        print("Нет файла:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    sent = 0

    for item in posts:
        # Пропускаем, если уже отправляли
        if already_sent(item["link"]):
            print("⏩ Уже публиковали:", item["title"])
            continue

        score = item.get("score", 0)
        if score < MIN_SCORE:
            print("⏩ Пропущено поscore:", item["title"], "score =", score)
            continue

        result = send_message(item["post"])

        if result.get("ok"):
            print("✅ Отправлено:", item["title"])
            sent += 1
            # Запоминаем, что эту ссылку уже отправили
            save_sent_link(item["link"])
        else:
            print("❌ Ошибка:", result)

    print("====================")
    print("Отправлено:", sent)


if __name__ == "__main__":
    run()
