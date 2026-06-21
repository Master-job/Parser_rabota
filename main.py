import os
import time
import requests
from bs4 import BeautifulSoup
from threading import Thread
from flask import Flask

# Инициализируем веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Парсер мебели активен и работает 24/7", 200

# Переменные окружения (подтягиваются из настроек Render)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ключевые слова для фильтрации заказов
KEYWORDS = ["сборка", "собрать", "мебель", "шкаф", "кухня", "кровать", "монтаж", "тумба", "стол", "комод"]
CHECK_INTERVAL = 600  # Проверка каждые 10 минут (600 секунд)

# Сюда вписываешь те самые каналы-источники из Evernote (только хвостики ссылок!)
CHANNELS_TO_PARSE = [
    "poisk_masterov", 
    "rabota_sbor_mebel"
]

# Оперативная память бота (актуально для сессий Render)
history = set()
initialized_channels = set()

def send_telegram_notification(text):
    """Отправка красивого HTML-сообщения в твой Telegram-канал"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[!] Ошибка отправки в Telegram: {e}", flush=True)
        return False

def parse_channels():
    """Основной движок парсинга объявлений"""
    print(f"\n[*] Начинаю круг сканирования: {time.strftime('%H:%M:%S')}", flush=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for channel in CHANNELS_TO_PARSE:
        url = f"https://t.me/s/{channel}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"[!] Ошибка доступа к каналу @{channel} (Код: {response.status_code})", flush=True)
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")
            
            # Проверяем, сканируем ли мы этот канал впервые с момента запуска
            is_first_run_for_channel = channel not in initialized_channels
            new_posts_count = 0
            
            for msg in messages:
                post_id = msg.get("data-post")
                if not post_id or post_id in history:
                    continue
                
                text_block = msg.find("div", class_="tgme_widget_message_text")
                if not text_block:
                    continue
                
                text = text_block.get_text(separator="\n").strip()
                
                # Поиск совпадений по ключевым словам
                if any(keyword in text.lower() for keyword in KEYWORDS):
                    link_anchor = msg.find("a", class_="tgme_widget_message_date")
                    post_url = link_anchor.get("href") if link_anchor else f"https://t.me/{post_id}"
                    
                    history.add(post_id)
                    
                    # Если канал проверяется впервые — просто запоминаем пост, чтобы не спамить старьем
                    if not is_first_run_for_channel:
                        alert_text = (
                            f"<b>🔥 НАЙДЕН ЗАКАЗ!</b>\n\n"
                            f"<b>📍 Источник:</b> @{channel}\n"
                            f"<b>🔗 Ссылка на пост:</b> <a href='{post_url}'>Открыть в TG</a>\n\n"
                            f"<b>📋 Текст объявления:</b>\n<i>{text[:2500]}</i>"
                        )
                        send_telegram_notification(alert_text)
                        new_posts_count += 1
                        time.sleep(1)  # Защита от лимитов Telegram API
                        
            if is_first_run_for_channel:
                initialized_channels.add(channel)
                print(f"[+] Канал @{channel} успешно инициализирован. Старая база зафиксирована.", flush=True)
            elif new_posts_count > 0:
                print(f"[+] Найдено и отправлено {new_posts_count} новых заказов из @{channel}", flush=True)
                
            time.sleep(2)  # Пауза между каналами
        except Exception as e:
            print(f"[!] Критическая ошибка при обработке @{channel}: {e}", flush=True)

def run_parser_loop():
    """Бесконечный фоновый цикл"""
    time.sleep(5)  # Даем Flask 5 секунд на успешный старт
    while True:
        try:
            parse_channels()
        except Exception as e:
            print(f"[CRITICAL] Сбой в основном цикле: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[CRITICAL] Переменные окружения TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не настроены!", flush=True)
        exit(1)

    # 1. Запуск парсера в отдельном изолированном потоке
    parser_thread = Thread(target=run_parser_loop)
    parser_thread.daemon = True
    parser_thread.start()
    
    # 2. Запуск Flask сервера для удержания бесплатного тарифа Render
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)