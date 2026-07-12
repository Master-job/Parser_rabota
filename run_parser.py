import subprocess
import sys


def run(script):
    print("\n" + "=" * 60)
    print("▶ Запуск:", script)
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:
        print("❌ Ошибка:", script)
        exit(1)

    print("✅ Готово:", script)


def main():

    # 1. Парсим Авито (теперь строго на ПК, собирает новые цены!)
    run("parsers/avito_parser.py")

    # 2. Фильтруем вакансии
    run("services/filter_jobs.py")

    # 3. Оцениваем
    run("services/scorer.py")

    # 4. Создаем красивые посты
    run("services/create_posts.py")

    # 5. Публикуем в Telegram
    run("services/telegram_publisher.py")

    print("\n🎉 Полный цикл завершён.")


if __name__ == "__main__":
    main()