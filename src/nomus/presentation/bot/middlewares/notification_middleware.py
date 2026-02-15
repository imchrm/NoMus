"""
Middleware для проверки непрочитанных уведомлений при каждом взаимодействии пользователя.

При каждом входящем сообщении/callback проверяет NMservices на наличие
изменений статуса заказов и отправляет уведомления пользователю.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery

from nomus.application.services.order_service import OrderService
from nomus.config.settings import Messages

log = logging.getLogger(__name__)

# Локализованные шаблоны уведомлений о смене статуса
_STATUS_TEMPLATES: dict[str, dict[str, str]] = {
    "ru": {
        "confirmed": (
            "Заказ #{order_id} подтверждён.\n"
            "Услуга: {service_name}\n"
            "Стоимость: {amount} сум\n"
            "Мастер скоро свяжется с вами."
        ),
        "in_progress": (
            "Заказ #{order_id}: мастер в пути.\n"
            "Услуга: {service_name}\n"
            "Стоимость: {amount} сум"
        ),
        "completed": (
            "Заказ #{order_id} выполнен!\n"
            "Услуга: {service_name}\n"
            "Стоимость: {amount} сум\n"
            "Спасибо за использование NoMus!"
        ),
        "cancelled": (
            "Заказ #{order_id} отменён.\n"
            "Услуга: {service_name}\n"
            "Стоимость: {amount} сум"
        ),
    },
    "en": {
        "confirmed": (
            "Order #{order_id} confirmed.\n"
            "Service: {service_name}\n"
            "Price: {amount} sum\n"
            "The specialist will contact you shortly."
        ),
        "in_progress": (
            "Order #{order_id}: specialist is on the way.\n"
            "Service: {service_name}\n"
            "Price: {amount} sum"
        ),
        "completed": (
            "Order #{order_id} completed!\n"
            "Service: {service_name}\n"
            "Price: {amount} sum\n"
            "Thank you for using NoMus!"
        ),
        "cancelled": (
            "Order #{order_id} cancelled.\n"
            "Service: {service_name}\n"
            "Price: {amount} sum"
        ),
    },
    "uz": {
        "confirmed": (
            "Buyurtma #{order_id} tasdiqlandi.\n"
            "Xizmat: {service_name}\n"
            "Narxi: {amount} so'm\n"
            "Usta tez orada siz bilan bog'lanadi."
        ),
        "in_progress": (
            "Buyurtma #{order_id}: usta yo'lda.\n"
            "Xizmat: {service_name}\n"
            "Narxi: {amount} so'm"
        ),
        "completed": (
            "Buyurtma #{order_id} bajarildi!\n"
            "Xizmat: {service_name}\n"
            "Narxi: {amount} so'm\n"
            "NoMus dan foydalanganingiz uchun rahmat!"
        ),
        "cancelled": (
            "Buyurtma #{order_id} bekor qilindi.\n"
            "Xizmat: {service_name}\n"
            "Narxi: {amount} so'm"
        ),
    },
}


def _format_price(raw_price: Any) -> str:
    if raw_price is None:
        return "—"
    try:
        value = int(Decimal(str(raw_price)))
        return f"{value:,}".replace(",", " ")
    except (InvalidOperation, ValueError):
        return str(raw_price)


def _get_telegram_id(event: TelegramObject) -> int | None:
    """Extract telegram_id from any event type."""
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    return None


class NotificationMiddleware(BaseMiddleware):
    """
    Проверяет pending-уведомления при каждом взаимодействии пользователя.

    Работает как «pull при заходе»: если NMservices не смог доставить
    push-уведомление (бот был выключен или юзер заблокировал его),
    этот middleware покажет уведомление при следующем визите.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        telegram_id = _get_telegram_id(event)
        if not telegram_id:
            return await handler(event, data)

        order_service: OrderService | None = data.get("order_service")
        bot: Bot | None = data.get("bot")
        lexicon: Messages | None = data.get("lexicon")

        if order_service and bot:
            await self._check_and_send(telegram_id, order_service, bot, lexicon)

        return await handler(event, data)

    async def _check_and_send(
        self,
        telegram_id: int,
        order_service: OrderService,
        bot: Bot,
        lexicon: Messages | None,
    ) -> None:
        try:
            notifications = await order_service.get_pending_notifications(telegram_id)
            if not notifications:
                return

            # Determine language from lexicon (already resolved by L10nMiddleware)
            lang = "ru"
            if lexicon:
                # Attempt to detect from lexicon — check a known field
                if hasattr(lexicon, "cancel_button"):
                    if lexicon.cancel_button == "Cancel":
                        lang = "en"
                    elif lexicon.cancel_button == "Bekor qilish":
                        lang = "uz"

            templates = _STATUS_TEMPLATES.get(lang, _STATUS_TEMPLATES["ru"])
            order_ids: list[int] = []

            for n in notifications:
                status = n.get("status", "")
                template = templates.get(status)
                if not template:
                    continue

                text = template.format(
                    order_id=n.get("order_id", "—"),
                    service_name=n.get("service_name") or "—",
                    amount=_format_price(n.get("total_amount")),
                )

                try:
                    await bot.send_message(telegram_id, text)
                    order_ids.append(n["order_id"])
                except Exception as e:
                    log.error("Failed to send notification to %s: %s", telegram_id, e)

            # Acknowledge delivered notifications
            if order_ids:
                await order_service.ack_notifications(telegram_id, order_ids)

        except Exception as e:
            log.error("NotificationMiddleware error for %s: %s", telegram_id, e)
