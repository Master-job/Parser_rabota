# parsers/telegram_async.py
import os
import re
from telethon import TelegramClient
from typing import List, Dict

async def parse_channels_async() -> List[Dict]:
    """Асинхронный парсер Telegram-каналов/чатов заказов с использованием Telethon"""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_name = 'lead_generator_session'
    
    if not api_id or not api_hash:
        print("⚠️ Скип парсинга TG: Переменные TELEGRAM_API_ID или TELEGRAM_API_HASH не заданы.")
        return []
        
    # Инициализируем асинхронный клиент
    client = TelegramClient(session_name, int(api_id), api_hash)
    leads = []
    
    # Целевые каналы для мониторинга заказов (можно вынести в конфиг или БД)
    target_channels = ['@mebel_orders_moscow', '@rabota_sborka_mebeli', '@master_na_chas_msk']
    
    # Ключевые слова для валидации лида
    keywords = re.compile(r'(сборка|собрать|мебель|шкаф|кухн|кроват|комод|столешн)', re.IGNORECASE)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ Telethon: Клиент не авторизован. Требуется ручной запуск авторизации.")
            return []
            
        for channel in target_channels:
            try:
                # Читаем последние 10 сообщений из каждого канала
                async for message in client.iter_messages(channel, limit=10):
                    if message.text and keywords.search(message.text):
                        # Генерируем прямую ссылку на пост
                        channel_username = channel.replace('@', '')
                        link = f"https://t.me/{channel_username}/{message.id}"
                        
                        # Извлекаем первую строку текста в качестве заголовка
                        lines = message.text.split('\n')
                        title = lines[0][:60] + "..." if len(lines[0]) > 60 else lines[0]
                        
                        leads.append({
                            'title': title,
                            'description': message.text,
                            'category': 'Сборка мебели',
                            'subcategory': 'Лид из Telegram',
                            'metro': 'Уточняется',
                            'district': 'Москва',
                            'source': 'telegram',
                            'link': link
                        })
            except Exception as ch_err:
                print(f"Ошибка чтения канала {channel}: {ch_err}")
                
    except Exception as e:
        print(f"❌ Критическая ошибка парсера Telethon: {e}")
    finally:
        await client.disconnect()
        
    print(f"✅ Telegram-парсер: Собрано {len(leads)} подходящих постов")
    return leads