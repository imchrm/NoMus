# src/nomus/presentation/bot/middlewares/l10n_middleware.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from nomus.config.settings import Settings
from nomus.config.settings import Messages
from nomus.domain.interfaces.repo_interface import IStorageRepository
from nomus.application.services.language_service import (
    get_user_language_with_fallback,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
)


class L10nMiddleware(BaseMiddleware):
    """
    Middleware для определения языка пользователя и внедрения lexicon в handlers.

    Решение 3: Использует get_user_language_with_fallback() для автоматического
    определения языка с приоритетом:
    1. Сохранённый язык в storage
    2. Язык из Telegram API (если поддерживается)
    3. Русский по умолчанию
    """

    def __init__(self, settings: Settings, storage: IStorageRepository):
        self.settings = settings
        self.storage = storage

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем объект пользователя, если он есть
        user: User | None = data.get("event_from_user")

        lang_code = DEFAULT_LANGUAGE  # Fallback на русский
        if user:
            # Решение 3: Используем централизованную функцию с fallback
            lang_code = await get_user_language_with_fallback(user, self.storage)

        # Если языка нет в конфиге, откатываемся на default
        if not hasattr(self.settings.messages, lang_code):
            lang_code = DEFAULT_LANGUAGE

        # Получаем нужный объект Messages и "внедряем" его в хендлер
        lexicon_obj: Messages = getattr(self.settings.messages, lang_code)
        data["lexicon"] = lexicon_obj

        return await handler(event, data)
