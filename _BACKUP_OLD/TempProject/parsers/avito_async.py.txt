# parsers/avito_async.py
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict

async def parse_avito_async() -> List[Dict]:
    """Асинхронный неблокирующий скрапер Avito для сборки мебели"""
    url = "https://www.avito.ru/moskva/predlozheniya_uslug/remont_i_otdelka/sborka_i_remont_mebeli"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    print(f"❌ Ошибка получения данных с Avito: HTTP {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find_all('div', {'data-marker': 'item'})
                leads = []
                
                for item in items[:15]:
                    try:
                        title_elem = item.find('a', {'data-marker': 'item-title'})
                        if not title_elem: continue
                        
                        title = title_elem.get_text(strip=True)
                        link = "https://www.avito.ru" + title_elem.get('href', '')
                        
                        geo_elem = item.find('div', {'data-marker': 'item-address'})
                        metro = geo_elem.get_text(strip=True) if geo_elem else "Не указано"
                        
                        leads.append({
                            'title': title,
                            'description': f"Объявление найдено на Avito. Ссылка: {link}",
                            'category': 'Сборка мебели',
                            'subcategory': 'Внешний лид',
                            'metro': metro,
                            'district': 'Москва',
                            'source': 'avito',
                            'link': link
                        })
                    except Exception as e:
                        print(f"Ошибка парсинга элемента Avito: {e}")
                return leads
        except Exception as e:
            print(f"❌ Ошибка сессии Avito: {e}")
            return []