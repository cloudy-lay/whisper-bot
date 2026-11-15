"""
Шёпот Bot — Реферальная система
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from keyboards import referral_kb, main_menu_kb
from utils import get_referral_link, format_number
from config import REF_UNMASK_THRESHOLD, REF_WEEK_THRESHOLD, REF_MONTH_THRESHOLD

router = Router()


@router.callback_query(F.data == "referral_menu")
async def show_referral_menu(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Нажми /start", show_alert=True)
        return

    ref_count = await db.referral_count(user_id)
    ref_link = get_referral_link(user_id)

    # Прогресс до наград
    progress_lines = []

    if ref_count < REF_UNMASK_THRESHOLD:
        remaining = REF_UNMASK_THRESHOLD - ref_count
        bar = _progress_bar(ref_count, REF_UNMASK_THRESHOLD)
        progress_lines.append(
            f"🔓 <b>Бесплатное раскрытие:</b> {bar} ({remaining} ост.)"
        )
    else:
        progress_lines.append("🔓 Бесплатное раскрытие — ✅ Получено!")

    if ref_count < REF_WEEK_THRESHOLD:
        remaining = REF_WEEK_THRESHOLD - ref_count
        bar = _progress_bar(ref_count, REF_WEEK_THRESHOLD)
        progress_lines.append(
            f"⭐ <b>Premium неделя:</b> {bar} ({remaining} ост.)"
        )
    else:
        progress_lines.append("⭐ Premium неделя — ✅ Получено!")

    if ref_count < REF_MONTH_THRESHOLD:
        remaining = REF_MONTH_THRESHOLD - ref_count
        bar = _progress_bar(ref_count, REF_MONTH_THRESHOLD)
        progress_lines.append(
            f"🌟 <b>Premium месяц:</b> {bar} ({remaining} ост.)"
        )
    else:
        progress_lines.append("🌟 Premium месяц — ✅ Получено!")

    progress = "\n".join(progress_lines)

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашай друзей и получай награды!\n\n"
        f"📊 Твоих рефералов: <b>{format_number(ref_count)}</b>\n\n"
        f"🎯 <b>Награды:</b>\n{progress}\n\n"
        f"🔗 Твоя реферальная ссылка:\n"
        f"<code>{ref_link}</code>\n\n"
        f"📤 Поделись ссылкой с друзьями!"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=referral_kb()
    )
    await callback.answer()


def _progress_bar(current: int, total: int, length: int = 10) -> str:
    """Рисует прогресс-бар из эмодзи."""
    filled = min(int(current / total * length), length)
    empty = length - filled
    return "▓" * filled + "░" * empty
