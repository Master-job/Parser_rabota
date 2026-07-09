import asyncio
import random
from urllib.parse import quote_plus
from playwright.async_api import async_playwright
import httpx

KEYWORDS = ["грузчик", "разнорабочий", "ежедневная оплата"]
# URL твоего запущенного FastAPI сервера
API_URL = "http://127.0.0.1:8000/api/add_lead"

async def send_to_backend(payload):
    """Функция отправки лида в твою базу через FastAPI"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"Ошибка отправки на бэкенд: {e}")
        return False

async def parse_hh_live(query):
    encoded_query = quote_plus(query)
    url = f"https://hh.ru/search/vacancy?text={encoded_query}&area=1&order_by=publication_time"
    
    print(f"\n Начинаем сбор по ключу: '{query}'...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU"
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector('[data-qa="vacancy-serp__vacancy"]', timeout=15000)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4)")
            await page.wait_for_timeout(random.randint(1000, 2500))
        except Exception as e:
            print(f"Ошибка загрузки страницы (возможно капча): {e}")
            await browser.close()
            return 0
            
        cards = page.locator('[data-qa="vacancy-serp__vacancy"]')
        count = await cards.count()
        
        saved_count = 0
        for i in range(min(count, 15)):
            card = cards.nth(i)
            try:
                title = await card.locator('[data-qa="serp-item__title"]').inner_text()
                link = await card.locator('[data-qa="serp-item__title"]').get_attribute("href")
                clean_link = link.split('?')[0]
                
                # Вытаскиваем ID вакансии из ссылки (например, из https://hh.ru/vacancy/133320101 получим 133320101)
                source_id = f"hh_{clean_link.split('/')[-1]}"
                
                try:
                    company = await card.locator('[data-qa="vacancy-serp__vacancy-employer"]').inner_text()
                except:
                    company = "Не указана"
                
                # Формируем модель данных под твой ScrapeModel
                payload = {
                    "source_id": source_id,
                    "category": "Линейный персонал", # Твоя категория для ТГ-групп
                    "title": title.strip(),
                    "description": f"Компания: {company.strip()}",
                    "metro": "Не указано", # Для HH можно допилить позже
                    "district": "Москва",
                    "link": clean_link,
                    "tags": f"hh, {query}"
                }
                
                # Отправляем в твою базу данных
                success = await send_to_backend(payload)
                if success:
                    saved_count += 1
                    
            except Exception as item_err:
                continue
                
        await browser.close()
        return saved_count

async def main():
    for kw in KEYWORDS:
        added = await parse_hh_live(kw)
        print(f" Результат: Успешно обработано и отправлено в базу: {added}")
        
        sleep_time = random.randint(3, 6)
        print(f"Спим {sleep_time} сек...")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(main())