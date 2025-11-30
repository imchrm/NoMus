import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.config.settings import Messages, Settings

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
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_uz")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer(
        "Iltimos, tilingizni tanlang / Please select your language / Пожалуйста, выберите язык:",
        reply_markup=keyboard,
    )


@router.message(Command("language"))
async def cmd_language(message: Message, lexicon: Messages):
    """Displays language selection buttons."""
    await _send_language_selection(message)


@router.callback_query(F.data.startswith("lang_"))
async def process_lang_select(
    callback: CallbackQuery, storage: MemoryStorage, settings: Settings
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
