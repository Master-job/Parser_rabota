import json
import os
import re


INPUT_FILE = "vacancies_ready.json"
OUTPUT_FILE = "vacancies_salary.json"



def extract_salary(text):

    result = {
        "salary_min": None,
        "salary_max": None,
        "salary_text": None,
        "salary_period": None
    }


    if not text:
        return result


    clean = (
        text
        .replace("\xa0", " ")
        .replace(" ", " ")
    )


    # ищем диапазон:
    # 5000 - 8000 ₽
    # 5 000–8 000 ₽

    range_match = re.search(
        r"(\d[\d\s]{2,8})\s*[-–]\s*(\d[\d\s]{2,8})\s*(?:₽|руб)",
        clean,
        re.IGNORECASE
    )


    if range_match:

        result["salary_min"] = int(
            range_match.group(1)
            .replace(" ", "")
        )

        result["salary_max"] = int(
            range_match.group(2)
            .replace(" ", "")
        )

        result["salary_text"] = range_match.group(0)



    else:

        # ищем одно число:
        # 8000 ₽
        # 8 000 руб
        # от 8000 рублей

        single = re.search(

            r"(?:от\s*)?(\d[\d\s]{2,8})\s*(?:₽|руб|рублей)",

            clean,

            re.IGNORECASE
        )


        if single:

            number = (
                single.group(1)
                .replace(" ", "")
            )


            result["salary_min"] = int(number)

            result["salary_text"] = single.group(0)



    text_low = clean.lower()


    if "смен" in text_low:

        result["salary_period"] = "смена"


    elif "ежеднев" in text_low or "день" in text_low:

        result["salary_period"] = "день"


    elif "месяц" in text_low or "мес" in text_low:

        result["salary_period"] = "месяц"



    return result




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



    print("====================")
    print("Проверяем зарплаты")
    print("====================")



    for vacancy in vacancies:


        full_text = (

            vacancy.get("title", "")
            +
            " "
            +
            vacancy.get("text", "")

        )


        salary = extract_salary(
            full_text
        )


        vacancy.update(
            salary
        )



    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            vacancies,

            f,

            ensure_ascii=False,

            indent=4

        )



    print(
        "Обработано:",
        len(vacancies)
    )


    print("====================")


    for v in vacancies[:10]:

        print(
            "💰",
            v.get("salary_text"),
            "|",
            v["title"]
        )



if __name__ == "__main__":

    run()