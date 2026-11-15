"""
Шёпот Bot — Inline-клавиатуры
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import PRICE_UNMASK, PRICE_PREMIUM_WEEK, PRICE_PREMIUM_MONTH


# ──────────────────────── Главное меню ────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔗 Моя ссылка", callback_data="my_link"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="⭐ Premium", callback_data="premium_menu"),
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referral_menu"),
        ],
        [
            InlineKeyboardButton(text="❓ Как это работает?", callback_data="how_it_works"),
        ],
    ])


# ──────────────────────── Профиль ────────────────────────

def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить приветствие", callback_data="edit_greeting"),
        ],
        [
            InlineKeyboardButton(text="🔗 Моя ссылка", callback_data="my_link"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
    ])


# ──────────────────────── Сообщение: действия ────────────────────────

def message_actions_kb(message_id: int, show_unmask: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if show_unmask:
        buttons.append([
            InlineKeyboardButton(
                text=f"🔓 Раскрыть отправителя ({PRICE_UNMASK} ⭐)",
                callback_data=f"unmask:{message_id}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="💬 Ответить анонимно", callback_data=f"reply:{message_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def message_unmasked_kb(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить анонимно", callback_data=f"reply:{message_id}")],
    ])


# ──────────────────────── Отправка: после отправки ────────────────────────

def after_send_kb(receiver_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Отправить ещё", callback_data=f"send_more:{receiver_code}")],
        [InlineKeyboardButton(text="🔗 Получить свою ссылку", callback_data="my_link")],
    ])


# ──────────────────────── Premium ────────────────────────

def premium_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"⭐ Неделя — {PRICE_PREMIUM_WEEK} Stars",
                callback_data="buy_premium:week",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"⭐ Месяц — {PRICE_PREMIUM_MONTH} Stars",
                callback_data="buy_premium:month",
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
    ])


# ──────────────────────── Рефералы ────────────────────────

def referral_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", switch_inline_query="")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
    ])


# ──────────────────────── Подтверждения ────────────────────────

def confirm_unmask_kb(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, раскрыть", callback_data=f"confirm_unmask:{message_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
        ],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
    ])


# ──────────────────────── Поделиться ссылкой ────────────────────────

def share_link_kb(link: str) -> InlineKeyboardMarkup:
    text = f"🤫 Отправь мне анонимное сообщение!\n{link}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Поделиться",
                switch_inline_query=text,
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Меню", callback_data="back_main"),
        ],
    ])
