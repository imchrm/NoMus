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
from nomus.application.services.order_service import OrderService
from nomus.application.services.language_service import (
    get_user_language_with_fallback,
    is_valid_language,
    SUPPORTED_LANGUAGES,
)
from nomus.presentation.bot.states.language import LanguageStates

log: logging.Logger = logging.getLogger(__name__)

router = Router()


# ─── Keyboard builders ───────────────────────────────────────────────


def get_main_kb(
    lexicon: Messages,
    is_registered: bool = False,
    has_active_order: bool = False,
) -> ReplyKeyboardMarkup:
    """
    Создаёт контекстную главную клавиатуру.

    - Не зарегистрирован: [Регистрация] [Настройки]
    - Зарегистрирован, нет заказа: [Сделать заказ] [Настройки]
    - Зарегистрирован, есть заказ: [Сделать заказ] [Мой заказ] [Настройки]
    """
    kb: list[list[KeyboardButton]] = []

    if not is_registered:
        kb.append([KeyboardButton(text=lexicon.registration_button)])
    else:
        kb.append([KeyboardButton(text=lexicon.start_ordering_button)])
        if has_active_order:
            kb.append([KeyboardButton(text=lexicon.my_order_button)])

    kb.append([KeyboardButton(text=lexicon.settings_button)])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# Backward-compatible alias
def get_start_kb(lexicon: Messages, show_registration: bool = True) -> ReplyKeyboardMarkup:
    return get_main_kb(lexicon, is_registered=not show_registration)


# ─── Language selection helpers ──────────────────────────────────────


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


async def ensure_user_language(
    message: Message,
    storage: IUserRepository,
    state: FSMContext,
    return_to: str | None = None,
) -> str | None:
    """
    Проверяет наличие языка пользователя.
    Если язык отсутствует — показывает выбор языка и возвращает None.
    Если язык есть — возвращает language_code.
    """
    if not message.from_user:
        return None

    lang_code = await storage.get_user_language(message.from_user.id)
    if is_valid_language(lang_code):
        return lang_code

    log.info("Language not found for user %s, showing selection", message.from_user.id)
    await state.set_state(LanguageStates.waiting_for_language)
    if return_to:
        await state.update_data(return_to=return_to)
    await _send_language_selection(message)
    return None


# ─── /start command ──────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    order_service: OrderService,
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

        await storage.save_or_update_user(
            telegram_id=message.from_user.id,
            data={
                "username": message.from_user.username,
                "full_name": message.from_user.full_name,
                "language_code": "ru",
                "phone_number": "+998901234567",
                "registered_at": datetime.now().isoformat(),
            }
        )

        lexicon = settings.messages.ru
        await message.answer(
            lexicon.dev_mode_skip_registration,
            reply_markup=get_main_kb(lexicon, is_registered=True)
        )
        return

    # ===================================================================
    # ОБЫЧНЫЙ FLOW: Проверка регистрации
    # ===================================================================
    user_data = await storage.get_user_by_telegram_id(message.from_user.id)

    # ===================================================================
    # ВЕТВЛЕНИЕ А: Зарегистрированный пользователь (есть телефон)
    # ===================================================================
    if user_data and user_data.get("phone_number"):
        log.info("Registered user %s returned", message.from_user.id)

        lang_code = await get_user_language_with_fallback(message.from_user, storage)
        lexicon = getattr(settings.messages, lang_code)

        # Проверяем наличие активного заказа для контекстного меню
        has_active = False
        active = await order_service.get_active_order(message.from_user.id)
        has_active = active is not None

        await message.answer(
            lexicon.welcome_back,
            reply_markup=get_main_kb(lexicon, is_registered=True, has_active_order=has_active)
        )
        return

    # ===================================================================
    # ВЕТВЛЕНИЕ Б: Новый пользователь ИЛИ незарегистрированный
    # ===================================================================
    log.info("New or unregistered user %s", message.from_user.id)

    lang_code = message.from_user.language_code
    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = "ru"

    await storage.save_or_update_user(
        telegram_id=message.from_user.id,
        data={
            "username": message.from_user.username,
            "full_name": message.from_user.full_name,
            "language_code": lang_code,
        }
    )

    if message.from_user.language_code in SUPPORTED_LANGUAGES:
        lexicon = getattr(settings.messages, lang_code)
        await message.answer(
            lexicon.language_detected.format(lang_code=lang_code.upper())
        )

    await _send_language_selection(message)


# ─── /cancel command ─────────────────────────────────────────────────


@router.message(Command("cancel"))
async def cmd_cancel(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    lexicon: Messages,
):
    """Отменяет текущее действие и возвращает в главное меню."""
    await state.clear()

    if not message.from_user:
        await message.answer(lexicon.cancel_button, reply_markup=get_main_kb(lexicon))
        return

    is_registered = await auth_service.is_user_registered(message.from_user.id)

    await message.answer(
        lexicon.cancel_button,
        reply_markup=get_main_kb(lexicon, is_registered=is_registered)
    )


# ─── /language command ───────────────────────────────────────────────


@router.message(Command("language"))
async def cmd_language(message: Message, lexicon: Messages):
    """Displays language selection buttons."""
    await _send_language_selection(message)


# ─── Language callback ───────────────────────────────────────────────


@router.callback_query(F.data.startswith("lang_"))
async def process_lang_select(
    callback: CallbackQuery,
    storage: IUserRepository,
    settings: Settings,
    state: FSMContext,
):
    """
    Saves the selected language and handles return to interrupted action.
    """
    if not callback.from_user:
        return
    assert callback.data is not None
    _language_code = callback.data.split("_")[1]  # 'lang_ru' -> 'ru'

    log.info("Language selected: %s", _language_code)

    await storage.update_user_language(
        telegram_id=callback.from_user.id, language_code=_language_code
    )

    assert isinstance(callback.message, Message)

    new_lexicon = getattr(settings.messages, _language_code)
    await callback.message.edit_text(new_lexicon.language_changed_prompt)

    # Проверяем, нужно ли вернуться к прерванному действию
    current_state = await state.get_state()
    if current_state == LanguageStates.waiting_for_language.state:
        data = await state.get_data()
        return_to = data.get("return_to")

        if return_to == "ordering":
            await state.clear()
            log.info("Returning user %s to ordering after language selection", callback.from_user.id)
            from nomus.presentation.bot.handlers.ordering import _start_service_selection

            await callback.message.answer(new_lexicon.order_continue_after_language)
            await callback.answer()
            return

        if return_to == "settings":
            await state.clear()
            # Возвращаемся в настройки после смены языка
            from nomus.presentation.bot.handlers.settings import _show_settings_menu
            await _show_settings_menu(callback.message, new_lexicon)
            await callback.answer()
            return

        await state.clear()

    # Обычный flow — показываем User Agreement
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
    await callback.message.delete()

    await callback.message.answer(
        new_lexicon.welcome, reply_markup=get_main_kb(new_lexicon)
    )

    await callback.answer()
