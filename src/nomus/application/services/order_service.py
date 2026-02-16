import logging
from typing import Any, Optional

from nomus.domain.interfaces.repo_interface import IOrderRepository, IUserRepository
from nomus.domain.interfaces.payment_interface import IPaymentService

log: logging.Logger = logging.getLogger(__name__)

# Заглушка каталога услуг для локальной разработки (stub-режим без remote API)
_STUB_SERVICES: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Классический массаж",
        "description": "Общий классический массаж тела",
        "base_price": "150000.00",
        "duration_minutes": 60,
        "is_active": True,
    },
    {
        "id": 2,
        "name": "Спортивный массаж",
        "description": "Массаж для восстановления после нагрузок",
        "base_price": "200000.00",
        "duration_minutes": 90,
        "is_active": True,
    },
    {
        "id": 3,
        "name": "Расслабляющий массаж",
        "description": "Лёгкий расслабляющий массаж",
        "base_price": "120000.00",
        "duration_minutes": 45,
        "is_active": True,
    },
]


class OrderService:
    def __init__(
        self,
        order_repo: IOrderRepository,
        payment_service: IPaymentService,
        user_repo: Optional[IUserRepository] = None,
        api_client: Optional[Any] = None,
    ):
        self.order_repo: IOrderRepository = order_repo
        self.payment_service: IPaymentService = payment_service
        self.user_repo: Optional[IUserRepository] = user_repo
        self.api_client = api_client  # RemoteApiClient для прямых вызовов API

    async def get_services(self) -> list[dict[str, Any]]:
        """
        Получает список активных услуг.

        В remote-режиме — вызывает GET /services.
        В stub-режиме — возвращает захардкоженный каталог.
        """
        if self.api_client:
            try:
                response = await self.api_client.get("/services")
                services = response.get("services", [])
                return [s for s in services if s.get("is_active", True)]
            except Exception as e:
                log.error("Failed to fetch services from API: %s", e)
                return []
        return list(_STUB_SERVICES)

    async def get_server_user_id(self, telegram_id: int) -> Optional[int]:
        """
        Получает server_user_id пользователя по telegram_id.

        Returns:
            ID пользователя на сервере NMservices или None
        """
        if not self.user_repo:
            return None
        user_data = await self.user_repo.get_user_by_telegram_id(telegram_id)
        if user_data:
            return user_data.get("server_user_id") or user_data.get("id")
        return None

    async def create_order(
        self,
        server_user_id: int,
        service_id: int,
        address_text: str,
    ) -> Optional[dict[str, Any]]:
        """
        Создаёт заказ через API.

        Args:
            server_user_id: ID пользователя на сервере NMservices
            service_id: ID выбранной услуги
            address_text: Текстовый адрес

        Returns:
            Ответ API {"status": "ok", "order_id": ..., "message": ...}
            или None при ошибке
        """
        if self.api_client:
            try:
                response = await self.api_client.post(
                    "/orders",
                    {
                        "user_id": server_user_id,
                        "service_id": service_id,
                        "address_text": address_text,
                    },
                )
                if response.get("status") == "ok":
                    log.info(
                        "Order created: order_id=%s for user=%s",
                        response.get("order_id"),
                        server_user_id,
                    )
                    return response
                log.warning("Unexpected response from /orders: %s", response)
                return None
            except Exception as e:
                log.error("Failed to create order via API: %s", e)
                return None
        else:
            # Stub-режим: симулируем создание заказа
            success = await self.payment_service.process_payment(0)
            if success:
                return {
                    "status": "ok",
                    "order_id": 999,
                    "message": "Stub order created",
                }
            return None

    # ─── Active order ────────────────────────────────────────────────

    async def get_active_order(
        self, telegram_id: int
    ) -> Optional[dict[str, Any]]:
        """
        Получает активный заказ пользователя (pending/confirmed/in_progress).

        Returns:
            Данные заказа или None
        """
        if not self.api_client:
            return None
        try:
            response = await self.api_client.get(
                "/orders/active",
                params={"telegram_id": telegram_id},
            )
            if response.get("has_active_order"):
                return response.get("order")
            return None
        except Exception as e:
            log.error("Failed to fetch active order: %s", e)
            return None

    # ─── Notifications ───────────────────────────────────────────────

    async def get_pending_notifications(
        self, telegram_id: int
    ) -> list[dict[str, Any]]:
        """
        Получает непрочитанные уведомления об изменении статуса заказов.

        Вызывается при каждом взаимодействии пользователя с ботом.
        """
        if not self.api_client:
            return []
        try:
            response = await self.api_client.get(
                "/orders/pending-notifications",
                params={"telegram_id": telegram_id},
            )
            return response.get("notifications", [])
        except Exception as e:
            log.error("Failed to fetch pending notifications: %s", e)
            return []

    async def ack_notifications(
        self, telegram_id: int, order_ids: list[int]
    ) -> None:
        """
        Подтверждает доставку уведомлений (помечает notified_status = status).
        """
        if not self.api_client or not order_ids:
            return
        try:
            await self.api_client.post(
                "/orders/notifications/ack",
                {"telegram_id": telegram_id, "order_ids": order_ids},
            )
        except Exception as e:
            log.error("Failed to ack notifications: %s", e)
