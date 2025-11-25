from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from nomus.presentation.bot.states.registration import RegistrationStates
from nomus.application.services.auth_service import AuthService

router = Router()


@router.message(F.text == "Регистрация")
async def start_registration(message: Message, state: FSMContext):
    kb = [[KeyboardButton(text="Отправить контакт", request_contact=True)]]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, one_time_keyboard=True
    )

    await message.answer(
        "Пожалуйста, отправьте ваш контакт для регистрации.", reply_markup=keyboard
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext, auth_service: AuthService):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)

    # Send verification code
    await auth_service.send_verification_code(phone)

    await message.answer(
        "Код подтверждения отправлен (см. консоль). Введите 4 цифры:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(RegistrationStates.waiting_for_sms_code)


@router.message(RegistrationStates.waiting_for_sms_code)
async def process_code(message: Message, state: FSMContext, auth_service: AuthService):
    code = message.text
    if not code.isdigit() or len(code) != 4:
        await message.answer("Пожалуйста, введите 4 цифры.")
        return

    # Verify code (simplified for PoC: always check against '1234')
    if code == "1234":
        data = await state.get_data()
        phone = data.get("phone")
        await auth_service.register_user(phone)

        await message.answer("Регистрация успешно завершена!")
        await state.clear()
    else:
        await message.answer("Неверный код. Попробуйте еще раз.")
