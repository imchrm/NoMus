import logging
import uuid
from aiogram import F, Router
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from nomus.presentation.bot.states.ordering import OrderStates
from nomus.application.services.order_service import OrderService
from nomus.application.services.auth_service import AuthService
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.presentation.bot.filters.text_equals import TextEquals
from nomus.config.settings import Messages

log: logging.Logger = logging.getLogger(__name__)

router = Router()


async def _start_tariff_selection(
    message: Message,
    state: FSMContext,
    order_service: OrderService,
    lexicon: Messages,
    lang_code: str,
):
    """Helper to start the tariff selection process."""
    tariffs = await order_service.get_tariffs(lang=lang_code)
    # Store tariffs in state for validation
    await state.update_data(tariffs=tariffs)

    kb = [[KeyboardButton(text=t)] for t in tariffs.keys()]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(lexicon.select_tariff_prompt, reply_markup=keyboard)
    await state.set_state(OrderStates.selecting_tariff)


@router.message(TextEquals("start_ordering_button"))
async def start_ordering(
    message: Message,
    state: FSMContext,
    order_service: OrderService,
    auth_service: AuthService,
    storage: MemoryStorage,
    lexicon: Messages,
):
    # We can't process an action without a user (e.g., from a channel)
    if not message.from_user:
        return

    # Check if the user is registered
    if not await auth_service.is_user_registered(message.from_user.id):
        await message.answer(lexicon.order_registration_prompt)
        return

    # Get user language from storage
    lang_code = await storage.get_user_language(message.from_user.id)
    if lang_code is None:
        raise ValueError("User language not found in storage.")

    await _start_tariff_selection(message, state, order_service, lexicon, lang_code)


@router.message(OrderStates.selecting_tariff)
async def process_tariff(message: Message, state: FSMContext, lexicon: Messages):
    if not message.text:
        return
    tariff_name = message.text.strip()  # Убираем лишние пробелы с концов строки
    data = await state.get_data()
    tariffs = data.get("tariffs", {})
    log.info(
        "Processing tariff selection. Tariff name: '%s'. Tariffs in state: %s",
        tariff_name,
        tariffs,
    )

    if tariff_name not in tariffs:
        await message.answer(lexicon.choose_tariff_from_list_prompt)
        return

    amount = tariffs[tariff_name]
    await state.update_data(tariff=tariff_name, amount=amount)

    # Inline keyboard for payment
    kb = [
        [
            InlineKeyboardButton(
                text=lexicon.payment_button.format(amount=amount), callback_data="pay"
            )
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    await message.answer(
        lexicon.payment_prompt.format(tariff_name=tariff_name, amount=amount),
        reply_markup=keyboard,
    )
    await state.set_state(OrderStates.waiting_for_payment)
    current_state = await state.get_state()
    log.debug("State set to: %s", current_state)


@router.callback_query(OrderStates.waiting_for_payment, F.data == "pay")
async def process_payment(
    callback: CallbackQuery,
    state: FSMContext,
    order_service: OrderService,
    lexicon: Messages,
):
    # Assert that the message is an accessible `Message` object, not `InaccessibleMessage`.
    # This satisfies Pylance and ensures the .edit_text() method exists.
    assert isinstance(callback.message, Message)

    await callback.message.edit_text(lexicon.payment_processing)

    data = await state.get_data()
    # Assume user phone is stored in context or passed differently.
    # For PoC, we might need to ask for it or assume it's from the user object if registered.
    # Here we just use the telegram user id/name as placeholder if phone not in state
    user_id = str(callback.from_user.id)

    success = await order_service.create_order(
        user_id=user_id, tariff=data["tariff"], amount=data["amount"]
    )
    order_id = uuid.uuid4()  # TODO: replace with real order id
    if success:
        await callback.message.delete()
        await callback.message.answer(
            lexicon.order_success.format(order_id=order_id),
            reply_markup=ReplyKeyboardRemove(),
        )
        await callback.message.answer(lexicon.order_status)
    else:
        await callback.message.edit_text(lexicon.payment_error)

    await state.clear()
