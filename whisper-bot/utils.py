"""
Шёпот Bot — Утилиты
"""
import hashlib
import random
import string
import time
from config import BOT_USERNAME, BANNED_WORDS


def generate_unique_code(user_id: int) -> str:
    """Генерирует уникальный 8-символьный код для пользователя."""
    seed = f"{user_id}:{time.time()}:{random.random()}"
    hash_hex = hashlib.md5(seed.encode()).hexdigest()
    # Берём 8 символов из хеша, добавляем случайную букву для читаемости
    code = hash_hex[:8]
    return code


def get_anon_link(unique_code: str) -> str:
    """Возвращает ссылку для анонимных сообщений."""
    return f"https://t.me/{BOT_USERNAME}?start={unique_code}"


def get_referral_link(user_id: int) -> str:
    """Возвращает реферальную ссылку."""
    return f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"


def escape_html(text: str) -> str:
    """Экранирует HTML спецсимволы."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def check_banned_words(text: str) -> bool:
    """Проверяет текст на наличие запрещённых слов. True = содержит."""
    if not BANNED_WORDS:
        return False
    lower = text.lower()
    return any(word.lower() in lower for word in BANNED_WORDS)


def format_number(n: int) -> str:
    """Форматирует число с разделителями."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def sender_hint(username: str | None, first_name: str | None) -> str:
    """Генерирует подсказку о отправителе для Premium пользователей."""
    name = first_name or username or "Аноним"
    hints = []
    hints.append(f"📏 Длина имени: {len(name)} символов")
    if name:
        hints.append(f"🔤 Первая буква: {name[0].upper()}")
    return "\n".join(hints)
