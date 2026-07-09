from playwright.sync_api import sync_playwright
import time
import random
import json


TASKS = [
    {
        "profession": "Сборщик мебели",
        "url": "https://www.avito.ru/moskva/vakansii?q=сборщик+мебели"
    },
    {
        "profession": "Монтажник мебели",
        "url": "https://www.avito.ru/moskva/vakansii?q=монтажник+мебели"
    }
]


def save_result(data):
    with open(
        "vacancies_test.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


def parse(page, task):

    print("\n====================")
    print("Ищем:", task["profession"])
    print("====================")


    try:

        page.goto(
            task["url"],
            wait_until="domcontentloaded",
            timeout=60000
        )


    except Exception as e:

        print("Ошибка загрузки:")
        print(e)
        return []


    time.sleep(
        random.uniform(7,10)
    )


    print(
        "Текущий URL:",
        page.url
    )

    print(
        "Заголовок:",
        page.title()
    )


    items = page.query_selector_all(
        '[data-marker="item"]'
    )


    print(
        "Карточек найдено:",
        len(items)
    )


    result = []


    for item in items[:20]:

        try:

            title_el = item.query_selector(
                '[data-marker="item-title"]'
            )


            if not title_el:
                continue


            title = title_el.inner_text()


            href = title_el.get_attribute(
                "href"
            )


            text = item.inner_text()


            result.append(
                {
                    "profession":
                    task["profession"],

                    "title":
                    title,

                    "text":
                    text[:500],

                    "link":
                    "https://www.avito.ru" + href
                    if href else ""
                }
            )


            print(
                "✓",
                title
            )


        except Exception as e:

            print(
                "Ошибка карточки:",
                e
            )


    return result



def run():

    all_vacancies = []


    with sync_playwright() as p:


        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )


        context = browser.new_context(

            user_agent=
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/122.0.0.0 Safari/537.36"

        )


        page = context.new_page()


        for task in TASKS:

            data = parse(
                page,
                task
            )

            all_vacancies.extend(
                data
            )


        browser.close()


    save_result(
        all_vacancies
    )


    print("\nГотово!")
    print(
        "Сохранено вакансий:",
        len(all_vacancies)
    )



if __name__ == "__main__":
    run()