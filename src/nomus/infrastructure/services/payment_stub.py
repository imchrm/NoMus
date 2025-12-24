import asyncio
from typing import Optional


class PaymentServiceStub:
    """
    Заглушка платежного сервиса для локальной разработки.
    Симулирует обработку платежей без реального взаимодействия с платежным провайдером.
    """

    def __init__(self):
        self._last_order_id: Optional[int] = None

    async def process_payment(self, amount: int, currency: str = "UZS") -> bool:
        print(f"[Payment-Stub] Processing payment of {amount} {currency}...")
        await asyncio.sleep(1)  # Simulate bank processing delay as per requirements
        print(f"[Payment-Stub] Payment successful.")
        return True

    async def create_order_with_payment(
        self,
        user_id: int,
        tariff_code: str,
        amount: int = 30000,
    ) -> bool:
        """
        Создает заказ с обработкой платежа (stub-режим).

        В stub-режиме просто симулирует создание заказа без реального взаимодействия с API.
        """
        print(
            f"[Payment-Stub] Creating order for user {user_id}, "
            f"tariff: {tariff_code}, amount: {amount}..."
        )
        # Симулируем обработку платежа
        result = await self.process_payment(amount)
        if result:
            print(f"[Payment-Stub] Order created successfully (stub mode).")
        return result

    @property
    def last_order_id(self) -> Optional[int]:
        """Возвращает None для stub-режима (нет интеграции с сервером)."""
        return self._last_order_id
