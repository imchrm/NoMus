import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.config.settings import Messages

log: logging.Logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("language"))
async def cmd_language(message: Message, lexicon: Messages):
    """Displays language selection buttons."""
    kb = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_uz")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("Please select your language:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang_"))
async def process_lang_select(callback: CallbackQuery, storage: MemoryStorage):
    """Saves the selected language."""
    if not callback.from_user:
        return
    assert callback.data is not None
    lang_code = callback.data.split("_")[1]  # 'lang_ru' -> 'ru'

    log.info("Language selected: %s", lang_code)
    
    # Save the language choice to our storage
    await storage.update_user_language(
        telegram_id=callback.from_user.id, lang_code=lang_code
    )

    # Let the user know the language has been changed
    # We can't use the lexicon object here easily, so we send a multilingual message.
    # Assert that the message is an accessible `Message` object, not `InaccessibleMessage`.
    # This satisfies Pylance and ensures the .edit_text() method exists.
    assert isinstance(callback.message, Message)
    await callback.message.edit_text(
        "Язык изменен.\nLanguage has been changed.\nTil oʻzgartirildi."
    )

    # Answer the callback to remove the "loading" state on the button
    await callback.answer()
