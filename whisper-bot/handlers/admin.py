"""
Шёпот Bot — Админ-панель
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message

from database import Database
from utils import format_number
from config import ADMIN_IDS

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database):
    if not _is_admin(message.from_user.id):
        return

    stats = await db.stats()

    text = (
        "📊 <b>Админ-панель Шёпот</b>\n\n"
        f"👥 Всего пользователей: <b>{format_number(stats['total_users'])}</b>\n"
        f"👤 Сегодня новых: <b>{format_number(stats['today_users'])}</b>\n"
        f"🟢 Активных 24ч: <b>{format_number(stats['active_24h'])}</b>\n"
        f"⭐ Premium: <b>{format_number(stats['premium_users'])}</b>\n\n"
        f"💌 Всего сообщений: <b>{format_number(stats['total_messages'])}</b>\n"
        f"📩 Сегодня сообщений: <b>{format_number(stats['today_messages'])}</b>\n\n"
        f"💰 Выручка (Stars): <b>{format_number(stats['total_revenue'])} ⭐</b>\n\n"
        "<b>Команды:</b>\n"
        "/broadcast <i>текст</i> — рассылка\n"
        "/ban <i>user_id</i> — бан\n"
        "/unban <i>user_id</i> — разбан\n"
        "/stats — эта панель"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def stats_command(message: Message, db: Database):
    if not _is_admin(message.from_user.id):
        return
    await admin_panel(message, db)


@router.message(Command("broadcast"))
async def broadcast_command(message: Message, db: Database, bot: Bot):
    if not _is_admin(message.from_user.id):
        return

    text = message.text.replace("/broadcast", "", 1).strip()
    if not text:
        await message.answer("❌ Использование: /broadcast <i>текст</i>", parse_mode="HTML")
        return

    user_ids = await db.all_user_ids()
    total = len(user_ids)
    sent = 0
    failed = 0

    status_msg = await message.answer(f"📡 Начинаю рассылку для {total} пользователей...")

    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

        # Telegram rate limit: ~30 сообщений/сек
        if (sent + failed) % 25 == 0:
            await asyncio.sleep(1)
            try:
                await status_msg.edit_text(
                    f"📡 Рассылка: {sent + failed}/{total}\n"
                    f"✅ Доставлено: {sent}\n❌ Ошибок: {failed}"
                )
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Всего: {total}\n"
        f"✅ Доставлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        parse_mode="HTML",
    )


@router.message(Command("ban"))
async def ban_command(message: Message, db: Database):
    if not _is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Использование: /ban <i>user_id</i>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный user_id")
        return

    await db.ban_user(target_id, ban=True)
    await message.answer(f"🚫 Пользователь <code>{target_id}</code> заблокирован.", parse_mode="HTML")


@router.message(Command("unban"))
async def unban_command(message: Message, db: Database):
    if not _is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Использование: /unban <i>user_id</i>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный user_id")
        return

    await db.ban_user(target_id, ban=False)
    await message.answer(f"✅ Пользователь <code>{target_id}</code> разблокирован.", parse_mode="HTML")
