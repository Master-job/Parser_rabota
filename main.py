import os
import threading
import time
from flask import Flask, render_template, request, redirect, url_for
from database import init_db, get_posts, get_stats, get_channels, add_channel
from parsers.telegram import parse_channels

app = Flask(__name__)
CHECK_INTERVAL = 300 # 5 минут

def parser_loop():
    time.sleep(5)
    while True:
        print(f"\n[*] Запуск обхода источников: {time.strftime('%H:%M:%S')}", flush=True)
        try:
            parse_channels()
            # Сюда потом добавим parse_avito()
        except Exception as e:
            print(f"[CRITICAL] Ошибка в цикле парсера: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=parser_loop, daemon=True).start()

@app.route("/")
def index():
    stats = get_stats()
    channels = get_channels()
    posts = get_posts()
    # Flask теперь сам берет файл index.html из папки templates
    return render_template("index.html", stats=stats, channels=channels, posts=posts)

@app.route("/add_channel", methods=["POST"])
def add_channel_route():
    new_channel = request.form.get("channel_name")
    if new_channel:
        add_channel(new_channel)
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)