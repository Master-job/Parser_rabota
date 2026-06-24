import time
import requests
import os
from bs4 import BeautifulSoup
from database import save_post, post_exists, get_channels

# Твои фильтры
ORDER_WORDS = ["сборка", "собрать", "монтаж"]
VACANCY_WORDS = ["требуется", "ищем", "вакансия"]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_to_telegram(text, url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Отправляем строго в Channel ID
    data = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": f"{text}\n\nИсточник: {url}"
    }
    try:
        requests.post(api_url, data=data, timeout=10)
    except Exception as e:
        print(f"[!] Ошибка отправки в ТГ: {e}")

def parse_channels():
    channels = get_channels()
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for channel in channels:
        try:
            url = f"https://t.me/s/{channel}"
            req = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(req.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")
            
            for msg in messages:
                msg_text_div = msg.find("div", class_="tgme_widget_message_text")
                if not msg_text_div:
                    continue
                    
                text = msg_text_div.get_text(separator="\n").strip()
                post_id = msg.get("data-post")
                post_url = f"https://t.me/{post_id}"
                
                if not post_id or post_exists(post_id):
                    continue
                    
                lower_text = text.lower()
                post_type = None
                
                if any(word in lower_text for word in ORDER_WORDS):
                    post_type = "ORDER"
                elif any(word in lower_text for word in VACANCY_WORDS):
                    post_type = "VACANCY"
                    
                if post_type:
                    save_post(post_id, post_type, channel, text, post_url)
                    send_to_telegram(f"[{post_type}] Новая запись!\n{text}", post_url)
        except Exception as e:
            print(f"[!] Ошибка парсинга {channel}: {e}")
        
        time.sleep(2) # Защитная пауза между каналами