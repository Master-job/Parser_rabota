import cloudscraper
import random
import time
from bs4 import BeautifulSoup
from database import save_post, post_exists

# Вставь сюда свои данные: http://логин:пароль@ip:порт
PROXY = "http://fN5wao:FECguD@209.127.51.168:8000"

def parse_avito(query_url):
    print(f"[*] --- НАЧАЛО ДИАГНОСТИКИ АВИТО ---")
    
    # Настройка прокси
    proxies = {
        "http": PROXY,
        "https": PROXY
    }
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome', 
            'platform': 'windows', 
            'desktop': True
        }
    )
    
    try:
        time.sleep(random.uniform(5, 10))
        # Запрос с использованием прокси
        response = scraper.get(query_url, proxies=proxies, timeout=20)
        
        print(f"[*] Статус: {response.status_code}")
        print(f"[*] Размер HTML: {len(response.text)} символов")
        
        if "captcha" in response.text.lower() or "защита от ботов" in response.text:
            print("[!] ОБНАРУЖЕНА КАПЧА ИЛИ ЗАЩИТА!")
            return

        if response.status_code != 200:
            print(f"[!] Авито ответил ошибкой: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select('div[data-marker="item"]')
        
        print(f"[*] Найдено карточек: {len(items)}")
        
        if len(items) == 0:
            print(f"[*] Текст начала страницы: {response.text[:200]}")
            print("[!] Внимание: Селектор div[data-marker='item'] не сработал!")

        for item in items:
            title_tag = item.select_one('h3[itemprop="name"]')
            link_tag = item.select_one('a[itemprop="url"]')
            
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = "https://www.avito.ru" + link_tag["href"]
                post_id = link.split("_")[-1]
                
                if not post_exists(post_id):
                    save_post(post_id, "ORDER", "avito", title, link)
                    print(f"[+] УСПЕХ! Лид найден: {title}")
                    
    except Exception as e:
        print(f"[!] Критическая ошибка парсера: {e}")