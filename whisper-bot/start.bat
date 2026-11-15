@echo off
chcp 65001 > nul
echo [INFO] Запуск бота Шёпот...
if not exist .env (
    echo [ERROR] Файл .env не найден! Скопируйте .env.example в .env и укажите BOT_TOKEN.
    pause
    exit /b 1
)
python bot.py
pause
