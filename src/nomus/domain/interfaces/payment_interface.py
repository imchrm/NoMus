"""
Интерфейс для платежного сервиса.
Определяет контракт для всех реализаций платежных сервисов (stub, remote, real).
"""

from typing import Protocol, Optional


class IPaymentService(Protocol):
    """
    Интерфейс для платежного сервиса.

    Используется для абстракции от конкретной реализации:
    - PaymentServiceStub - заглушка для разработки
    - PaymentServiceRemote - удаленный API NMservices
    - PaymentServiceReal - реальный платежный провайдер (будущая реализация)
    """

    async def process_payment(self, amount: int, currency: str = "UZS") -> bool:
        """
        Обрабатывает платеж (совместимость с stub-режимом).

        Args:
            amount: Сумма платежа
            currency: Валюта платежа (по умолчанию UZS)

        Returns:
            True если платеж успешно обработан, False иначе
        """
        ...

    async def create_order_with_payment(
        self,
        user_id: int,
        tariff_code: str,
        amount: int = 30000,
    ) -> bool:
        """
        Создает заказ с обработкой платежа (для remote-режима).

        Args:
            user_id: ID пользователя на сервере NMservices
            tariff_code: Код тарифа (например, "standard_300")
            amount: Сумма платежа (по умолчанию 30000 UZS)

        Returns:
            True если заказ успешно создан, False иначе
        """
        ...

    @property
    def last_order_id(self) -> Optional[int]:
        """
        Возвращает ID последнего созданного заказа (для remote-режима).

        Returns:
            ID заказа или None для stub-режима
        """
        ...
