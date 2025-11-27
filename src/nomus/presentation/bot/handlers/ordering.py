from aiogram import Router, F
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
from nomus.presentation.bot.states.registration import RegistrationStates
from nomus.application.services.order_service import OrderService
from nomus.application.services.auth_service import AuthService

router = Router()


@router.message(F.text == "Сделать заказ")
async def start_ordering(
    message: Message,
    state: FSMContext,
    order_service: OrderService,
    auth_service: AuthService,
):
    # We can't process an action without a user (e.g., from a channel)
    if not message.from_user:
        return

    # Check if the user is registered
    if not await auth_service.is_user_registered(message.from_user.id):
        await message.answer(
            "Чтобы сделать заказ, вам необходимо сначала зарегистрироваться. Нажмите 'Регистрация' в меню."
        )
        return

    tariffs = await order_service.get_tariffs()
    # Store tariffs in state for validation
    await state.update_data(tariffs=tariffs)

    kb = [[KeyboardButton(text=t)] for t in tariffs.keys()]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer("Выберите тариф:", reply_markup=keyboard)
    await state.set_state(OrderStates.selecting_tariff)


@router.message(OrderStates.selecting_tariff)
async def process_tariff(message: Message, state: FSMContext):
    tariff_name = message.text
    data = await state.get_data()
    tariffs = data.get("tariffs", {})

    if tariff_name not in tariffs:
        await message.answer("Пожалуйста, выберите тариф из списка.")
        return

    amount = tariffs[tariff_name]
    await state.update_data(tariff=tariff_name, amount=amount)

    # Inline keyboard for payment
    kb = [[InlineKeyboardButton(text=f"Оплатить {amount} сум", callback_data="pay")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    await message.answer(
        f"Вы выбрали тариф {tariff_name}. Сумма к оплате: {amount}",
        reply_markup=keyboard,
    )
    await state.set_state(OrderStates.waiting_for_payment)


@router.callback_query(OrderStates.waiting_for_payment, F.data == "pay")
async def process_payment(
    callback: CallbackQuery, state: FSMContext, order_service: OrderService
):
    # Assert that the message is an accessible `Message` object, not `InaccessibleMessage`.
    # This satisfies Pylance and ensures the .edit_text() method exists.
    assert isinstance(callback.message, Message)

    await callback.message.edit_text("Обработка платежа...")

    data = await state.get_data()
    # Assume user phone is stored in context or passed differently.
    # For PoC, we might need to ask for it or assume it's from the user object if registered.
    # Here we just use the telegram user id/name as placeholder if phone not in state
    user_phone = str(callback.from_user.id)

    success = await order_service.create_order(
        user_phone=user_phone, tariff=data["tariff"], amount=data["amount"]
    )

    if success:
        await callback.message.edit_text("Заказ успешно оплачен и создан!")
    else:
        await callback.message.edit_text("Ошибка оплаты.")

    await state.clear()
