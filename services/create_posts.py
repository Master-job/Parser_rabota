import json
import os

INPUT_FILE = "vacancies_salary.json"
OUTPUT_FILE = "telegram_preview.json"

def detect_category(title):
    text = title.lower()
    if "кух" in text: return "📐 Кухни (Монтаж и сборка)"
    if "корпус" in text: return "📦 Корпусная мебель"
    if "шкаф" in text: return "🚪 Шкафы-купе / Гардеробы"
    if "замер" in text: return "📏 Замеры мебели"
    return "🛠 Сборка мебели"

def format_post(vacancy):
    title = vacancy.get("title", "Разовый заказ").strip()
    salary = vacancy.get("salary_text", "По договоренности").strip()
    score = vacancy.get("score", 0)
    category = detect_category(title)
    link = vacancy.get("link", "")
    metro = vacancy.get("metro", "Москва").strip()
    # --- ДОБАВЬ ВОТ ЭТУ СТРОЧКУ ДЛЯ ОЧИСТКИ ССЫЛКИ ---
    if link and "?" in link:
        link = link.split("?")[0]

    # Форматируем красивый заголовок в зависимости от цены
    if "25 000" in salary or "30 000" in salary:
        header = f"💰 🔥 ЖИРНЫЙ ЗАКАЗ: {title.upper()}"
    else:
        header = f"⚡ НОВЫЙ ЗАКАЗ: {title.upper()}"

    # Собираем сочный пост с HTML-тегами
    post = f"""<b>{header}</b>

🔥 <i>Отличный прямой заказ для мастера со своим инструментом! Без посредников и b2b-спама.</i>

📍 <b>Локация:</b> {metro}
🛠 <b>Направление:</b> {category}
💵 <b>Бюджет / Оплата:</b> <u>{salary}</u>

⭐ <b>Надежность заказа:</b> {score}/100 (Высокий приоритет)

⚠️ <b>Условия:</b> Прямой контакт с частным клиентом. Выплаты, как правило, сразу по факту выполнения работы.

🟢 <b>Успей перехватить объект в работу:</b>
👉 <a href="{link}">НАЖМИ ТУТ, ЧТОБЫ ОТКРЫТЬ ВАКАНСИЮ</a>

#работаМосква #сборщикмебели #кухни #подработка"""

    return post.strip()

def run():
    if not os.path.exists(INPUT_FILE):
        print("Нет файла:", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        vacancies = json.load(f)

    result = []
    for vacancy in vacancies:
        post = format_post(vacancy)
        result.append({
            "title": vacancy.get("title"),
            "score": vacancy.get("score"),
            "link": vacancy.get("link"), # Оставляем линк для проверки в паблишере
            "post": post
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("====================")
    print("Готово постов:", len(result))
    print("====================")

    for item in result[:2]:
        print("\n" + item["post"] + "\n--------------------")

if __name__ == "__main__":
    run()