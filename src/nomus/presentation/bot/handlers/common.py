import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from nomus.config.bot_user_properties import BotUserProps
from nomus.domain.interfaces.repo_interface import IUserRepository
from nomus.config.settings import Messages, Settings
from nomus.application.services.auth_service import AuthService

log: logging.Logger = logging.getLogger(__name__)

router = Router()


def get_start_kb(lexicon: Messages) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=lexicon.registration_button)],
        [KeyboardButton(text=lexicon.start_ordering_button)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


async def _send_language_selection(message: Message):
    """Helper function to send the language selection menu."""
    kb = [
        [InlineKeyboardButton(
            text=BotUserProps.DEF_SELECT_LANG_UZ, callback_data=BotUserProps.CALLBACK_LANG_UZ
        )],
        [InlineKeyboardButton(
            text=BotUserProps.DEF_SELECT_LANG_EN, callback_data=BotUserProps.CALLBACK_LANG_EN
        )],
        [InlineKeyboardButton(
            text=BotUserProps.DEF_SELECT_LANG_RU, callback_data=BotUserProps.CALLBACK_LANG_RU
            )],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer(
        BotUserProps.DEF_SELECT_LANG_PHRASE,
        reply_markup=keyboard,
    )


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    storage: IUserRepository,
    settings: Settings,
):
    await state.clear()

    if not message.from_user:
        return

    # ===================================================================
    # РЕЖИМ БЫСТРОГО СТАРТА ДЛЯ DEVELOPMENT (SKIP_REGISTRATION=True)
    # ===================================================================
    if settings.env.is_development() and settings.skip_registration:
        log.warning("DEV MODE: SKIP_REGISTRATION is enabled, creating mock registered user")

        # Создаём "фейкового" зарегистрированного пользователя
        await storage.save_or_update_user(
            telegram_id=message.from_user.id,
            data={
                "username": message.from_user.username,
                "full_name": message.from_user.full_name,
                "language_code": "ru",
                "phone_number": "+998901234567",  # MOCK номер
                "registered_at": datetime.now().isoformat(),
            }
        )

        lexicon = settings.messages.ru
        await message.answer(
            lexicon.dev_mode_skip_registration,
            reply_markup=get_start_kb(lexicon)
        )
        return

    # ===================================================================
    # ОБЫЧНЫЙ FLOW: Проверка регистрации
    # ===================================================================

    # Проверяем, есть ли пользователь в storage
    user_data = await storage.get_user_by_telegram_id(message.from_user.id)

    # ===================================================================
    # ВЕТВЛЕНИЕ А: Зарегистрированный пользователь (есть телефон)
    # ===================================================================
    if user_data and user_data.get("phone_number"):
        log.info("Registered user %s returned", message.from_user.id)

        # Получаем язык пользователя
        lang_code = await storage.get_user_language(message.from_user.id)
        if not lang_code or lang_code not in ["uz", "ru", "en"]:
            lang_code = "ru"  # Fallback

        lexicon = getattr(settings.messages, lang_code)

        # Приветствие "С возвращением!"
        await message.answer(
            lexicon.welcome_back,
            reply_markup=get_start_kb(lexicon)
        )
        return

    # ===================================================================
    # ВЕТВЛЕНИЕ Б: Новый пользователь ИЛИ незарегистрированный
    # ===================================================================
    log.info("New or unregistered user %s", message.from_user.id)

    # Определяем язык из Telegram API
    lang_code = message.from_user.language_code
    if lang_code not in ["uz", "ru", "en"]:
        lang_code = "ru"  # Fallback на русский

    # Создаём "черновик" пользователя с базовыми данными
    await storage.save_or_update_user(
        telegram_id=message.from_user.id,
        data={
            "username": message.from_user.username,
            "full_name": message.from_user.full_name,
            "language_code": lang_code,
            # phone_number НЕ сохраняем - пользователь ещё не зарегистрирован
        }
    )

    # Если язык определён из Telegram, показываем информационное сообщение
    if message.from_user.language_code in ["uz", "ru", "en"]:
        lexicon = getattr(settings.messages, lang_code)
        await message.answer(
            lexicon.language_detected.format(lang_code=lang_code.upper())
        )

    # Показываем выбор языка
    await _send_language_selection(message)


# @router.message(LexiconFilter('cancel_button'))
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, lexicon: Messages):
    # ...

    await state.clear()
    await message.answer(lexicon.cancel_button, reply_markup=get_start_kb(lexicon))


@router.message(Command("language"))
async def cmd_language(message: Message, lexicon: Messages):
    """Displays language selection buttons."""
    await _send_language_selection(message)


@router.callback_query(F.data.startswith("lang_"))
async def process_lang_select(
    callback: CallbackQuery, storage: IUserRepository, settings: Settings
):
    """Saves the selected language and shows User Agreement."""
    if not callback.from_user:
        return
    assert callback.data is not None
    _language_code = callback.data.split("_")[1]  # 'lang_ru' -> 'ru'

    log.info("Language selected: %s", _language_code)

    # Save the language choice to our storage
    await storage.update_user_language(
        telegram_id=callback.from_user.id, language_code=_language_code
    )

    # Let the user know the language has been changed
    assert isinstance(callback.message, Message)

    # We will get the new lexicon after updating language in storage
    # TODO: how can I reload lexicon?
    # Probabli I can change state and handle it in another handler where will bw updated lexicon
    new_lexicon = getattr(settings.messages, _language_code)
    await callback.message.edit_text(new_lexicon.language_changed_prompt)

    # Show User Agreement and Agree button
    kb = get_agreement_kb(new_lexicon, _language_code)
    await callback.message.answer(
        new_lexicon.user_agreement_prompt,
        reply_markup=kb,
    )

    await callback.answer()


def get_agreement_kb(lexicon: Messages, lang_code: str) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(
                text=f"📄 {lexicon.user_agreement_button}",
                url=lexicon.user_agreement_url,
            )
        ],
        [
            InlineKeyboardButton(
                text=lexicon.user_agreement_accept_button,
                callback_data=f"agree_terms_{lang_code}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("agree_terms_"))
async def process_agreement(callback: CallbackQuery, settings: Settings):
    """Handles agreement to terms."""
    if not callback.from_user:
        return
    assert callback.data is not None
    _language_code = callback.data.split("_")[2]  # 'agree_terms_ru' -> 'ru'

    new_lexicon = getattr(settings.messages, _language_code)

    assert isinstance(callback.message, Message)
    # Delete the agreement message or edit it to remove buttons?
    # Let's delete it to keep chat clean, or just edit text.
    await callback.message.delete()

    # Send welcome message with main menu
    await callback.message.answer(
        new_lexicon.welcome, reply_markup=get_start_kb(new_lexicon)
    )

    await callback.answer()
