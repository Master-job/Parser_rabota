import json
import os


INPUT_FILE = "vacancies_salary.json"
OUTPUT_FILE = "telegram_preview.json"



def detect_category(title):

    text = title.lower()


    if "кух" in text:
        return "Кухни"

    if "корпус" in text:
        return "Корпусная мебель"

    if "мебел" in text:
        return "Сборка мебели"

    if "замер" in text:
        return "Замеры мебели"


    return "Мебель"



def format_post(vacancy):

    title = vacancy.get(
        "title",
        "Вакансия"
    )


    salary = vacancy.get(
        "salary_text"
    )


    if not salary:

        salary = "Уточняется"



    score = vacancy.get(
        "score",
        0
    )


    category = detect_category(
        title
    )


    link = vacancy.get(
        "link",
        ""
    )



    post = f"""
🔥 {title.upper()}


📍 Москва

🛠 Направление:
{category}


💰 Оплата:
{salary}


⭐ Рейтинг:
{score}/100


🔗 Открыть вакансию:
{link}
"""


    return post.strip()



def run():

    if not os.path.exists(INPUT_FILE):

        print(
            "Нет файла:",
            INPUT_FILE
        )

        return



    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        vacancies = json.load(f)



    result = []


    for vacancy in vacancies:

        post = format_post(
            vacancy
        )

        result.append(
            {
                "title": vacancy.get("title"),
                "score": vacancy.get("score"),
                "post": post
            }
        )



    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=4
        )



    print("====================")
    print(
        "Готово постов:",
        len(result)
    )
    print("====================")



    for item in result[:3]:

        print()
        print(item["post"])
        print("--------------------")



if __name__ == "__main__":

    run()