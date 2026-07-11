import json
import os
import re


INPUT_FILE = "vacancies_clean.json"
OUTPUT_FILE = "vacancies_ready.json"



def normalize(text):

    text = text.lower()

    text = re.sub(
        r"[^а-яa-z0-9 ]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()



def calculate_score(vacancy):

    text = (
        vacancy.get("title", "")
        + " "
        + vacancy.get("text", "")
    ).lower()


    score = 0


    # профессия
    if "мебел" in text:
        score += 30

    if "кухн" in text:
        score += 25

    if "сборщик" in text:
        score += 20

    if "монтажник" in text:
        score += 15

    if "корпус" in text:
        score += 15

    if "обив" in text:
        score += 15


    # хорошие условия
    if "ежеднев" in text:
        score += 10

    if "выплат" in text:
        score += 10

    if "смен" in text:
        score += 5

    if "постоян" in text:
        score += 10


    return score



def remove_duplicates(vacancies):

    result = []

    seen = set()


    for vacancy in vacancies:

        key = normalize(
            vacancy.get("title", "")
        )


        if key in seen:
            continue


        seen.add(key)

        result.append(vacancy)


    return result



def run():

    if not os.path.exists(INPUT_FILE):

        print(
            "Нет файла",
            INPUT_FILE
        )

        return


    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        vacancies = json.load(f)



    print(
        "До обработки:",
        len(vacancies)
    )


    vacancies = remove_duplicates(
        vacancies
    )


    print(
        "После удаления дублей:",
        len(vacancies)
    )


    for vacancy in vacancies:

        vacancy["score"] = calculate_score(
            vacancy
        )


    vacancies.sort(
        key=lambda x: x["score"],
        reverse=True
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
        "===================="
    )

    print(
        "Готово:",
        len(vacancies)
    )


    for v in vacancies:

        print(
            "⭐",
            v["score"],
            "-",
            v["title"]
        )



if __name__ == "__main__":

    run()