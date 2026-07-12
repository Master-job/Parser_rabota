import subprocess
import sys


def run(script, ignore_errors=False):
    print("\n" + "=" * 60)
    print(f"▶ Запуск: {script}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:
        print(f"❌ Ошибка в скрипте: {script}")
        if not ignore_errors:
            exit(1)
        else:
            print(f"⚠️ Ошибка проигнорирована, конвейер продолжается...")
    else:
        print(f"✅ Готово: {script}")


def main():

    # 1. Парсим Авито (Ставим True, чтобы падение Playwright на Render не ломало всё ядро)
    run("parsers/avito_parser.py", ignore_errors=True)

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