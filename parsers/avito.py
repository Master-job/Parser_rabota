import requests
import random
import time
from bs4 import BeautifulSoup
from database import save_post, post_exists

# Авито требует, чтобы запрос выглядел как от реального браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.avito.ru/"
}

def parse_avito(query_url):
    """
    query_url: полная ссылка на результаты поиска на Авито
    """
    print(f"[*] Запуск парсинга Авито: {query_url}")
    
    try:
        # Добавляем рандомную задержку, чтобы Авито не понял, что мы бот
        time.sleep(random.uniform(2, 5))
        
        response = requests.get(query_url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[!] Авито ответил кодом {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        
        # На Авито карточки объявлений лежат в определенных классах
        # ВАЖНО: Классы Авито часто меняет, если перестанет парсить — нужно обновлять селектор
        items = soup.find_all("div", {"data-marker": "item"})
        
        for item in items:
            title_tag = item.find("h3", {"itemprop": "name"})
            link_tag = item.find("a", {"itemprop": "url"})
            
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = "https://www.avito.ru" + link_tag["href"]
                post_id = link.split("_")[-1] # Уникальный ID объявления из ссылки
                
                if not post_exists(post_id):
                    # Сохраняем как ORDER (заказ)
                    save_post(post_id, "ORDER", "avito", title, link)
                    print(f"[+] Найден заказ на Авито: {title}")
                    
    except Exception as e:
        print(f"[!] Ошибка при парсинге Авито: {e}")