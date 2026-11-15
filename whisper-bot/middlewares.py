"""
Шёпот Bot — Middleware (антиспам, регистрация)
"""
from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from database import Database


class DatabaseMiddleware(BaseMiddleware):
    """Прокидывает объект БД во все хендлеры."""

    def __init__(self, db: Database):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        return await handler(event, data)


class UserActivityMiddleware(BaseMiddleware):
    """Обновляет last_active и данные пользователя при каждом событии."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        db: Database = data.get("db")
        user = None

        # Извлекаем пользователя из разных типов событий
        if hasattr(event, "from_user") and event.from_user:
            user = event.from_user
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user = event.message.from_user

        if user and db and not user.is_bot:
            existing = await db.get_user(user.id)
            if existing:
                await db.update_user_info(user.id, user.username, user.first_name)
            # Записываем в data для удобства
            data["db_user"] = existing

        return await handler(event, data)
