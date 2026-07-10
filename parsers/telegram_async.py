# parsers/telegram_async.py
import os
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8912127798:AAGD9HHuokyYOD6UF6JkUkprZrxSaxOKo8o")
RENDER_SERVER_URL = os.getenv('RENDER_SERVER_URL', 'https://parser-rabota.onrender.com/add_lead')

# Ключевые слова для фильтрации заказов
KEYWORDS = re.compile(r'(сборка|собрать|мебель|шкаф|кухн|кроват|комод|столешн|тумб|прихож|навесить|повесить)', re.IGNORECASE)
STOP_WORDS = ["ищу работу", "резюме", "соберу", "предлагаю услуги"]

# Инициализируем бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

print("🚀 Telegram-бот запущен и готов к работе...")

def send_to_crm(payload):
    try:
        response = requests.post(RENDER_SERVER_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Заказ успешно отправлен в CRM: {payload['title']}")
    except Exception as err:
        print(f"❌ Ошибка отправки в CRM: {err}")

# Ловим ВСЕ сообщения из чатов, где сидит бот
@dp.message_handler()
async def handle_messages(message: types.Message):
    text = message.text
    if not text:
        return

    lower_text = text.lower()
    if any(stop in lower_text for stop in STOP_WORDS):
        return

    if KEYWORDS.search(text):
        chat_title = message.chat.title or "Приватный чат"
        
        # Ссылка на сообщение
        if message.chat.username:
            link = f"https://t.me/{message.chat.username}/{message.message_id}"
        else:
            # Для закрытых чатов
            link = f"https://t.me/c/{str(message.chat.id).replace('-100', '')}/{message.message_id}"

        lines = text.split('\n')
        title = lines[0][:50] + "..." if len(lines[0]) > 50 else lines[0]

        print(f"\n🎯 Бот поймал заказ в чате [{chat_title}]!")

        payload = {
            'title': f"TG: {title}",
            'description': text,
            'category': 'Сборка мебели',
            'subcategory': 'Лид из Telegram-чата',
            'metro': 'Уточняется',
            'district': 'Москва',
            'source': 'telegram',
            'link': link
        }

        send_to_crm(payload)
        
async def parse_channels_async():
    """
    Совместимость с CRM.
    Telegram-бот работает через polling отдельно.
    Здесь возвращаем пустой список,
    чтобы FastAPI мог запуститься.
    """
    return []
    
if __name__ == '__main__':
    # Перед запуском убедись, что библиотека aiogram установлена: pip install aiogram==2.25.1
    executor.start_polling(dp, skip_updates=True)
