import os
import threading
import time
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, get_posts, get_stats, get_channels, add_channel, delete_channel
from parsers.telegram import parse_channels
from parsers.avito import parse_avito  # 👈 Добавили импорт модуля Авито

app = Flask(__name__)
CHECK_INTERVAL = 300 # 5 минут
AVITO_URL = "https://www.avito.ru/moskva/predlozheniya_uslug/remont_i_otdelka/sborka_i_remont_mebeli/sborka_i_razborka_mebeli-ASgBAgICA0SYC8CfAcQVrPUBuqgW0syWAw?cd=1&q=%D1%81%D0%b1%D0%be%D1%80%D0%ba%D0%b0+%D0%bc%D0%b5%D0%b1%D0%b5%D0%bb%D0%b8"

def parser_loop():
    time.sleep(5)
    while True:
        print(f"\n[*] Запуск обхода источников: {time.strftime('%H:%M:%S')}", flush=True)
        try:
            # 1. Парсим телеграм
            parse_channels()
            # 2. Парсим Авито
            parse_avito(AVITO_URL)
        except Exception as e:
            print(f"[CRITICAL] Ошибка в цикле парсера: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)

# Запускаем парсер в отдельном потоке
threading.Thread(target=parser_loop, daemon=True).start()

@app.route("/")
def index():
    stats = get_stats()
    channels = get_channels()
    posts = get_posts()
    return render_template("index.html", stats=stats, channels=channels, posts=posts)

@app.route("/add_channel", methods=["POST"])
def add_channel_route():
    new_channel = request.form.get("channel_name")
    if new_channel:
        add_channel(new_channel)
    return redirect(url_for("index"))

@app.route("/delete_channel/<username>", methods=["POST"])
def delete_channel_route(username):
    delete_channel(username)
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)