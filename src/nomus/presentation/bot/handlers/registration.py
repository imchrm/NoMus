from datetime import datetime
from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from nomus.domain.entities.user import User
from nomus.presentation.bot.states.registration import RegistrationStates
from nomus.presentation.bot.states.ordering import OrderStates
from nomus.application.services.auth_service import AuthService
from nomus.application.services.order_service import OrderService
from nomus.presentation.bot.filters.lexicon_filter import LexiconFilter

router = Router()


@router.message(LexiconFilter('registration_button'))
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
    
    # TODO: Check if you are guaranteed to receive a `phone_number` after `request_contact`
    # 
    # Telegram API(https://core.telegram.org/bots/api): 
    # KeyboardButton: 
    # Field: https://core.telegram.org/bots/api
    # Type: Boolean
    # Description: Optional. If True, the user's phone number will be sent as a contact when the button is pressed. Available in private chats only.
    # if message.contact is None:
    #     await message.answer("Пожалуйста, отправьте ваш контакт.")
    #     return
    
    # First variant
    # if message.contact is None:
    #     assert False, "message.contact should not be None here"
    assert message.contact is not None # assertion for Pylance, second variant
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
async def process_code(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    order_service: OrderService,
):
    if not message.from_user:
        # We cannot process a message without a user (for example, from a channel)
        return

    if not message.text:
        await message.answer("Пожалуйста, отправьте код в виде текстового сообщения.")
        return

    code = message.text
    if not code.isdigit() or len(code) != 4:
        await message.answer("Пожалуйста, введите 4 цифры.")
        return

    # Verify code (simplified for PoC: always check against '1234')
    if code == "1234":
        data = await state.get_data()
        phone = data.get("phone")
        
        if phone:
            user_data = User(
                id=message.from_user.id,
                telegram_id=message.from_user.id,
                phone_number=phone,
                registered_at=datetime.now()
            ).model_dump() # Преобразуем Pydantic модель в словарь для сохранения
            
            # Теперь мы не создаем нового пользователя, а обновляем существующего,
            # добавляя номер телефона и другие данные.
            # Метод register_user в auth_service должен использовать save_or_update_user.
            await auth_service.user_repo.save_or_update_user(message.from_user.id, user_data)
            
            await message.answer("Регистрация успешно завершена!")
            
            # --- Transition to the ordering flow ---
            tariffs = await order_service.get_tariffs()
            await state.update_data(tariffs=tariffs)
            kb = [[KeyboardButton(text=t)] for t in tariffs.keys()]
            keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer("Теперь вы можете сделать свой первый заказ. Выберите тариф:", reply_markup=keyboard)
            await state.set_state(OrderStates.selecting_tariff)
            
        else:
            message.answer("Не удалось получить номер телефона. Попробуйте еще раз.")
    else:
        await message.answer("Неверный код. Попробуйте еще раз.")
