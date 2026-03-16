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
from nomus.domain.interfaces.repo_interface import IStorageRepository, IUserRepository
from nomus.presentation.bot.states.registration import RegistrationStates
from nomus.application.services.auth_service import AuthService
from nomus.application.services.order_service import OrderService
from nomus.presentation.bot.handlers.ordering import _start_service_selection
from nomus.presentation.bot.filters.emoji_prefix_equals import EmojiPrefixEquals
from nomus.config.settings import Messages

router = Router()


@router.message(EmojiPrefixEquals("registration_button"))
async def start_registration(message: Message, state: FSMContext, lexicon: Messages):

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
    message: Message,
    state: FSMContext,
    auth_service: AuthService,
    order_service: OrderService,
    storage: IStorageRepository,
    lexicon: Messages,
):
    if not message.from_user:
        return

    assert message.contact is not None  # assertion for Pylance
    phone = message.contact.phone_number

    data = await state.get_data()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    # Регистрируем пользователя через AuthService и получаем server_user_id
    server_user_id = await auth_service.register_user(phone)

    user_data = User(
        id=message.from_user.id,
        telegram_id=message.from_user.id,
        phone_number=phone,
        registered_at=datetime.now(),
        latitude=latitude,
        longitude=longitude,
        server_user_id=server_user_id,
    ).model_dump()

    # Обновляем пользователя в локальном хранилище
    await auth_service.user_repo.save_or_update_user(
        message.from_user.id, user_data
    )

    # Синхронизируем данные с remote storage (если используется)
    await storage.flush()

    await message.answer(
        lexicon.registration_successful,
        reply_markup=ReplyKeyboardRemove(),
    )

    # Set is_registered flag in FSM for keyboard building
    await state.update_data(is_registered=True)

    # Get user language from storage
    lang_code = await storage.get_user_language(message.from_user.id)
    if lang_code is None:
        raise ValueError("User language not found in storage.")

    # --- Transition to the ordering flow ---
    await _start_service_selection(
        message, state, order_service, lexicon
    )
