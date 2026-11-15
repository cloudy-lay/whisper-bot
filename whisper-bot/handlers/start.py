"""
Шёпот Bot — Обработчик /start и регистрация
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import main_menu_kb, share_link_kb, cancel_kb
from utils import generate_unique_code, get_anon_link, get_referral_link, escape_html
from config import REF_UNMASK_THRESHOLD, REF_WEEK_THRESHOLD, REF_MONTH_THRESHOLD

router = Router()


class SendingState(StatesGroup):
    """FSM состояния для отправки анонимного сообщения."""
    waiting_message = State()       # Ожидание текста сообщения
    target_user_id = State()        # ID получателя (хранится в state data)


WELCOME_TEXT = """
🤫 <b>Добро пожаловать в Шёпот!</b>

Анонимные сообщения, которые ты давно хотел получить.

<b>Как это работает:</b>
1️⃣ Получи свою <b>уникальную ссылку</b>
2️⃣ Поделись ей в соцсетях, сторис, в био
3️⃣ Получай <b>анонимные сообщения</b> от друзей и подписчиков
4️⃣ Отвечай анонимно — чат остаётся тайным 🔮

Нажми <b>«🔗 Моя ссылка»</b> и начни прямо сейчас!
"""

ANON_GREETING_DEFAULT = """
🤫 <b>Отправь анонимное сообщение для {name}!</b>

Напиши что-нибудь — отправитель останется <b>в тайне</b>.
Просто введи текст ниже 👇
"""


@router.message(CommandStart(deep_link=True))
async def start_with_link(message: Message, command: CommandObject, db: Database, state: FSMContext):
    """Обработка /start с deep link (анонимная ссылка или реферал)."""
    args = command.args
    user_id = message.from_user.id

    # ── Реферальная ссылка: ref_USERID ──
    if args.startswith("ref_"):
        referrer_id_str = args[4:]
        try:
            referrer_id = int(referrer_id_str)
        except ValueError:
            await _register_and_welcome(message, db)
            return

        if referrer_id == user_id:
            await _register_and_welcome(message, db)
            return

        # Регистрируем нового пользователя
        existing = await db.get_user(user_id)
        if not existing:
            code = generate_unique_code(user_id)
            await db.create_user(user_id, message.from_user.username, message.from_user.first_name, code, referrer_id)
            await db.create_referral(referrer_id, user_id)

            # Проверяем награды для реферера
            await _check_referral_rewards(db, referrer_id, message)

            await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())
        else:
            await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())
        return

    # ── Анонимная ссылка: unique_code ──
    target_user = await db.get_user_by_code(args)
    if not target_user:
        # Невалидный код — просто регистрируем
        await _register_and_welcome(message, db)
        return

    target_id = target_user["user_id"]

    # Нельзя писать самому себе
    if target_id == user_id:
        await message.answer(
            "😅 Ты не можешь отправить анонимное сообщение самому себе!\n\n"
            "Поделись своей ссылкой с друзьями 👇",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        return

    # Регистрируем отправителя если новый
    existing = await db.get_user(user_id)
    if not existing:
        code = generate_unique_code(user_id)
        await db.create_user(user_id, message.from_user.username, message.from_user.first_name, code)

    # Проверяем бан
    if target_user["is_banned"]:
        await message.answer("❌ Этот пользователь недоступен.")
        return

    # Показываем приветствие и ждём сообщение
    name = escape_html(target_user["first_name"] or "Аноним")
    greeting = target_user["greeting"]
    if greeting:
        text = f"🤫 <b>{escape_html(greeting)}</b>\n\nНапиши анонимное сообщение для <b>{name}</b> 👇"
    else:
        text = ANON_GREETING_DEFAULT.format(name=name)

    await message.answer(text, parse_mode="HTML", reply_markup=cancel_kb())

    # Устанавливаем FSM
    await state.set_state(SendingState.waiting_message)
    await state.update_data(target_user_id=target_id, target_code=args)


@router.message(CommandStart())
async def start_clean(message: Message, db: Database, state: FSMContext):
    """Обработка чистого /start без параметров."""
    await state.clear()
    await _register_and_welcome(message, db)


async def _register_and_welcome(message: Message, db: Database):
    """Регистрирует пользователя и показывает приветствие."""
    user_id = message.from_user.id
    existing = await db.get_user(user_id)
    if not existing:
        code = generate_unique_code(user_id)
        await db.create_user(user_id, message.from_user.username, message.from_user.first_name, code)
    await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=main_menu_kb())


async def _check_referral_rewards(db: Database, referrer_id: int, message: Message):
    """Проверяет и начисляет реферальные награды."""
    count = await db.referral_count(referrer_id)

    notifications = []

    if count == REF_UNMASK_THRESHOLD:
        await db.add_free_unmasks(referrer_id, 1)
        notifications.append(
            f"🎉 У тебя <b>{count}</b> рефералов! Получи <b>1 бесплатное раскрытие</b> отправителя!"
        )
    elif count == REF_WEEK_THRESHOLD:
        await db.set_premium(referrer_id, 7)
        notifications.append(
            f"🎉 У тебя <b>{count}</b> рефералов! Ты получил <b>Premium на неделю</b>! 🌟"
        )
    elif count == REF_MONTH_THRESHOLD:
        await db.set_premium(referrer_id, 30)
        notifications.append(
            f"🎉 У тебя <b>{count}</b> рефералов! Ты получил <b>Premium на месяц</b>! 🌟"
        )

    # Уведомляем реферера
    for text in notifications:
        try:
            await message.bot.send_message(referrer_id, text, parse_mode="HTML")
        except Exception:
            pass  # Пользователь мог заблокировать бота


# ──────────────────────── Навигация ────────────────────────

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🤫 <b>Шёпот</b> — Главное меню",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено.",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "how_it_works")
async def how_it_works(callback: CallbackQuery):
    text = """
❓ <b>Как работает Шёпот?</b>

1️⃣ <b>Получи ссылку</b> — нажми «🔗 Моя ссылка»
2️⃣ <b>Поделись</b> — в Instagram Stories, TikTok, Twitter, ВК
3️⃣ <b>Получай сообщения</b> — анонимно, прямо в этот бот
4️⃣ <b>Отвечай</b> — автор получит ответ, но не узнает кто ты

💎 <b>Premium возможности:</b>
• 🔓 Раскрой отправителя любого сообщения
• 🔤 Подсказки: первая буква имени, длина
• 📨 Больше сообщений в день
• ✏️ Персональное приветствие

👥 <b>Приглашай друзей</b> — получай Premium бесплатно!
"""
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=main_menu_kb()
    )
    await callback.answer()
