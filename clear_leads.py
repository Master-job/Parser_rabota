import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Загружаем настройки из твоего файла .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def clear_table():
    print("⏳ Подключаемся к базе данных через твой DATABASE_URL...")
    
    if not DATABASE_URL:
        print("❌ Ошибка: Переменная DATABASE_URL не найдена в файле .env!")
        return

    try:
        # Подключаемся точно так же, как твоя CRM
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🧹 Очищаем таблицу лидов от старого мусора...")
        await conn.execute("TRUNCATE TABLE leads RESTART IDENTITY CASCADE;")
        
        print("✅ БАЗА ПОЛНОСТЬЮ ОЧИЩЕНА! В CRM теперь идеальная чистота.")
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при очистке базы: {e}")

if __name__ == "__main__":
    asyncio.run(clear_table())