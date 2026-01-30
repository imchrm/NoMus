"""
Сервис для работы с языковыми предпочтениями пользователей.

Предоставляет функции для получения языка пользователя с fallback логикой
и константы для поддерживаемых языков.
"""

import logging
from aiogram.types import User as TelegramUser
from nomus.domain.interfaces.repo_interface import IUserRepository

log: logging.Logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = ["ru", "uz", "en"]
DEFAULT_LANGUAGE = "ru"


async def get_user_language_with_fallback(
    telegram_user: TelegramUser,
    storage: IUserRepository
) -> str:
    """
    Получает язык пользователя с fallback на Telegram API и default.

    Приоритет:
    1. Сохранённый язык в storage
    2. Язык из Telegram API (если поддерживается)
    3. Русский по умолчанию

    Args:
        telegram_user: Объект пользователя Telegram (message.from_user)
        storage: Репозиторий пользователей

    Returns:
        Код языка (ru, uz или en)
    """
    # 1. Пробуем получить из storage
    lang_code = await storage.get_user_language(telegram_user.id)
    if lang_code in SUPPORTED_LANGUAGES:
        log.debug("Language for user %s found in storage: %s", telegram_user.id, lang_code)
        return lang_code

    # 2. Пробуем Telegram API
    telegram_lang = telegram_user.language_code
    if telegram_lang in SUPPORTED_LANGUAGES:
        log.info(
            "Language for user %s not in storage, using Telegram API: %s",
            telegram_user.id, telegram_lang
        )
        # Сохраняем для будущих запросов
        await storage.update_user_language(telegram_user.id, telegram_lang)
        return telegram_lang

    # 3. Default
    log.info(
        "Language for user %s not found, using default: %s",
        telegram_user.id, DEFAULT_LANGUAGE
    )
    return DEFAULT_LANGUAGE


def is_valid_language(lang_code: str | None) -> bool:
    """
    Проверяет, является ли код языка поддерживаемым.

    Args:
        lang_code: Код языка для проверки

    Returns:
        True если язык поддерживается, False иначе
    """
    return lang_code in SUPPORTED_LANGUAGES
