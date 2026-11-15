"""
Шёпот Bot — Premium и оплата через Telegram Stars
"""
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    Message,
)

from database import Database
from keyboards import premium_menu_kb, main_menu_kb, message_unmasked_kb
from utils import escape_html
from config import PRICE_PREMIUM_WEEK, PRICE_PREMIUM_MONTH, PRICE_UNMASK

router = Router()


@router.callback_query(F.data == "premium_menu")
async def show_premium_menu(callback: CallbackQuery, db: Database):
    is_prem = await db.is_premium(callback.from_user.id)
    user = await db.get_user(callback.from_user.id)

    if is_prem:
        until = user["premium_until"][:10] if user and user["premium_until"] else "∞"
        status = f"✅ Твой Premium активен до <b>{until}</b>\n\nМожешь продлить:"
    else:
        status = "🌟 Открой все возможности с <b>Premium!</b>"

    text = (
        f"⭐ <b>Шёпот Premium</b>\n\n"
        f"{status}\n\n"
        f"<b>Что даёт Premium:</b>\n"
        f"🔓 Раскрывай отправителей сообщений\n"
        f"🔤 Подсказки: первая буква имени\n"
        f"📨 200 сообщений в день (вместо 15)\n"
        f"✏️ Персональное приветствие\n"
        f"⚡ Быстрый кулдаун\n\n"
        f"💳 Оплата через <b>Telegram Stars</b> ⭐"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=premium_menu_kb()
    )
    await callback.answer()


# ──────────────────────── Покупка Premium ────────────────────────

@router.callback_query(F.data.startswith("buy_premium:"))
async def buy_premium(callback: CallbackQuery, bot: Bot):
    period = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if period == "week":
        price = PRICE_PREMIUM_WEEK
        title = "⭐ Premium на 7 дней"
        desc = "Все возможности Шёпот Premium на 1 неделю"
        payload = "premium:7"
    elif period == "month":
        price = PRICE_PREMIUM_MONTH
        title = "⭐ Premium на 30 дней"
        desc = "Все возможности Шёпот Premium на 1 месяц"
        payload = "premium:30"
    else:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=title,
            description=desc,
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=price)],
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:80]}", show_alert=True)


# ──────────────────────── Pre-checkout ────────────────────────

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    """Подтверждаем все pre-checkout запросы."""
    await query.answer(ok=True)


# ──────────────────────── Успешная оплата ────────────────────────

@router.message(F.successful_payment)
async def successful_payment(message: Message, db: Database):
    """Обработка успешной оплаты Stars."""
    payment = message.successful_payment
    payload = payment.invoice_payload
    user_id = message.from_user.id
    amount = payment.total_amount

    # Сохраняем платёж
    await db.create_payment(
        user_id=user_id,
        amount=amount,
        payment_type=payload,
        tg_payment_id=payment.telegram_payment_charge_id,
    )

    if payload.startswith("premium:"):
        days = int(payload.split(":")[1])
        await db.set_premium(user_id, days)

        await message.answer(
            f"🎉 <b>Premium активирован!</b>\n\n"
            f"Ты получил Premium на <b>{days} дней</b>.\n\n"
            f"Наслаждайся всеми возможностями Шёпот! 🌟",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )

    elif payload.startswith("unmask:"):
        msg_id = int(payload.split(":")[1])
        await db.unmask_message(msg_id)
        msg = await db.get_message(msg_id)

        if msg:
            sender = await db.get_user(msg["sender_id"])
            if sender:
                name = escape_html(sender["first_name"] or "Аноним")
                uname = f"@{sender['username']}" if sender["username"] else "юзернейм скрыт"
                await message.answer(
                    f"🔓 <b>Отправитель раскрыт!</b>\n\n"
                    f"👤 Имя: {name}\n"
                    f"📎 Username: {uname}",
                    parse_mode="HTML",
                    reply_markup=message_unmasked_kb(msg_id),
                )
                return

        await message.answer(
            "🔓 Оплата прошла, но сообщение не найдено.",
            reply_markup=main_menu_kb(),
        )
