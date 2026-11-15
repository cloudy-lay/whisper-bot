"""
Шёпот Bot — Профиль и настройки
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from keyboards import profile_kb, share_link_kb, main_menu_kb, cancel_kb
from utils import get_anon_link, escape_html, format_number

router = Router()


class GreetingState(StatesGroup):
    waiting_greeting = State()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Сначала нажми /start", show_alert=True)
        return

    is_prem = await db.is_premium(user_id)
    premium_badge = "⭐ Premium" if is_prem else "Бесплатный"
    premium_until = ""
    if is_prem and user["premium_until"]:
        premium_until = f"\n📅 Premium до: <code>{user['premium_until'][:10]}</code>"

    ref_count = await db.referral_count(user_id)
    link = get_anon_link(user["unique_code"])

    greeting_text = user["greeting"] or "<i>не установлено</i>"

    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"📛 Имя: <b>{escape_html(user['first_name'] or '—')}</b>\n"
        f"🏷 Статус: <b>{premium_badge}</b>{premium_until}\n"
        f"📩 Получено сообщений: <b>{format_number(user['messages_received'])}</b>\n"
        f"📤 Отправлено: <b>{format_number(user['messages_sent'])}</b>\n"
        f"👥 Рефералов: <b>{ref_count}</b>\n"
        f"🔓 Бесплатных раскрытий: <b>{user['free_unmasks']}</b>\n\n"
        f"✉️ Приветствие: {greeting_text}\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=profile_kb())
    await callback.answer()


@router.callback_query(F.data == "my_link")
async def show_my_link(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Нажми /start", show_alert=True)
        return

    link = get_anon_link(user["unique_code"])

    text = (
        f"🔗 <b>Твоя анонимная ссылка:</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"📱 Размести её в:\n"
        f"• Instagram Stories / Bio\n"
        f"• TikTok профиле\n"
        f"• Twitter / ВКонтакте\n"
        f"• Telegram каналах и чатах\n\n"
        f"🤫 Каждый, кто перейдёт — сможет написать тебе <b>анонимно!</b>"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=share_link_kb(link)
    )
    await callback.answer()


@router.callback_query(F.data == "edit_greeting")
async def start_edit_greeting(callback: CallbackQuery, state: FSMContext, db: Database):
    is_prem = await db.is_premium(callback.from_user.id)
    if not is_prem:
        await callback.answer(
            "⭐ Персональное приветствие доступно для Premium!",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "✏️ Напиши текст приветствия, который увидят люди, "
        "перед отправкой тебе анонимного сообщения.\n\n"
        "Максимум 200 символов.",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await state.set_state(GreetingState.waiting_greeting)
    await callback.answer()


@router.message(GreetingState.waiting_greeting, F.text)
async def save_greeting(message: Message, db: Database, state: FSMContext):
    text = message.text.strip()[:200]
    await db.set_greeting(message.from_user.id, text)
    await state.clear()
    await message.answer(
        f"✅ Приветствие обновлено:\n\n<i>«{escape_html(text)}»</i>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
