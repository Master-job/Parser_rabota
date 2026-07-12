import json
import os

# ЧИТАЕМ ТО, ЧТО РЕАЛЬНО СОЗДАЛ SCORER.PY
INPUT_FILE = "vacancies_ready.json"
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
    # Так как в твоей структуре поле называется 'text' или 'salary', подстрахуемся:
    salary = vacancy.get("salary_text") or vacancy.get("salary") or "По договоренности"
    score = vacancy.get("score", 0)
    category = detect_category(title)
    link = vacancy.get("link", "").strip()
    metro = vacancy.get("metro", "Москва").strip()

    # Срезаем хвосты Авито прямо на корню
    if link and "?" in link:
        link = link.split("?")[0]

    if "25 000" in str(salary) or "30 000" in str(salary):
        header = f"💰 🔥 ЖИРНЫЙ ЗАКАЗ: {title.upper()}"
    else:
        header = f"⚡ НОВЫЙ ЗАКАЗ: {title.upper()}"

    post = f"""<b>{header}</b>

🔥 <i>Отличный прямой заказ для мастера со своим инструментом! Без посредников.</i>

📍 <b>Локация:</b> {metro}
🛠 <b>Направление:</b> {category}
💵 <b>Бюджет / Оплата:</b> <u>{salary}</u>

⭐ <b>Надежность заказа:</b> {score}/100 (Высокий приоритет)

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
            "link": vacancy.get("link"),
            "post": post
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("====================")
    print("Успешно сформировано постов:", len(result))
    print("====================")

if __name__ == "__main__":
    run()