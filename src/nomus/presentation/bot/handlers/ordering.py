import logging
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from nomus.presentation.bot.states.ordering import OrderStates
from nomus.application.services.order_service import OrderService
from nomus.application.services.auth_service import AuthService
from nomus.application.services.language_service import get_user_language_with_fallback
from nomus.domain.interfaces.repo_interface import IUserRepository
from nomus.presentation.bot.filters.text_equals import TextEquals
from nomus.config.settings import Messages

log: logging.Logger = logging.getLogger(__name__)

router = Router()


def _format_price(raw_price: str | Decimal | int | float | None) -> str:
    """Форматирует цену: '150000.00' → '150 000'."""
    if raw_price is None:
        return "—"
    try:
        value = int(Decimal(str(raw_price)))
        return f"{value:,}".replace(",", " ")
    except (InvalidOperation, ValueError):
        return str(raw_price)


def _build_services_keyboard(services: list[dict]) -> InlineKeyboardMarkup:
    """Строит inline-клавиатуру со списком услуг."""
    buttons: list[list[InlineKeyboardButton]] = []
    for svc in services:
        name = svc.get("name", "—")
        price = _format_price(svc.get("base_price"))
        duration = svc.get("duration_minutes")
        duration_text = f" ({duration} min)" if duration else ""
        label = f"{name} — {price} сум{duration_text}"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"svc_{svc['id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _start_service_selection(
    message: Message,
    state: FSMContext,
    order_service: OrderService,
    lexicon: Messages,
) -> None:
    """Вспомогательная функция: запускает выбор услуги."""
    services = await order_service.get_services()

    if not services:
        await message.answer(lexicon.no_services_available)
        return

    # Сохраняем услуги в состоянии для последующей валидации
    await state.update_data(services={str(s["id"]): s for s in services})

    keyboard = _build_services_keyboard(services)
    await message.answer(lexicon.select_service_prompt, reply_markup=keyboard)
    await state.set_state(OrderStates.selecting_service)


# ─── 1. Начало заказа ───────────────────────────────────────────────


@router.message(TextEquals("start_ordering_button"))
async def start_ordering(
    message: Message,
    state: FSMContext,
    order_service: OrderService,
    auth_service: AuthService,
    storage: IUserRepository,
    lexicon: Messages,
) -> None:
    if not message.from_user:
        return

    # Проверка регистрации
    if not await auth_service.is_user_registered(message.from_user.id):
        await message.answer(lexicon.order_registration_prompt)
        return

    await _start_service_selection(message, state, order_service, lexicon)


# ─── 2. Выбор услуги (inline callback) ──────────────────────────────


@router.callback_query(OrderStates.selecting_service, F.data.startswith("svc_"))
async def process_service_selection(
    callback: CallbackQuery,
    state: FSMContext,
    lexicon: Messages,
) -> None:
    assert isinstance(callback.message, Message)

    service_id = callback.data.removeprefix("svc_")  # type: ignore[union-attr]
    data = await state.get_data()
    services: dict = data.get("services", {})

    selected = services.get(service_id)
    if not selected:
        await callback.answer("Service not found")
        return

    await state.update_data(
        selected_service=selected,
        service_id=int(service_id),
    )

    # Убираем inline-кнопки и просим адрес
    await callback.message.edit_text(
        f"{lexicon.select_service_prompt} {selected['name']}"
    )
    await callback.message.answer(
        lexicon.enter_address_prompt, reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(OrderStates.entering_address)
    await callback.answer()


# ─── 3. Ввод адреса ─────────────────────────────────────────────────


@router.message(OrderStates.entering_address)
async def process_address(
    message: Message,
    state: FSMContext,
    lexicon: Messages,
) -> None:
    if not message.text or not message.text.strip():
        await message.answer(lexicon.enter_address_prompt)
        return

    address = message.text.strip()
    await state.update_data(address=address)

    # Показываем summary
    data = await state.get_data()
    svc = data["selected_service"]
    price = _format_price(svc.get("base_price"))
    duration = svc.get("duration_minutes", "—")

    summary = lexicon.order_summary.format(
        service_name=svc["name"],
        duration=duration,
        price=price,
        address=address,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=lexicon.confirm_order_button, callback_data="order_confirm"
                ),
                InlineKeyboardButton(
                    text=lexicon.cancel_order_button, callback_data="order_cancel"
                ),
            ]
        ]
    )

    await message.answer(summary, reply_markup=keyboard)
    await state.set_state(OrderStates.confirming_order)


# ─── 4. Подтверждение заказа ─────────────────────────────────────────


@router.callback_query(OrderStates.confirming_order, F.data == "order_confirm")
async def process_order_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    order_service: OrderService,
    lexicon: Messages,
) -> None:
    assert isinstance(callback.message, Message)

    await callback.message.edit_text(lexicon.order_creating)

    data = await state.get_data()
    service_id: int = data["service_id"]
    address: str = data["address"]

    # Получаем server_user_id
    server_user_id = await order_service.get_server_user_id(callback.from_user.id)
    if not server_user_id:
        log.error(
            "server_user_id not found for telegram_id=%s", callback.from_user.id
        )
        await callback.message.edit_text(lexicon.order_creation_error)
        await state.clear()
        await callback.answer()
        return

    # Создаём заказ
    result = await order_service.create_order(
        server_user_id=server_user_id,
        service_id=service_id,
        address_text=address,
    )

    if result:
        order_id = result.get("order_id", "—")
        await callback.message.edit_text(
            lexicon.order_created.format(order_id=order_id)
        )
    else:
        await callback.message.edit_text(lexicon.order_creation_error)

    await state.clear()
    await callback.answer()


# ─── 5. Отмена заказа ───────────────────────────────────────────────


@router.callback_query(OrderStates.confirming_order, F.data == "order_cancel")
async def process_order_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    lexicon: Messages,
) -> None:
    assert isinstance(callback.message, Message)

    await callback.message.edit_text(lexicon.order_cancelled)
    await state.clear()
    await callback.answer()
