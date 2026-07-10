import requests
from playwright.sync_api import sync_playwright
import time
import random

# Ссылки возвращены в русло ЗАКАЗЧИКОВ (Вакансии/Подработки), но строго от ЧАСТНЫХ ЛИЦ (&user=1)
TASKS = [
    {
        "category": "Частные Заказчики: Сборщик мебели (Разовый заказ)",
        "target": "lead",
        "strict_filter": True,
        # Ищем в вакансиях, но параметр user=1 отсекает агентства и оставляет обычных людей
        "url": "https://www.avito.ru/moskva/vakansii?q=сборщик+мебели&user=1"
    },
    {
        "category": "Частные Заказчики: Поиск по действию (Собрать мебель)",
        "target": "lead",
        "strict_filter": True, 
        "url": "https://www.avito.ru/moskva/vakansii?q=собрать+мебель&user=1"
    },
    {
        "category": "Частные Заказчики: Срочная подработка",
        "target": "lead",
        "strict_filter": True, 
        "url": "https://www.avito.ru/moskva/vakansii?q=подработка+сборка+мебели&user=1"
    }
]

# БЕЛЫЙ СПИСОК: Пропускаем только то, что связано с мебелью и сборкой
ALLOWED_KEYWORDS = [
    "нужно собрать мебель"
"собрать шкаф"
"сборка кухни"
"шкаф не влезает"
"разобрать шкаф"после переезда
"после ремонта"
"самовывоз мебели"
"шкаф купе разобрать"
"перевезти мебель"
"освободить квартиру"
"вынести мебель"
]

# ЧЕРНЫЙ СПИСОК: Жестко выкашиваем HR-спам, вакансии, заводы и левые ниши
BANNED_KEYWORDS = [
    "заказ", "день\\вечер", "день/вечер", "без опыта", "16+", "18+",
    "обед", "повар", "курьер", "даркстор", "достав", "водитель", 
    "грузчик", "комплектовщик", "упаковщик", "склад", "клининг", 
    "фасовщик", "яндекс", "самокат", "озон", "дрон", "бпла", 
    "беспилотник", "тыл", "сво", "косметика", "канцтовар", 
    "бижутерия", "аппарат", "германия", "продукции", "бус",
    # Дополнительный щит от b2b-вакансий:
    "вакансия", "график", "оклад", "смена", "тк рф", "оформление",
    "производство", "в цех", "фабрика", "приглашаем", "требуются",
    "работа в", "прямой работодатель", "зп", "зарплата"
]

def extract_tags(text):
    text_low = text.lower()
    tags = []
    if any(x in text_low for x in ["столешн", "врезка"]): tags.append("Столешницы")
    if any(x in text_low for x in ["кухн", "кухон"]): tags.append("Кухни")
    if any(x in text_low for x in ["шкаф", "купе", "гардероб"]): tags.append("Шкафы")
    if any(x in text_low for x in ["корпус", "стеллаж"]): tags.append("Корпусная")
    return ",".join(tags) if tags else "Сборка"

def send_to_crm(lead_data, target):
    try:
        endpoint = "/api/add_lead" if target == "lead" else "/api/add_master"
        response = requests.post(f"http://127.0.0.1:8000{endpoint}", json=lead_data, timeout=10)
        if response.status_code == 200:
            print(f"[CRM] [+] ЧАСТНЫЙ ЗАКАЗ добавлен: {lead_data['title'][:40]}")
    except Exception as e:
        print(f"[CRM] Ошибка отправки: {e}")

def parse_category(page, task):
    print(f"\n[*] Прочесываем направление: {task['category']}...")
    page.goto(task['url'])
    time.sleep(random.uniform(5.0, 7.0)) # Безопасная пауза, чтобы Авито прогрузился
    
    # Ищем карточки объявлений
    items = page.query_selector_all('[data-marker="catalog-serp"] div[data-marker="item"]') or page.query_selector_all('div[data-marker="item"]')
    print(f"[*] Всего объявлений на странице: {len(items)}")
    
    for item in items:
        link_el = item.query_selector('a[data-marker="item-title"]') or item.query_selector('a')
        if not link_el:
            continue
            
        title = link_el.inner_text().strip().replace('\n', ' ')
        title_low = title.lower()
        
        # --- ФИЛЬТР КОМПАНИЙ, ЮРЛИЦ И АГЕНТСТВ ---
        seller_el = item.query_selector('[data-marker="item-badge"]') or item.query_selector('span[class*="company"]') or item.query_selector('[data-marker="seller-info/label"]')
        if seller_el:
            seller_text = seller_el.inner_text().lower()
            if any(x in seller_text for x in ["компания", "агентство", "проверенный партнер", "работодатель", "юридическое лицо"]):
                continue  # Скидываем коммерцию сразу
        
        # --- ФИЛЬТРАЦИЯ ТЕКСТОВОГО ШУМА ---
        if task["strict_filter"]:
            # 1. Защита от мусора из черного списка
            if any(b_kw in title_low for b_kw in BANNED_KEYWORDS):
                continue
            # 2. Проверка на соответствие белому списку
            if not any(a_kw in title_low for a_kw in ALLOWED_KEYWORDS):
                continue
        
        href = link_el.get_attribute('href')
        if href and "/images/" not in href:
            link = "https://www.avito.ru" + href.split('?')[0]
            
            geo_el = item.query_selector('[data-marker="item-address"]') or item.query_selector('div[class*="geo-root"]')
            metro = geo_el.inner_text().strip().split(',')[0] if geo_el else "Москва"
            
            source_id = item.get_attribute('data-item-id') or href.split('/')[-1]
            
            lead_data = {
                "source_id": str(source_id),
                "category": "Сборка мебели",
                "title": title,
                "description": "Прямой заказ от частного клиента (требуется сборка)",
                "metro": metro,
                "district": "Уточняется",
                "link": link,
                "tags": extract_tags(title)
            }
            send_to_crm(lead_data, task["target"])

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"]) 
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        for task in TASKS:
            try: 
                parse_category(page, task)
            except Exception as e: 
                print(f"[-] Ошибка при обработке категории: {e}")
        browser.close()

if __name__ == "__main__":
    run()
