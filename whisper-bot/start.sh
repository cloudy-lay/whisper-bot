#!/usr/bin/env bash
set -e

if [ ! -f .env ]; then
    echo "[ERROR] Файл .env не найден! Скопируйте .env.example в .env и укажите BOT_TOKEN."
    exit 1
fi

python3 bot.py
