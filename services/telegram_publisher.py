import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()


INPUT_FILE = "telegram_preview.json"


TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHANNEL_ID = os.getenv(
    "TELEGRAM_CHANNEL_ID"
)



MIN_SCORE = 70



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



def run():


    if not os.path.exists(INPUT_FILE):

        print(
            "Нет файла:",
            INPUT_FILE
        )

        return



    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        posts = json.load(f)
                 sent = 0
        
        if already_sent(item["link"]):
            print("⏩ Уже публиковали:", item["title"])
            continue
        
            for item in posts:


        score = item.get(
            "score",
            0
        )


        if score < MIN_SCORE:

            continue



        result = send_message(
            item["post"]
        )


        if result.get("ok"):

            print(
                "✅ Отправлено:",
                item["title"]
            )

            sent += 1


        else:

            print(
                "❌ Ошибка:",
                result
            )



    print(
        "===================="
    )

    print(
        "Отправлено:",
        sent
    )



if __name__ == "__main__":

    run()
