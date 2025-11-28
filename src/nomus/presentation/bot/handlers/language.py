import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from nomus.presentation.bot.states.flow import FlowStates
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.config.settings import Messages, Settings

log: logging.Logger = logging.getLogger(__name__)

router = Router()


def get_start_kb(lexicon: Messages) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=lexicon.registration_button)],
        [KeyboardButton(text=lexicon.start_ordering_button)]
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
    await message.answer("Iltimos, tilingizni tanlang / Please select your language / Пожалуйста, выберите язык:", reply_markup=keyboard)

@router.message(Command("language"))
async def cmd_language(message: Message, lexicon: Messages):
    """Displays language selection buttons."""
    await _send_language_selection(message)


@router.callback_query(F.data.startswith("lang_"))
async def process_lang_select(
    callback: CallbackQuery, storage: MemoryStorage, settings: Settings
):
    """Saves the selected language."""
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
    # 
    # Assert that the message is an accessible `Message` object, not `InaccessibleMessage`.
    # This satisfies Pylance and ensures the .edit_text() method exists.
    assert isinstance(callback.message, Message)
    # Шаг 1: Редактируем сообщение, убирая инлайн-клавиатуру
    await callback.message.edit_text(
        "Язык изменен.\nLanguage has been changed.\nTil oʻzgartirildi."
    )

    # Получаем новый, правильный lexicon после обновления
    new_lexicon = getattr(settings.messages, _language_code)

    # Шаг 2: Отправляем новое сообщение, чтобы показать основную клавиатуру
    await callback.message.answer(
        new_lexicon.welcome, reply_markup=get_start_kb(new_lexicon)
    )
    
    # Answer the callback to remove the "loading" state on the button
    await callback.answer()
