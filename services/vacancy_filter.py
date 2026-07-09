import json
import os


INPUT_FILE = "vacancies_test.json"
OUTPUT_FILE = "vacancies_clean.json"


# Что нам интересно
GOOD_WORDS = [
    "мебел",
    "кухн",
    "шкаф",
    "корпусн",
    "обив",
    "столеш",
    "фасад",
]


BAD_WORDS = [
    "дрон",
    "бпла",
    "летатель",
    "сво",
    "склад",
    "заказов",
    "комплектовщик",
    "курьер",
    "достав",
    "водитель",
    "такси",
    "натяжн",
    "потолок",
    "корея",
    "солнеч",
    "вагончик",
    "детск",
]


def check_vacancy(vacancy):

    text = (
        vacancy.get("title", "")
        + " "
        + vacancy.get("text", "")
    ).lower()


    # сначала режем мусор
    for bad in BAD_WORDS:

        if bad in text:
            return False


    # потом ищем соответствие профессии
    for good in GOOD_WORDS:

        if good in text:
            return True


    return False



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



    clean = []


    for vacancy in vacancies:

        if check_vacancy(vacancy):

            clean.append(vacancy)



    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            clean,
            f,
            ensure_ascii=False,
            indent=4
        )


    print("====================")
    print("Всего:", len(vacancies))
    print("После фильтра:", len(clean))
    print("====================")


    for item in clean:

        print(
            "✅",
            item["title"]
        )



if __name__ == "__main__":

    run()