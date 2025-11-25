from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from nomus.application.services.auth_service import AuthService
from nomus.application.services.order_service import OrderService


class ServiceLayerMiddleware(BaseMiddleware):
    def __init__(self, auth_service: AuthService, order_service: OrderService):
        self.auth_service = auth_service
        self.order_service = order_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["auth_service"] = self.auth_service
        data["order_service"] = self.order_service
        return await handler(event, data)
