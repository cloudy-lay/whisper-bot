"""
Шёпот Bot — Конфигурация
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Основные настройки ──
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "WhisperAnonBot")

# ── Лимиты ──
FREE_MESSAGES_PER_DAY = 15          # Бесплатных сообщений в день
PREMIUM_MESSAGES_PER_DAY = 200      # Premium сообщений в день
MESSAGE_COOLDOWN_SECONDS = 20       # Кулдаун между сообщениями одной паре
MAX_MESSAGE_LENGTH = 2000           # Макс. длина сообщения

# ── Цены (Telegram Stars ⭐) ──
PRICE_UNMASK = 49                   # Раскрыть отправителя 1 сообщения
PRICE_PREMIUM_WEEK = 149            # Premium на 7 дней
PRICE_PREMIUM_MONTH = 449           # Premium на 30 дней

# ── Реферальные награды ──
REF_UNMASK_THRESHOLD = 3            # 3 реферала = 1 бесплатное раскрытие
REF_WEEK_THRESHOLD = 10             # 10 рефералов = неделя Premium
REF_MONTH_THRESHOLD = 25            # 25 рефералов = месяц Premium

# ── База данных ──
DB_PATH = "whisper.db"

# ── Стоп-слова (базовый фильтр) ──
BANNED_WORDS: list[str] = []        # Добавьте сюда слова для фильтрации
