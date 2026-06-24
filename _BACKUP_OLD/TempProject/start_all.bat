@echo off
chcp 65001 > nul
echo [*] Запуск Enterprise CRM Сервера...
start cmd /k "title CRM Server && python server.py"

echo [*] Ждем 4 секунды, пока сервер проснется...
timeout /t 4

echo [*] Запуск Интеллектуального Парсера Авито...
start cmd /k "title Avito Parser && python local_avito_parser.py"

echo [+] Все компоненты запущенны успешно!