"""My Orders handler: shows the user's active orders as a text list."""

import logging
from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.types import Message

from nomus.config.settings import Messages
from nomus.application.services.order_service import OrderService
from nomus.presentation.bot.filters.emoji_prefix_equals import EmojiPrefixEquals

log = logging.getLogger(__name__)

router = Router()

_STATUS_KEY_MAP = {
    "pending": "status_pending",
    "confirmed": "status_confirmed",
    "in_progress": "status_in_progress",
    "completed": "status_completed",
    "cancelled": "status_cancelled",
}


def _format_price(raw: Decimal | str | None) -> str:
    if raw is None:
        return "—"
    try:
        value = int(Decimal(str(raw)))
        return f"{value:,}".replace(",", " ")
    except (InvalidOperation, ValueError):
        return str(raw)


@router.message(EmojiPrefixEquals("my_orders_button"))
async def show_my_orders(
    message: Message,
    order_service: OrderService,
    lexicon: Messages,
) -> None:
    if not message.from_user:
        return

    orders = await order_service.get_active_orders(message.from_user.id)

    if not orders:
        await message.answer(lexicon.no_active_order)
        return

    # Build list of order items
    items: list[str] = []
    for order in orders:
        status_key = _STATUS_KEY_MAP.get(order.get("status", ""), "")
        status_label = getattr(lexicon, status_key, order.get("status", "—"))

        item = lexicon.my_orders_item.format(
            order_id=order.get("order_id", "—"),
            service_name=order.get("service_name") or "—",
            amount=_format_price(order.get("total_amount")),
            address=order.get("address_text") or "—",
            status=status_label,
        )
        items.append(item)

    text = lexicon.my_orders_title + "\n\n" + "\n\n".join(items)
    await message.answer(text)
