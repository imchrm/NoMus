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
from nomus.domain.interfaces.repo_interface import IUserRepository
from nomus.presentation.bot.states.registration import RegistrationStates
from nomus.application.services.auth_service import AuthService
from nomus.application.services.order_service import OrderService
from nomus.presentation.bot.handlers.ordering import _start_tariff_selection
from nomus.presentation.bot.filters.text_equals import TextEquals
from nomus.config.settings import Messages

router = Router()


@router.message(TextEquals("registration_button"))
async def start_registration(message: Message, state: FSMContext, lexicon: Messages):
    # kb = [[KeyboardButton(text=lexicon.send_contact_button, request_contact=True)]]
    # keyboard = ReplyKeyboardMarkup(
    #     keyboard=kb, resize_keyboard=True, one_time_keyboard=True
    # )

    # prompt_text = lexicon.send_contact_prompt
    # if prompt_text is None:
    #     # It's error of configuration of lexicon. `send_contact_prompt` is undefined for current language.
    #     raise ValueError(
    #         "Missing translation for 'send_contact_prompt'. Check your lexicon configuration (configuration.yaml: messages)."
    #     )

    # await message.answer(prompt_text, reply_markup=keyboard)
    # await state.set_state(RegistrationStates.waiting_for_phone)

    # Make a button for sharing location of current user
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=lexicon.share_location_button, request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer(lexicon.share_location_prompt, reply_markup=kb)
    await state.set_state(RegistrationStates.waiting_for_location)


@router.message(RegistrationStates.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext, lexicon: Messages):
    if not message.location:
        return

    await state.update_data(
        latitude=message.location.latitude, longitude=message.location.longitude
    )

    # Make a button for sharing phone number of current user
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=lexicon.confirm_phone_button, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer(lexicon.share_phone_number_prompt, reply_markup=kb)
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(
    message: Message, state: FSMContext, auth_service: AuthService, lexicon: Messages
):
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
    assert message.contact is not None  # assertion for Pylance, second variant
    phone = message.contact.phone_number

    await state.update_data(phone=phone)

    # Send verification code
    await auth_service.send_verification_code(phone)

    await message.answer(
        lexicon.code_sent_prompt,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(RegistrationStates.waiting_for_sms_code)


@router.message(RegistrationStates.waiting_for_sms_code)
async def process_code(
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    order_service: OrderService,
    storage: IUserRepository,
    lexicon: Messages,
):
    if not message.from_user:
        # We cannot process a message without a user (for example, from a channel)
        return

    if not message.text:
        await message.answer(lexicon.send_code_as_text_prompt)
        return

    code = message.text
    if not code.isdigit() or len(code) != 4:
        await message.answer(lexicon.enter_4_digits_prompt)
        return

    # Verify code (simplified for PoC: always check against '1234')
    if code == "1234":
        data = await state.get_data()
        phone = data.get("phone")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if phone:
            user_data = User(
                id=message.from_user.id,
                telegram_id=message.from_user.id,
                phone_number=phone,
                registered_at=datetime.now(),
                latitude=latitude,
                longitude=longitude,
            ).model_dump()  # Преобразуем Pydantic модель в словарь для сохранения

            # Теперь мы не создаем нового пользователя, а обновляем существующего,
            # добавляя номер телефона и другие данные.
            # Метод register_user в auth_service должен использовать save_or_update_user.
            await auth_service.user_repo.save_or_update_user(
                message.from_user.id, user_data
            )

            await message.answer(lexicon.registration_successful)

            # Get user language from storage
            lang_code = await storage.get_user_language(message.from_user.id)
            if lang_code is None:
                raise ValueError("User language not found in storage.")

            # --- Transition to the ordering flow ---
            # We don't know the user's language yet, so we use the default.
            # TODO: Возможно нужно меньше образаться к внешним ресурсам для получения пользовательского языка
            # тогда получение языка можно сделать синхронным
            lang_code = await storage.get_user_language(message.from_user.id)
            # TODO: Проверить утверждение, пересмотреть логику!
            assert lang_code is not None  # утверждаем, что язык точно не None
            await _start_tariff_selection(
                message, state, order_service, lexicon, lang_code
            )

        else:
            await message.answer(lexicon.phone_number_error)
    else:
        await message.answer(lexicon.invalid_code_error)
