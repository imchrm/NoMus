import uuid
from typing import Dict, Any, Optional
from nomus.domain.interfaces.repo_interface import IOrderRepository, IUserRepository
from nomus.domain.interfaces.payment_interface import IPaymentService


class OrderService:
    _TARIFFS: Dict[str, Dict[str, int]] = {
        "ru": {"Эконом": 10000, "Стандарт": 30000, "Премиум": 50000},
        "en": {"Economy": 10000, "Standard": 30000, "Premium": 50000},
        "uz": {"Iqtisodiyot": 10000, "Standard": 30000, "Premium": 50000},
    }

    # Маппинг локализованных названий тарифов на коды для API
    _TARIFF_CODES: Dict[str, str] = {
        "Эконом": "economy_100",
        "Economy": "economy_100",
        "Iqtisodiyot": "economy_100",
        "Стандарт": "standard_300",
        "Standard": "standard_300",
        "Премиум": "premium_500",
        "Premium": "premium_500",
    }

    _DEFAULT_LANG = "ru"

    def __init__(
        self,
        order_repo: IOrderRepository,
        payment_service: IPaymentService,
        user_repo: Optional[IUserRepository] = None,
    ):
        self.order_repo: IOrderRepository = order_repo
        self.payment_service: IPaymentService = payment_service
        self.user_repo: Optional[IUserRepository] = user_repo

    async def get_tariffs(self, lang: str = _DEFAULT_LANG) -> Dict[str, int]:
        return self._TARIFFS.get(lang, self._TARIFFS[self._DEFAULT_LANG])

    async def create_order(self, user_id: str, tariff: str, amount: int) -> bool:
        """
        Создает заказ с обработкой платежа.

        Args:
            user_id: telegram_id пользователя
            tariff: Название тарифа (локализованное)
            amount: Сумма платежа

        Returns:
            True если заказ успешно создан, False иначе
        """
        payment_success = False

        # Проверяем, поддерживает ли сервис create_order_with_payment (remote-режим)
        if hasattr(self.payment_service, "create_order_with_payment"):
            # Remote режим - получаем server_user_id из БД
            if self.user_repo:
                user_data = await self.user_repo.get_user_by_telegram_id(int(user_id))
                # server_user_id может быть в поле "server_user_id" (локальная регистрация)
                # или в поле "id" (данные загружены с сервера NMservices)
                server_user_id = (
                    user_data.get("server_user_id") or user_data.get("id")
                ) if user_data else None

                if server_user_id:
                    # Получаем код тарифа для API
                    tariff_code = self._TARIFF_CODES.get(tariff, "standard_300")

                    payment_success = (
                        await self.payment_service.create_order_with_payment(
                            user_id=server_user_id,
                            tariff_code=tariff_code,
                            amount=amount,
                        )
                    )
                else:
                    print(
                        f"[OrderService] server_user_id not found for user {user_id}"
                    )
                    return False
            else:
                print("[OrderService] user_repo not available for remote mode")
                return False
        else:
            # Stub режим - старая логика
            payment_success = await self.payment_service.process_payment(amount)

        if payment_success:
            order_id = str(uuid.uuid4())
            order_data: dict[str, Any] = {
                "id": order_id,
                "user": user_id,
                "tariff": tariff,
                "amount": amount,
                "status": "paid",
            }
            await self.order_repo.save_or_update_order(order_id, order_data)
            return True
        return False
