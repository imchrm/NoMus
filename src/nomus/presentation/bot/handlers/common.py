from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.presentation.bot.filters.text_equals import TextEquals
from nomus.config.settings import Messages
from nomus.presentation.bot.handlers.language import _send_language_selection

router = Router()


def get_start_kb(lexicon: Messages) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=lexicon.registration_button)],
        [KeyboardButton(text=lexicon.start_ordering_button)],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, lexicon: Messages, storage: MemoryStorage
):
    await state.clear()
    if message.from_user:
        await storage.save_or_update_user(
            telegram_id=message.from_user.id,
            data={
                "username": message.from_user.username,
                "full_name": message.from_user.full_name,
                "language_code": "ru",  # Устанавливаем язык по умолчанию
            },
        )

    await _send_language_selection(message)


@router.message(Command("cancel"))
@router.message(TextEquals("cancel_button"))
async def cmd_cancel(message: Message, state: FSMContext, lexicon: Messages):
    # ...

    await state.clear()
    await message.answer(lexicon.cancel_button, reply_markup=get_start_kb(lexicon))
