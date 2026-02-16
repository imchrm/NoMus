"""Settings submenu handler: Language, Profile, About."""

import logging

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from nomus.config.settings import Messages, Settings
from nomus.domain.interfaces.repo_interface import IUserRepository
from nomus.presentation.bot.filters.text_equals import TextEquals
from nomus.presentation.bot.states.language import LanguageStates

log = logging.getLogger(__name__)

router = Router()

_LANG_LABELS = {"uz": "O'zbekcha", "en": "English", "ru": "Русский"}


# ─── Helpers ─────────────────────────────────────────────────────────


def _settings_kb(lexicon: Messages) -> InlineKeyboardMarkup:
    """Inline keyboard for settings submenu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lexicon.settings_language_button, callback_data="settings_lang")],
        [InlineKeyboardButton(text=lexicon.settings_profile_button, callback_data="settings_profile")],
        [InlineKeyboardButton(text=lexicon.settings_about_button, callback_data="settings_about")],
    ])


async def _show_settings_menu(message: Message, lexicon: Messages) -> None:
    """Send settings inline menu (reused from multiple places)."""
    await message.answer(lexicon.settings_title, reply_markup=_settings_kb(lexicon))


# ─── Entry point: reply-keyboard button ─────────────────────────────


@router.message(TextEquals("settings_button"))
async def open_settings(message: Message, lexicon: Messages) -> None:
    await _show_settings_menu(message, lexicon)


# ─── Language ────────────────────────────────────────────────────────


@router.callback_query(F.data == "settings_lang")
async def settings_language(
    callback: CallbackQuery,
    state: FSMContext,
    lexicon: Messages,
) -> None:
    assert isinstance(callback.message, Message)

    # Отмечаем, что после выбора языка нужно вернуться в настройки
    await state.set_state(LanguageStates.waiting_for_language)
    await state.update_data(return_to="settings")

    from nomus.presentation.bot.handlers.common import _send_language_selection
    await _send_language_selection(callback.message)
    await callback.answer()


# ─── Profile ─────────────────────────────────────────────────────────


@router.callback_query(F.data == "settings_profile")
async def settings_profile(
    callback: CallbackQuery,
    storage: IUserRepository,
    lexicon: Messages,
) -> None:
    assert isinstance(callback.message, Message)

    if not callback.from_user:
        await callback.answer()
        return

    user_data = await storage.get_user_by_telegram_id(callback.from_user.id)
    if not user_data or not user_data.get("phone_number"):
        await callback.message.answer(lexicon.profile_no_data)
        await callback.answer()
        return

    lang_code = user_data.get("language_code", "—")
    lang_label = _LANG_LABELS.get(lang_code, lang_code)

    text = lexicon.profile_title.format(
        full_name=user_data.get("full_name") or "—",
        phone=user_data.get("phone_number") or "—",
        language=lang_label,
    )
    await callback.message.answer(text)
    await callback.answer()


# ─── About / Help ────────────────────────────────────────────────────


@router.callback_query(F.data == "settings_about")
async def settings_about(
    callback: CallbackQuery,
    lexicon: Messages,
) -> None:
    assert isinstance(callback.message, Message)
    await callback.message.answer(lexicon.about_text)
    await callback.answer()
