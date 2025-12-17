# src/nomus/presentation/bot/middlewares/l10n_middleware.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from nomus.config.settings import Settings
from nomus.config.settings import Messages
from nomus.domain.interfaces.repo_interface import IStorageRepository


class L10nMiddleware(BaseMiddleware):
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

        lang_code = "en"  # Fallback
        if user:
            # 1. Пытаемся получить язык из нашей "базы данных"
            user_data = await self.storage.get_user_by_telegram_id(user.id)
            if user_data and user_data.get("language_code"):
                lang_code = user_data["language_code"]
            # 2. Если в базе нет, берем из профиля Telegram
            elif user.language_code in ("ru", "en", "uz"):
                lang_code = user.language_code

        # Получаем нужный объект Messages и "внедряем" его в хендлер
        # под ключом 'lexicon'.
        # Это и есть ключевой момент: мы один раз используем строковый ключ,
        # чтобы получить нужный объект.
        # Если языка нет в конфиге, откатываемся на английский
        if not hasattr(self.settings.messages, lang_code):
            lang_code = "en"
        lexicon_obj: Messages = getattr(self.settings.messages, lang_code)
        data["lexicon"] = lexicon_obj

        return await handler(event, data)
