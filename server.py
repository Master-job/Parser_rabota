import os
import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import aiosqlite
import asyncio
import sys

# Импортируем функцию run из твоего главного файла автоматизации
# Убедись, что путь к run_parser правильный (если он лежит в корне, то просто run_parser)
try:
    import run_parser
except ImportError:
    # Если скрипты лежат в папке services, раскомментируй строчки ниже:
    # sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))
    # import run_parser
    pass

DB_PATH = "database.db"

async def background_parser_loop():
    """Фоновый воркер, который крутит парсер без Крона 24/7"""
    # Даем серверу 10 секунд спокойно проинициализироваться при старте
    await asyncio.sleep(10)
    
    while True:
        try:
            print("\n[ФОНОВЫЙ ВОРКЕР] 🚀 Начинаю цикл парсинга Авито...")
            
            # Запускаем твой готовый конвейер (парсер -> фильтр -> скорер -> паблишер)
            # Так как run() синхронный (Playwright sync), запускаем его в отдельном потоке,
            # чтобы он не намертво не вешал сам веб-сервер FastAPI
            await asyncio.to_thread(run_parser.run)
            
            print("[ФОНОВЫЙ ВОРКЕР] ✅ Цикл завершен успешно. Сплю 30 минут...")
        except Exception as e:
            print(f"[ФОНОВЫЙ ВОРКЕР] ❌ Ошибка в цикле парсинга: {e}")
        
        # Засыпаем на 30 минут (1800 секунд)
        await asyncio.sleep(1800)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем базу и таблицы прямо при запуске
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT UNIQUE, category TEXT, title TEXT, description TEXT, metro TEXT, district TEXT, link TEXT, tags TEXT, status TEXT DEFAULT 'Новый', worker_id INTEGER, worker_name TEXT)")
        await conn.execute("CREATE TABLE IF NOT EXISTS scraped_masters (id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT UNIQUE, category TEXT, title TEXT, description TEXT, metro TEXT, district TEXT, link TEXT, tags TEXT, scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        await conn.execute("CREATE TABLE IF NOT EXISTS workers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
        await conn.commit()
    
    # Запускаем фоновую задачу парсинга в бэкграунде
    parser_task = asyncio.create_task(background_parser_loop())
    
    yield
    
    # При остановке сервера аккуратно тушим задачу
    parser_task.cancel()

app = FastAPI(title="LEAD-GENERATOR PRO v3.0", lifespan=lifespan)

class ScrapeModel(BaseModel):
    source_id: str
    category: str
    title: str
    description: str
    metro: str
    district: str
    link: str
    tags: str 

@app.post("/api/add_lead")
async def add_lead(lead: ScrapeModel):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("INSERT OR IGNORE INTO leads (source_id, category, title, description, metro, district, link, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                           (lead.source_id, lead.category, lead.title, lead.description, lead.metro, lead.district, lead.link, lead.tags))
        await conn.commit()
    return {"status": "success"}

@app.post("/api/assign_worker")
async def assign_worker(lead_id: int = Form(...), worker_id: int = Form(...)):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT name FROM workers WHERE id = ?", (worker_id,))
        worker = await cursor.fetchone()
        if worker:
            await conn.execute("UPDATE leads SET status='В работе', worker_id=?, worker_name=? WHERE id=?", (worker_id, worker[0], lead_id))
            await conn.commit()
    return RedirectResponse(url="/?tab=orders", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return HTMLResponse("<h1>Сервер запущен и работает! Фоновый парсер активен.</h1>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)