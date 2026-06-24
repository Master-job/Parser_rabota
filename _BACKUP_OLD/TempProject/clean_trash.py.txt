import asyncio
import asyncpg

try:
    from database_v2 import db
except ImportError:
    from database_v2 import DatabaseManager
    db = DatabaseManager()

# Список мусорных слов, по которым мы зачищаем базу
TRASH_KEYWORDS = [
    "дрон", "бпла", "беспилотник", "тыл", "сво", "косметика", 
    "канцтовар", "бижутерия", "обед", "курьер", "даркстор", 
    "достав", "водитель", "комплектовщик", "упаковщик", "склад", 
    "интернет-заказ", "клининг", "фасовщик", "аппарат", "товаров"
    "заказ", "день\\вечер", "день/вечер", "без опыта", 
    "косметика", "бижутерия", "готовой продукции"
]

async def clean_database():
    print("🧹 Запуск генеральной уборки в базе данных...")
    await db.init_pool()
    
    async with db.pool.acquire() as conn:
        # Считаем, сколько всего было заказов до чистки
        total_before = await conn.fetchval("SELECT COUNT(*) FROM leads")
        print(f"📊 Всего записей в Матрице Заказов: {total_before}")
        
        deleted_count = 0
        for keyword in TRASH_KEYWORDS:
            # Удаляем записи, где в названии (title) проскакивает мусорное слово
            result = await conn.execute(
                "DELETE FROM leads WHERE LOWER(title) LIKE $1", 
                f"%{keyword}%"
            )
            # Извлекаем количество удаленных строк из ответа СУБД (например, 'DELETE 15')
            count = int(result.split()[-1])
            if count > 0:
                print(f"❌ Удалено объявлений по ключу '{keyword}': {count}")
                deleted_count += count
                
        total_after = await conn.fetchval("SELECT COUNT(*) FROM leads")
        print("--------------------------------------------------")
        print(f"🎯 Уборка завершена!")
        print(f"🗑️ Всего удалено мусорных строк: {deleted_count}")
        print(f"💼 Осталось реальных заказов в CRM: {total_after}")

    if db.pool:
        await db.pool.close()

if __name__ == "__main__":
    asyncio.run(clean_database())