from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    # Создаем кнопку, которая запрашивает ИМЕННО КОНТАКТ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Подтвердить мой номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer(
        "Нажмите кнопку ниже, чтобы поделиться своим контактом.", reply_markup=kb
    )


@router.message(F.contact)
async def handle_contact(message: Message):
    # Эта проверка нужна только для защиты от ручной отправки чужого контакта через скрепку.
    # Если пользователь нажал кнопку выше - условие выполнится автоматически.
    if message.contact.user_id != message.from_user.id:
        await message.answer(
            "Пожалуйста, отправляйте только СВОЙ контакт через кнопку в меню!"
        )
        return

    # Логика регистрации
    user_phone = message.contact.phone_number
    await message.answer(
        f"Спасибо! Ваш номер {user_phone} принят.", reply_markup=ReplyKeyboardRemove()
    )
