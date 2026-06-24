import requests
from playwright.sync_api import sync_playwright
import time
import random

# Ссылки, которые ты уже дал — они работают как вечные поисковые узлы
TASKS = [
    {
        "category": "Сборка мебели (Основной контур)",
        "target": "lead",
        "strict_filter": True, # Включаем фильтрацию для всех потоков
        "url": "https://www.avito.ru/moskva/vakansii/tag/sborschik-mebeli?context=H4sIAAAAAAAA_wFNALL_YToyOntzOjg6ImZyb21QYWdlIjtzOjE2OiJzZWFyY2hGb3JtV2lkZ2V0IjtzOjE6InkiO3M6MTY6InpabXZDVGc0bDJrcmtsM2giO33vItVfTQAAAA&localPriority=0"
    },
    {
        "category": "Общий поток: Подработка",
        "target": "lead",
        "strict_filter": True, 
        "url": "https://www.avito.ru/moskva/vakansii?cd=1&context=H4sIAAAAAAAA_wFNALL_YToyOntzOjg6ImZyb21QYWdlIjtzOjE2OiJzZWFyY2hGb3JtV2lkZ2V0IjtzOjE6InkiO3M6MTY6Ikg5SWhmRmRqZWJoNllwQzYiO32NsZrgTQAAAA&localPriority=0&q=%D0%BF%D0%BE%D0%B4%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%BA%D0%B0"
    }
]

# БЕЛЫЙ СПИСОК: Жесткие мебельные маркеры
ALLOWED_KEYWORDS = [
    "мебель", "кухн", "кухон", "шкаф", "монтаж", "монтажник", 
    "установк", "диван", "кроват", "корпусн", "тумб", "гардероб", "сборка", "сборщик"
]

# ЧЕРНЫЙ СПИСОК: Сюда зашиты все комбинации левых сборщиков
BANNED_KEYWORDS = [
    "заказ", "день\\вечер", "день/вечер", "без опыта", "16+", "18+",
    "обед", "повар", "курьер", "даркстор", "достав", "водитель", 
    "грузчик", "комплектовщик", "упаковщик", "склад", "клининг", 
    "фасовщик", "яндекс", "самокат", "озон", "дрон", "бпла", 
    "беспилотник", "тыл", "сво", "косметика", "канцтовар", 
    "бижутерия", "аппарат", "германия", "продукции", "бус"
]

# 2. Логика проверки объявления (вставь в свой цикл парсинга)
def is_valid_lead(title):
    title_lower = title.lower()
    # Проверяем, есть ли хотя бы одно слово из черного списка
    for word in BANNED_KEYWORDS:
        if word in title_lower:
            return False # Если нашли мусор — отбрасываем
    return True # Если всё чисто — оставляем

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
            print(f"[CRM] [+] Заказ прошел фильтрацию и добавлен: {lead_data['title'][:40]}")
    except Exception as e:
        print(f"[CRM] Ошибка отправки: {e}")

def parse_category(page, task):
    print(f"\n[*] Прочесываем направление: {task['category']}...")
    page.goto(task['url'])
    time.sleep(random.uniform(4.0, 6.0)) 
    
    items = page.query_selector_all('[data-marker="catalog-serp"] div[data-marker="item"]') or page.query_selector_all('div[data-marker="item"]')
    print(f"[*] Всего карточек на странице Авито: {len(items)}")
    
    for item in items:
        link_el = item.query_selector('a[data-marker="item-title"]') or item.query_selector('a')
        if not link_el:
            continue
            
        title = link_el.inner_text().strip().replace('\n', ' ')
        title_low = title.lower()
        
        # УМНАЯ СИСТЕМА ФИЛЬТРАЦИИ ШУМА
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
                "description": "Срочный заказ / Подработка",
                "metro": metro,
                "district": "Уточняется",
                "link": link,
                "tags": extract_tags(title)
            }
            send_to_crm(lead_data, task["target"])

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"]) 
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        for task in TASKS:
            try: parse_category(page, task)
            except Exception as e: print(f"[-] Ошибка: {e}")
        browser.close()

if __name__ == "__main__":
    run()