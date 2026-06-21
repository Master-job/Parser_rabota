import os
import time
import requests
from bs4 import BeautifulSoup
from threading import Thread
from flask import Flask, request, redirect
from database import init_db, save_post, post_exists, get_posts, get_stats, get_channels, add_channel

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = 600

# Твои списки ключевых слов
ORDER_WORDS = ["сборка", "собрать", "шкаф", "кухня", "комод", "кровать", "стол", "тумба", "монтаж мебели", "сборка мебели"]
VACANCY_WORDS = ["требуется сборщик", "ищем сборщика", "вакансия", "работа сборщик мебели", "монтажник мебели"]

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        new_ch = request.form.get("channel_name")
        if new_ch:
            add_channel(new_ch)
        return redirect("/")

    stats = get_stats()
    channels = get_channels()
    
    # Формируем красивый список каналов для админки
    channels_html = "".join([f"<li>@{ch}</li>" for ch in channels])

    return f"""
    <html>
    <head><title>Furniture CRM</title></head>
    <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>Furniture CRM Панель</h1>
        <p><b>Всего записей в базе:</b> {stats['total']}</p>
        <p><b>Заказов найдено:</b> {stats['orders']}</p>
        <p><b>Вакансий найдено:</b> {stats['vacancies']}</p>
        <hr>
        <h2>🚪 Ходить по всем дверям (Управление каналами)</h2>
        <form method="POST" style="margin-bottom: 20px;">
            <input type="text" name="channel_name" placeholder="Вставь имя канала или ссылку" style="padding: 8px; width: 300px;" required>
            <button type="submit" style="padding: 8px 15px; cursor: pointer;">Добавить в парсинг</button>
        </form>
        <h3>Сейчас сканируются каналы ({len(channels)}):</h3>
        <ul>{channels_html}</ul>
        <hr>
        <a href='/orders' style="font-size: 18px; margin-right: 20px;">📂 Открыть Заказы</a>
        <a href='/vacancies' style="font-size: 18px;">💼 Открыть Вакансии</a>
    </body>
    </html>
    """

@app.route("/orders")
def orders():
    posts = get_posts("ORDER")
    html = "<h1>Заказы</h1><a href='/'>Назад на главную</a><hr>"
    for post in posts:
        html += f"""
        <div style='margin-bottom:20px'>
        <a href='{post['url']}' target='_blank'>Открыть в Telegram</a><br>
        <b>Источник: @{post['channel']}</b><br>
        <p>{post['text'][:500]}</p>
        </div>
        <hr>
        """
    return html

@app.route("/vacancies")
def vacancies():
    posts = get_posts("VACANCY")
    html = "<h1>Вакансии</h1><a href='/'>Назад на главную</a><hr>"
    for post in posts:
        html += f"""
        <div style='margin-bottom:20px'>
        <a href='{post['url']}' target='_blank'>Открыть в Telegram</a><br>
        <b>Источник: @{post['channel']}</b><br>
        <p>{post['text'][:500]}</p>
        </div>
        <hr>
        """
    return html

def send_telegram_notification(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print(f"[!] Ошибка отправки сообщения: {e}", flush=True)

def detect_type(text):
    lower = text.lower()
    if any(x in lower for x in VACANCY_WORDS):
        return "VACANCY"
    if any(x in lower for x in ORDER_WORDS):
        return "ORDER"
    return None

def parse_channels():
    # Загружаем актуальный список каналов прямо из базы данных перед каждым кругом!
    channels_to_parse = get_channels()
    print(f"\n[*] SCAN START. Проверяю каналов: {len(channels_to_parse)}", flush=True)
    headers = {"User-Agent": "Mozilla/5.0"}

    for channel in channels_to_parse:
        try:
            url = f"https://t.me/s/{channel}"
            response = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")

            for msg in messages:
                post_id = msg.get("data-post")
                if not post_id or post_exists(post_id):
                    continue

                text_block = msg.find("div", class_="tgme_widget_message_text")
                if not text_block:
                    continue

                text = text_block.get_text(separator="\n").strip()
                post_type = detect_type(text)

                if not post_type:
                    continue

                link = msg.find("a", class_="tgme_widget_message_date")
                post_url = link.get("href") if link else f"https://t.me/{post_id}"

                save_post(post_id, post_type, channel, text, post_url)

                # Защита от кривых HTML-тегов при обрезке
                truncated_text = text[:3000]
                icon = "💼" if post_type == "VACANCY" else "🔥"
                
                flash_message = f"<b>{icon} {post_type}</b>\n\n<i>{truncated_text}</i>\n\n🔗 <a href='{post_url}'>Открыть источник</a>"
                
                send_telegram_notification(flash_message)
                print(f"[+] Saved post {post_id} from @{channel}", flush=True)
                time.sleep(1)

        except Exception as e:
            print(f"[!] Error processing channel {channel}: {e}", flush=True)

def parser_loop():
    time.sleep(5)
    while True:
        try:
            parse_channels()
        except Exception as e:
            print(f"[CRITICAL] Loop error: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    init_db()
    
    parser_thread = Thread(target=parser_loop)
    parser_thread.daemon = True
    parser_thread.start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)