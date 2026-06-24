import os
import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

try:
    from database_v2 import db
except ImportError:
    from database_v2 import DatabaseManager
    db = DatabaseManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    async with db.pool.acquire() as conn:
        print("🛠️ Настройка двухъядерной базы данных PostgreSQL...")
        
        # КРЫЛО 1: Таблица для реальных заказов (Вакансий)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                source_id TEXT UNIQUE,
                category TEXT,
                title TEXT,
                description TEXT,
                metro TEXT,
                district TEXT,
                link TEXT,
                tags TEXT, 
                status TEXT DEFAULT 'Новый',
                worker_id INTEGER,
                worker_name TEXT
            )
        """)
        
        # КРЫЛО 2: Таблица для конкурентов (Твой будущий SaaS продукт)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scraped_masters (
                id SERIAL PRIMARY KEY,
                source_id TEXT UNIQUE,
                category TEXT,
                title TEXT,
                description TEXT,
                metro TEXT,
                district TEXT,
                link TEXT,
                tags TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("CREATE TABLE IF NOT EXISTS workers (id SERIAL PRIMARY KEY, name TEXT UNIQUE)")
        
        workers_count = await conn.fetchval("SELECT COUNT(*) FROM workers")
        if workers_count == 0:
            await conn.execute("""
                INSERT INTO workers (name) VALUES 
                ('Иван (Сборщик Кухонь)'), ('Сергей (Шкафы-Купе)'), ('Алексей (Универсал)')
            """)

        # 🔥 АВТО-МИГРАЦИЯ: Наводим порядок прямо сейчас
        masters_in_saas = await conn.fetchval("SELECT COUNT(*) FROM scraped_masters")
        if masters_in_saas == 0:
            leads_count = await conn.fetchval("SELECT COUNT(*) FROM leads")
            if leads_count > 0:
                print("🚚 Опаньки! Обнаружены старые мастера в таблице заказов. Переносим их в SaaS...")
                await conn.execute("""
                    INSERT INTO scraped_masters (source_id, category, title, description, metro, district, link, tags)
                    SELECT source_id, category, title, description, metro, district, link, tags FROM leads
                    ON CONFLICT (source_id) DO NOTHING
                """)
                await conn.execute("DELETE FROM leads")
                print("🎯 Успешно! Теперь вкладка заказов пуста и готова принимать реальную работу.")

        print("✅ База данных полностью готова к работе!")
    yield
    if db.pool: await db.pool.close()

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
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO leads (source_id, category, title, description, metro, district, link, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT (source_id) DO NOTHING
        """, lead.source_id, lead.category, lead.title, lead.description, lead.metro, lead.district, lead.link, lead.tags)
    return {"status": "success", "target": "orders_pool"}

@app.post("/api/add_master")
async def add_master(master: ScrapeModel):
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO scraped_masters (source_id, category, title, description, metro, district, link, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT (source_id) DO NOTHING
        """, master.source_id, master.category, master.title, master.description, master.metro, master.district, master.link, master.tags)
    return {"status": "success", "target": "saas_pool"}

@app.post("/api/assign_worker")
async def assign_worker(lead_id: int = Form(...), worker_id: int = Form(...)):
    async with db.pool.acquire() as conn:
        worker_name = await conn.fetchval("SELECT name FROM workers WHERE id = $1", worker_id)
        await conn.execute("UPDATE leads SET status='В работе', worker_id=$1, worker_name=$2 WHERE id=$3", worker_id, worker_name, lead_id)
    return RedirectResponse(url="/?tab=orders", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    tab = request.query_params.get("tab", "orders")
    
    try:
        # Пытаемся получить данные
        async with db.pool.acquire() as conn:
            leads = await conn.fetch("SELECT * FROM leads ORDER BY id DESC")
            masters = await conn.fetch("SELECT * FROM scraped_masters ORDER BY id DESC")
            workers = await conn.fetch("SELECT id, name FROM workers ORDER BY id ASC")
    except Exception as e:
        print(f"⚠️ Ошибка базы данных, реконект: {e}")
        # Если база отвалилась — пробуем переинициализировать пул
        await db.pool.close()
        await db.init_pool()
        return HTMLResponse("<h1>База данных переподключается, обнови страницу через 2 секунды</h1>", status_code=503)

    # ... далее идет твой код отрисовки HTML (orders_rows, etc.) ...
    orders_rows = ""
    for r in leads:
        tag_badges = "".join([f'<span class="badge bg-primary me-1">{t}</span>' for t in r['tags'].split(',') if t])
        action = f'<span class="badge bg-indigo text-white">👷 {r["worker_name"]}</span>' if r['status'] != 'Новый' else f"""
            <form action="/api/assign_worker" method="post" class="d-flex gap-1 mb-0">
                <input type="hidden" name="lead_id" value="{r['id']}">
                <select name="worker_id" class="form-select form-select-sm" required>
                    {"".join([f'<option value="{w["id"]}">{w["name"]}</option>' for w in workers])}
                </select>
                <button type="submit" class="btn btn-sm btn-dark">ОТПРАВИТЬ</button>
            </form>
        """
        orders_rows += f"<tr><td>#{r['id']}</td><td>{r['title']} <a href='{r['link']}' target='_blank'>↗</a><br>{tag_badges}</td><td>📍 {r['metro']}</td><td>{action}</td></tr>"

    masters_rows = ""
    for r in masters:
        tag_badges = "".join([f'<span class="badge bg-warning text-dark me-1">{t}</span>' for t in r['tags'].split(',') if t])
        masters_rows += f"<tr><td>#{r['id']}</td><td class='fw-semibold'>{r['title']} <a href='{r['link']}' target='_blank'>↗</a><br>{tag_badges}</td><td>📍 {r['metro']}</td><td><span class='badge bg-success-subtle text-success border border-success-subtle'>Доступен для SaaS</span></td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>LEAD-GENERATOR PRO v3.0</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: #f8fafc; font-family: system-ui, sans-serif; }}
            .nav-pills .nav-link.active {{ background-color: #4f46e5 !important; }}
            .crm-card {{ background: white; border-radius: 14px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h1 class="fw-bold text-dark m-0">LEAD-GENERATOR PRO <span class="text-primary fs-4">v3.0</span></h1>
                    <p class="text-muted m-0">Двухъядерная экосистема: Раздельный сбор Лидов и Конкурентов</p>
                </div>
            </div>

            <ul class="nav nav-pills mb-4 bg-white p-2 border rounded-3 d-inline-flex">
                <li class="nav-item"><a class="nav-link {"active" if tab=="orders" else ""}" href="/?tab=orders">💼 Матрица Заказов ({len(leads)})</a></li>
                <li class="nav-item"><a class="nav-link {"active" if tab=="masters" else ""}" href="/?tab=masters">🚀 База Мастеров / SaaS ({len(masters)})</a></li>
            </ul>

            <div class="crm-card p-4">
                <table class="table align-middle table-hover">
                    {f'''<thead><tr><th>ID</th><th>Реальный Заказ (Вакансия)</th><th>Локация</th><th>Назначение бригады</th></tr></thead><tbody>{orders_rows}</tbody>''' if tab=="orders" else f'''<thead><tr><th>ID</th><th>Профиль Конкурента (Твой SaaS)</th><th>Локация</th><th>Статус</th></tr></thead><tbody>{masters_rows}</tbody>'''}
                </table>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)