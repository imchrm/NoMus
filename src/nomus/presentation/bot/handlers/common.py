from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from nomus.presentation.bot.filters.lexicon_filter import LexiconFilter
from nomus.config.settings import Messages

router = Router()


def get_start_kb(lexicon: Messages) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=lexicon.registration_button)],
        [KeyboardButton(text=lexicon.start_ordering_button)]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, lexicon: Messages):
    await state.clear()
    # TODO: Add logo of service
    # file = InputFileUnion()
    # await message.answer_photo(photo=file)
    await message.answer(
        lexicon.welcome,
        reply_markup=get_start_kb(lexicon)
    )

@router.message(Command("cancel"))
@router.message(LexiconFilter('cancel_button'))
async def cmd_cancel(message: Message, state: FSMContext, lexicon: Messages):
    # ...

    await state.clear()
    await message.answer(lexicon.cancel_button, reply_markup=get_start_kb(lexicon))
