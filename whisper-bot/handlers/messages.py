"""
Шёпот Bot — Обработчик анонимных сообщений
"""
from datetime import datetime, timezone
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from keyboards import (
    message_actions_kb,
    message_unmasked_kb,
    after_send_kb,
    cancel_kb,
    confirm_unmask_kb,
    main_menu_kb,
)
from handlers.start import SendingState
from utils import escape_html, check_banned_words, sender_hint
from config import (
    FREE_MESSAGES_PER_DAY,
    PREMIUM_MESSAGES_PER_DAY,
    MESSAGE_COOLDOWN_SECONDS,
    MAX_MESSAGE_LENGTH,
    PRICE_UNMASK,
)

router = Router()


# ──────────────────────── Отправка сообщения ────────────────────────

@router.message(SendingState.waiting_message, F.text)
async def receive_anon_message(message: Message, db: Database, state: FSMContext, bot: Bot):
    """Получение текста анонимного сообщения и доставка получателю."""
    data = await state.get_data()
    target_id = data.get("target_user_id")
    target_code = data.get("target_code", "")

    if not target_id:
        await state.clear()
        await message.answer("❌ Ошибка. Попробуй по ссылке заново.", reply_markup=main_menu_kb())
        return

    sender_id = message.from_user.id
    text = message.text.strip()

    # ── Валидация ──
    if len(text) > MAX_MESSAGE_LENGTH:
        await message.answer(
            f"❌ Сообщение слишком длинное! Максимум {MAX_MESSAGE_LENGTH} символов.",
            reply_markup=cancel_kb(),
        )
        return

    if check_banned_words(text):
        await message.answer(
            "❌ Сообщение содержит недопустимый контент.",
            reply_markup=cancel_kb(),
        )
        return

    # ── Проверка лимитов ──
    is_prem = await db.is_premium(sender_id)
    daily_limit = PREMIUM_MESSAGES_PER_DAY if is_prem else FREE_MESSAGES_PER_DAY
    sent_today = await db.count_sent_today(sender_id)

    if sent_today >= daily_limit:
        if is_prem:
            await message.answer(
                "📛 Ты достиг дневного лимита сообщений. Попробуй завтра!",
                reply_markup=main_menu_kb(),
            )
        else:
            await message.answer(
                f"📛 Ты достиг лимита <b>{FREE_MESSAGES_PER_DAY} сообщений</b> в день.\n\n"
                "⭐ Оформи <b>Premium</b> чтобы отправлять до 200 сообщений!",
                parse_mode="HTML",
                reply_markup=main_menu_kb(),
            )
        await state.clear()
        return

    # ── Кулдаун ──
    last_time = await db.last_message_time(sender_id, target_id)
    if last_time:
        now = datetime.now(timezone.utc)
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
        diff = (now - last_time).total_seconds()
        if diff < MESSAGE_COOLDOWN_SECONDS:
            wait = int(MESSAGE_COOLDOWN_SECONDS - diff)
            await message.answer(
                f"⏳ Подожди ещё <b>{wait} сек.</b> перед следующим сообщением.",
                parse_mode="HTML",
                reply_markup=cancel_kb(),
            )
            return

    # ── Сохраняем и доставляем ──
    msg_id = await db.create_message(sender_id, target_id, text)
    await state.clear()

    # Уведомляем получателя
    target_user = await db.get_user(target_id)
    target_is_premium = await db.is_premium(target_id)
    escaped_text = escape_html(text)

    notification = f"💌 <b>Новое анонимное сообщение!</b>\n\n<i>«{escaped_text}»</i>"

    # Подсказка для Premium
    if target_is_premium:
        sender = await db.get_user(sender_id)
        if sender:
            hint = sender_hint(sender["username"], sender["first_name"])
            notification += f"\n\n🔮 <b>Premium подсказка:</b>\n{hint}"

    try:
        await bot.send_message(
            target_id,
            notification,
            parse_mode="HTML",
            reply_markup=message_actions_kb(msg_id, show_unmask=True),
        )
    except Exception:
        pass  # Получатель заблокировал бота

    # Подтверждение отправителю
    await message.answer(
        "✅ <b>Сообщение отправлено анонимно!</b>\n\n"
        "Получатель не знает, кто ты 🤫",
        parse_mode="HTML",
        reply_markup=after_send_kb(target_code),
    )


