from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from nomus.presentation.bot.states.registration import RegistrationStates
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()


def get_start_kb():
    kb = [[KeyboardButton(text="Регистрация")], [KeyboardButton(text="Сделать заказ")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в NoMus! Выберите действие:", reply_markup=get_start_kb()
    )


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_start_kb())
