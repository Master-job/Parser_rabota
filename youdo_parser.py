import os
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth # <--- ИСПРАВЛЕН ИМПОРТ
import time
import random

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5625eb3b'

TASKS = [
    {
        "category": "Юду: Живая лента",
        "target": "lead",
        "strict_filter": True,
        "url": "https://youdo.com/tasks"
    }
]

ALLOWED_KEYWORDS = [
    "мебель", "кухн", "кухон", "шкаф", "диван", "кроват", "корпусн", "тумб", "гардероб", 
    "сборка", "сборщик", "комод", "стеллаж", "стол", "стул", "прихож", "двер", "петл", 
    "ручк", "ящик", "регулировк", "ремонт мебели", "навес", "зеркал", "карниз", "на час", 
    "плинтус", "повесить", "закрепить", "кронштейн", "полк", "картин", "телевизор", "тв", 
    "жалюзи", "ролл", "розетк", "люстр", "свет", "выключател", "проводк", "смесител", 
    "сифон", "раковин", "унитаз", "засор", "подключить стирал", "посудомойк", "душ"
]

BANNED_KEYWORDS = [
    "без опыта", "курьер", "достав", "водитель", "грузчик", 
    "склад", "клининг", "яндекс", "самокат", "озон", "косметика", "уборка"
]

def extract_tags(text):
    text_low = text.lower()
    tags = []
    if any(x in text_low for x in ["кухн", "кухон"]): tags.append("Кухни")
    if any(x in text_low for x in ["шкаф", "купе"]): tags.append("Шкафы")
    if any(x in text_low for x in ["розетк", "люстр", "выключател"]): tags.append("Электрика")
    if any(x in text_low for x in ["смесител", "раковин", "сифон"]): tags.append("Сантехника")
    if any(x in text_low for x in ["петл", "регулировк", "ремонт"]): tags.append("Ремонт мебели")
    return ",".join(tags) if tags else "Муж на час"

def send_to_crm(lead_data, target):
    try:
        endpoint = "/api/add_lead" if target == "lead" else "/api/add_master"
        response = requests.post(f"http://127.0.0.1:8000{endpoint}", json=lead_data, timeout=10)
        if response.status_code == 200:
            print(f"   [CRM] [+] Заказ отправлен: {lead_data['title'][:40]}...")
    except Exception as e:
        print(f"   [-] Ошибка отправки в CRM: {e}")

def human_scroll(page):
    print("[*] Подгружаем новые заказы (имитация человека)...")
    for _ in range(random.randint(3, 5)):
        try:
            page.mouse.wheel(0, random.randint(400, 900))
            page.wait_for_timeout(random.randint(800, 2500))
        except:
            break

def parse_youdo_category(page, task):
    print(f"\n[*] Подключаемся к Юду: {task['category']}...")
    page.goto(task['url'], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(random.randint(3000, 5000))
    page.mouse.move(random.randint(100, 500), random.randint(100, 500))
    
    human_scroll(page)
            
    try:
        page.wait_for_timeout(2000)
        all_elements = page.query_selector_all('a')
    except Exception as e:
        print(f"[-] Не удалось найти элементы на странице: {e}")
        return
    
    print(f"[DEBUG] Всего ссылок найдено: {len(all_elements)}")
    
    seen_hrefs = set()
    valid_links = []
    
    for el in all_elements:
        try:
            href = el.get_attribute('href')
            if href and '/t' in href.lower():
                parts = href.lower().split('/t')
                if len(parts) > 1 and parts[1] and parts[1][0].isdigit():
                    title = el.inner_text().strip()
                    if not title:
                        title = page.evaluate("(element) => element.parentElement ? element.parentElement.innerText : ''", el).strip()
                    title = title.split('\n')[0] if '\n' in title else title
                    
                    if title and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        valid_links.append((el, href, title))
        except:
            continue

    print(f"[*] Реальных заказов: {len(valid_links)}")
    print("-" * 50)

    for link_el, href, title in valid_links:
        try:
            title_low = title.lower()
            if task["strict_filter"]:
                if any(b_kw in title_low for b_kw in BANNED_KEYWORDS) or not any(a_kw in title_low for a_kw in ALLOWED_KEYWORDS):
                    continue
            
            print(f"     [+] Нашли подходящий: {title}")
            link = "https://youdo.com" + href if href.startswith('/') else href
            pure_id = href.split('?')[0].split('/')[-1].replace('t', '')
            
            lead_data = {
                "source_id": f"youdo_{pure_id}", 
                "category": "Муж на час / Сборка",
                "title": title.replace('\n', ' '),
                "description": f"Заказ с ленты Юду: {title}", 
                "metro": "Уточняется",
                "district": "Уточняется",
                "link": link,
                "tags": extract_tags(title)
            }
            
            send_to_crm(lead_data, task["target"])
            time.sleep(random.uniform(0.1, 0.4))
            
        except Exception as e:
            print(f"[-] Ошибка при обработке: {e}")

def run():
    # Замени данные на свои или закомментируй строку 'proxy=proxy_config' ниже, если парсишь без них
    PROXY_SERVER = "http://209.127.51.168:8000"
    PROXY_USER = "хххххх"
    PROXY_PASS = "ххххх"          

    with sync_playwright() as p:
        print("[*] Запускаем stealth-браузер...")
        
        proxy_config = {"server": PROXY_SERVER, "username": PROXY_USER, "password": PROXY_PASS} if PROXY_USER else None

        browser = p.chromium.launch(
            headless=False,
            # proxy=proxy_config, # РАСКОММЕНТИРУЙ, ЕСЛИ ЕСТЬ ПРОКСИ
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080"
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        stealth(page) # <--- ИСПРАВЛЕННЫЙ ВЫЗОВ АНТИБОТА
        
        for task in TASKS:
            parse_youdo_category(page, task)
                
        print("\n[+] Парсинг завершен! Закрываемся через 10 сек...")
        time.sleep(10)
        browser.close()

if __name__ == "__main__":
    run()