@router.message(SendingState.waiting_message)
async def non_text_anon_message(message: Message):
    """Если отправлен не текст."""
    await message.answer(
        "📝 Пожалуйста, отправь <b>текстовое</b> сообщение.",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )


# ──────────────────────── «Отправить ещё» ────────────────────────

@router.callback_query(F.data.startswith("send_more:"))
async def send_more(callback: CallbackQuery, db: Database, state: FSMContext):
    code = callback.data.split(":", 1)[1]
    target_user = await db.get_user_by_code(code)
    if not target_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    target_id = target_user["user_id"]
    if target_id == callback.from_user.id:
        await callback.answer("Нельзя писать самому себе!", show_alert=True)
        return

    name = escape_html(target_user["first_name"] or "Аноним")
    await callback.message.edit_text(
        f"📩 Напиши ещё одно анонимное сообщение для <b>{name}</b> 👇",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await state.set_state(SendingState.waiting_message)
    await state.update_data(target_user_id=target_id, target_code=code)
    await callback.answer()


# ──────────────────────── Ответ на сообщение ────────────────────────

class ReplyState:
    """FSM State для ответа на анонимное сообщение."""
    pass


from aiogram.fsm.state import State, StatesGroup


class ReplyingState(StatesGroup):
    waiting_reply = State()


@router.callback_query(F.data.startswith("reply:"))
async def start_reply(callback: CallbackQuery, db: Database, state: FSMContext):
    msg_id = int(callback.data.split(":")[1])
    msg = await db.get_message(msg_id)

    if not msg:
        await callback.answer("❌ Сообщение не найдено", show_alert=True)
        return

    # Определяем кому отвечаем: если я получатель — отвечаю отправителю, и наоборот
    user_id = callback.from_user.id
    if msg["receiver_id"] == user_id:
        reply_to_user = msg["sender_id"]
    elif msg["sender_id"] == user_id:
        reply_to_user = msg["receiver_id"]
    else:
        await callback.answer("❌ Это не твоё сообщение", show_alert=True)
        return

    await callback.message.answer(
        "💬 Напиши ответ — он будет доставлен <b>анонимно</b> 👇",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await state.set_state(ReplyingState.waiting_reply)
    await state.update_data(reply_to_user=reply_to_user, original_msg_id=msg_id)
    await callback.answer()


@router.message(ReplyingState.waiting_reply, F.text)
async def process_reply(message: Message, db: Database, state: FSMContext, bot: Bot):
    data = await state.get_data()
    reply_to_user = data.get("reply_to_user")
    original_msg_id = data.get("original_msg_id")
    sender_id = message.from_user.id

    if not reply_to_user:
        await state.clear()
        await message.answer("❌ Ошибка.", reply_markup=main_menu_kb())
        return

    text = message.text.strip()
    if len(text) > MAX_MESSAGE_LENGTH:
        await message.answer(
            f"❌ Максимум {MAX_MESSAGE_LENGTH} символов.",
            reply_markup=cancel_kb(),
        )
        return

    if check_banned_words(text):
        await message.answer("❌ Недопустимый контент.", reply_markup=cancel_kb())
        return

    # Сохраняем
    msg_id = await db.create_message(sender_id, reply_to_user, text, reply_to_id=original_msg_id)
    await state.clear()

    # Получаем оригинальное сообщение для цитаты
    original = await db.get_message(original_msg_id)
    original_preview = ""
    if original:
        preview_text = original["text"][:80]
        if len(original["text"]) > 80:
            preview_text += "…"
        original_preview = f"\n\n↩️ <i>В ответ на: «{escape_html(preview_text)}»</i>"

    escaped = escape_html(text)

    try:
        await bot.send_message(
            reply_to_user,
            f"💬 <b>Анонимный ответ!</b>\n\n<i>«{escaped}»</i>{original_preview}",
            parse_mode="HTML",
            reply_markup=message_actions_kb(msg_id),
        )
    except Exception:
        pass

    await message.answer(
        "✅ <b>Ответ отправлен анонимно!</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(ReplyingState.waiting_reply)
async def non_text_reply(message: Message):
    await message.answer(
        "📝 Отправь <b>текстовое</b> сообщение.",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )


# ──────────────────────── Раскрытие отправителя ────────────────────────

@router.callback_query(F.data.startswith("unmask:"))
async def unmask_sender(callback: CallbackQuery, db: Database):
    msg_id = int(callback.data.split(":")[1])
    msg = await db.get_message(msg_id)

    if not msg:
        await callback.answer("❌ Сообщение не найдено", show_alert=True)
        return

    if msg["receiver_id"] != callback.from_user.id:
        await callback.answer("❌ Это не твоё сообщение", show_alert=True)
        return

    if msg["is_unmasked"]:
        # Уже раскрыто — показываем инфо
        sender = await db.get_user(msg["sender_id"])
        if sender:
            name = sender["first_name"] or "—"
            uname = f"@{sender['username']}" if sender["username"] else "нет юзернейма"
            await callback.answer(f"Отправитель: {name} ({uname})", show_alert=True)
        return

    # Проверяем бесплатные раскрытия
    user = await db.get_user(callback.from_user.id)
    if user and user["free_unmasks"] > 0:
        await callback.message.answer(
            f"🔓 У тебя <b>{user['free_unmasks']}</b> бесплатных раскрытий.\n"
            f"Использовать одно для этого сообщения?",
            parse_mode="HTML",
            reply_markup=confirm_unmask_kb(msg_id),
        )
        await callback.answer()
        return

    # Запрашиваем оплату Stars
    await callback.message.answer(
        f"🔓 Раскрыть отправителя этого сообщения?\n\n"
        f"💰 Стоимость: <b>{PRICE_UNMASK} ⭐ Stars</b>",
        parse_mode="HTML",
        reply_markup=confirm_unmask_kb(msg_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_unmask:"))
async def confirm_unmask(callback: CallbackQuery, db: Database, bot: Bot):
    msg_id = int(callback.data.split(":")[1])
    msg = await db.get_message(msg_id)

    if not msg or msg["receiver_id"] != callback.from_user.id:
        await callback.answer("❌ Ошибка", show_alert=True)
        return

    user_id = callback.from_user.id

    # Попытка использовать бесплатное раскрытие
    used_free = await db.use_free_unmask(user_id)

    if used_free:
        # Бесплатно
        await db.unmask_message(msg_id)
        sender = await db.get_user(msg["sender_id"])
        if sender:
            name = escape_html(sender["first_name"] or "Аноним")
            uname = f"@{sender['username']}" if sender["username"] else "юзернейм скрыт"
            await callback.message.edit_text(
                f"🔓 <b>Отправитель раскрыт!</b>\n\n"
                f"👤 {name}\n"
                f"📎 {uname}\n\n"
                f"<i>Использовано бесплатное раскрытие</i>",
                parse_mode="HTML",
                reply_markup=message_unmasked_kb(msg_id),
            )
        await callback.answer()
        return

    # Платное — отправляем invoice через Telegram Stars
    from aiogram.types import LabeledPrice

    try:
        await bot.send_invoice(
            chat_id=user_id,
            title="🔓 Раскрыть отправителя",
            description="Узнай, кто отправил тебе это анонимное сообщение",
            payload=f"unmask:{msg_id}",
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label="Раскрытие отправителя", amount=PRICE_UNMASK)],
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка оплаты: {str(e)[:100]}", show_alert=True)
