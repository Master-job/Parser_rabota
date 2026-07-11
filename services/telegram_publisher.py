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
    if not os.path.exists(SENT_LINKS_FILE):
        return set()

    with open(SENT_LINKS_FILE, "r", encoding="utf-8") as f:
        return set(
            line.strip()
            for line in f
            if line.strip()
        )


def save_sent_link(link):
    with open(SENT_LINKS_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def send_message(text):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

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


def create_post(item):

    title = item.get("title", "Вакансия")
    score = item.get("score", 0)
    link = item.get("link", "")

    # чистим длинный хвост Avito
    if "?" in link:
        link = link.split("?")[0]

    post = f"""🔥 {title.upper()}

📍 Москва

💰 Оплата:
{item.get("salary", "Указана в вакансии")}

🛠 Направление:
Сборка и монтаж мебели

⭐ Рейтинг:
{score}/100

👇 Открыть вакансию:
{link}

#работаМосква #сборщикмебели #монтажникмебели #кухни"""

    return post


def run():

    if not os.path.exists(INPUT_FILE):
        print("Нет файла:", INPUT_FILE)
        return


    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        posts = json.load(f)


    sent_links = load_sent_links()

    sent = 0


    for item in posts:

        link = item.get("link")

        if not link:
            continue


        if link in sent_links:
            print(
                "⏩ Уже было:",
                item.get("title")
            )
            continue


        score = item.get(
            "score",
            0
        )


        if score < MIN_SCORE:
            continue


        post = create_post(item)


        result = send_message(post)


        if result.get("ok"):

            print(
                "✅ Отправлено:",
                item.get("title")
            )

            save_sent_link(link)

            sent += 1


        else:

            print(
                "❌ Ошибка:",
                result
            )


    print("====================")
    print(
        "Отправлено:",
        sent
    )


if __name__ == "__main__":
    run()
