# main.py
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
import aiohttp

from database_v2 import DatabaseManager
from matcher import SmartMatcher
from parsers.telegram_async import parse_channels_async
from parsers.avito_async import parse_avito_async

# ===== СХЕМЫ ВАЛИДАЦИИ (Pydantic v2 FIX) =====
class UserCreate(BaseModel):
    username: str
    full_name: str
    phone: str
    role: str = Field(..., pattern="^(customer|executor|both)$")
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ExecutorProfileCreate(BaseModel):
    category: str
    subcategories: List[str]
    experience_years: int
    min_price: int
    max_travel_distance: int
    portfolio_urls: Optional[List[str]] = []
    work_schedule: str = Field(..., pattern="^(full_time|part_time|weekend)$")

class CustomerRequestCreate(BaseModel):
    title: str
    description: str
    category: str
    subcategory: str
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    deadline: Optional[date] = None
    metro: str
    district: str
    is_urgent: bool = False

class ResponseCreate(BaseModel):
    request_id: int
    message: str
    proposed_price: int
    proposed_timeline: str

# ===== ИНИЦИАЛИЗАЦИЯ И LIFESPAN =====
security = HTTPBearer()
db = DatabaseManager()
matcher = SmartMatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 LEAD GENERATOR PRO v3.0: Инициализация ресурсов...")
    await db.init_pool()
    # Запуск фонового циклического парсинга
    asyncio.create_task(background_parsers_loop())
    yield
    await db.close_pool()
    print("👋 Ресурсы пула очищены. Сервер остановлен.")

app = FastAPI(
    title="LEAD GENERATOR PRO v3.0",
    version="3.0.0",
    lifespan=lifespan
)

@app.get("/")
async def home():
    return {
        "status": "online",
        "service": "LEAD GENERATOR PRO v3.0",
        "database": "connected"
    }
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== МЕНЕДЖЕР ВЕБСОКЕТОВ =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

# ===== ВСПОМОГАТЕЛЬНЫЕ ФОНОВЫЕ ФУНКЦИИ =====
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    user = await db.verify_token(token.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен")
    return user

async def background_parsers_loop():
    """Фоновый неблокирующий сборщик лидов"""
    while True:
        print(f"[*] [{datetime.now().strftime('%H:%M:%S')}] Старт сессии парсинга...")
        try:
            # Сбор с Авито
            avito_leads = await parse_avito_async()
            for lead in avito_leads:
                inserted = await db.save_parsed_lead(lead)
                if inserted:
                    await manager.active_connections.get(1) # Пример рассылки админу или в общий канал
                    
            # Сбор с Telegram-каналов
            tg_leads = await parse_channels_async()
            for lead in tg_leads:
                await db.save_parsed_lead(lead)
                
        except Exception as e:
            print(f"[CRITICAL Ошибка парсинга в цикле]: {e}")
        await asyncio.sleep(300)  # Сон 5 минут

async def process_matching(request_id: int):
    """Асинхронный интеллектуальный мэтчинг заявок"""
    print(f"[Мэтчинг] Анализ новой заявки #{request_id}")
    request = await db.get_request(request_id)
    if request:
        executors = await matcher.find_best_executors(request)
        for exec_id in executors:
            await manager.send_personal_message(
                f"Для вас найдена новая релевантная заявка: {request['title']}", 
                exec_id
            )

async def notify_customer(request_id: int, executor_id: int):
    """Уведомление о новом отклике СТРОГО в Telegram-канал"""
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")  # ID канала, например -100xxxxxxxxxx
    if tg_token and channel_id:
        text = f"🔔 **Новый отклик на платформе!**\nИсполнитель ID {executor_id} откликнулся на заявку #{request_id}."
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(url, json={"chat_id": channel_id, "text": text, "parse_mode": "Markdown"})
            except Exception as e:
                print(f"Ошибка отправки уведомления в TG-канал: {e}")

# ===== РОУТЫ API =====
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    user_id = await db.create_user(user_data)
    token = await db.generate_token(user_id)
    return {"token": token, "user_id": user_id}

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    user = await db.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    token = await db.generate_token(user['id'])
    return {"token": token, "user": user}

@app.post("/api/requests/create")
async def create_request(request_data: CustomerRequestCreate, user: dict = Depends(get_current_user)):
    if user['role'] not in ['customer', 'both']:
        raise HTTPException(status_code=403, detail="Доступно только для заказчиков")
    request_id = await db.create_request(user['id'], request_data)
    asyncio.create_task(process_matching(request_id))
    return {"request_id": request_id, "status": "created"}

@app.post("/api/executor/respond")
async def respond_to_request(response: ResponseCreate, user: dict = Depends(get_current_user)):
    # Логика создания отклика ...
    asyncio.create_task(notify_customer(response.request_id, user['id']))
    return {"status": "sent"}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Получено: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
