"""
🤫 Шёпот (Whisper) — Telegram-бот анонимных сообщений
Главный файл запуска
"""
import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import Database
from middlewares import DatabaseMiddleware, UserActivityMiddleware

# Handlers
from handlers import start, messages, profile, premium, referral, admin


# ── Простой пинг-сервер для предотвращения таймаутов на Render ──
async def health_check(request):
    return web.Response(text="Bot is running OK", status=200)

async def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.getLogger("whisper").info(f"🌐 Keep-Alive веб-сервер запущен на порту {port}")


async def main():
    # ── Логирование ──
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger("whisper")

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан! Создай файл .env по примеру .env.example")
        sys.exit(1)

    # ── База данных ──
    db = Database()
    await db.connect()
    logger.info("✅ База данных подключена")

    # ── Бот и диспетчер ──
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ── Middleware ──
    dp.update.middleware(DatabaseMiddleware(db))
    dp.message.middleware(UserActivityMiddleware())
    dp.callback_query.middleware(UserActivityMiddleware())

    # ── Роутеры ──
    dp.include_routers(
        start.router,
        messages.router,
        profile.router,
        premium.router,
        referral.router,
        admin.router,
    )

    # ── Запуск веб-сервера для Render (Keep-Alive) ──
    await start_web_server()

    # ── Startup ──
    bot_info = await bot.get_me()
    logger.info(f"🤫 Шёпот запущен как @{bot_info.username}")
    logger.info(f"   ID: {bot_info.id}")

    # ── Устанавливаем команды ──
    from aiogram.types import BotCommand

    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню"),
    ])

    # ── Polling ──
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close()
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
