import json
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "telegram_preview.json"
SENT_FILE = "sent_ids.txt"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

MIN_SCORE = 70


def get_avito_id(link):
    """
    Из ссылки Авито получает ID объявления.
    Например:
    https://www.avito.ru/..._7634504228?context=...
    ->
    7634504228
    """
    if not link:
        return None

    match = re.search(r"_(\d+)", link)

    if match:
        return match.group(1)

    return None


def load_sent():
    if not os.path.exists(SENT_FILE):
        return set()

    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_sent(avito_id):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(avito_id + "\n")


def send_message(text):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "disable_web_page_preview": False
    }

    response = requests.post(
        url,
        data=data,
        timeout=15
    )

    return response.json()


def run():

    if not os.path.exists(INPUT_FILE):
        print("Нет файла:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    sent_ids = load_sent()

    sent = 0

    for item in posts:

        score = item.get("score", 0)

        if score < MIN_SCORE:
            continue

        link = item.get("link", "")
        avito_id = get_avito_id(link)

        if avito_id and avito_id in sent_ids:
            print("⏩ Уже публиковали:", item["title"])
            continue

        result = send_message(item["post"])

        if result.get("ok"):

            print("✅ Отправлено:", item["title"])

            sent += 1

            if avito_id:
                save_sent(avito_id)
                sent_ids.add(avito_id)

        else:

            print("❌ Ошибка:", result)

    print("====================")
    print("Отправлено:", sent)


if __name__ == "__main__":
    run()
