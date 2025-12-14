import uuid
from typing import Dict, Any
from nomus.domain.interfaces.repo_interface import IOrderRepository
from nomus.infrastructure.services.payment_stub import PaymentServiceStub


class OrderService:
    _TARIFFS: Dict[str, Dict[str, int]] = {
        "ru": {"Эконом": 10000, "Стандарт": 30000, "Премиум": 50000},
        "en": {"Economy": 10000, "Standard": 30000, "Premium": 50000},
        "uz": {"Iqtisodiyot": 10000, "Standard": 30000, "Premium": 50000},
    }
    _DEFAULT_LANG = "ru"

    def __init__(
        self, order_repo: IOrderRepository, payment_service: PaymentServiceStub
    ):
        self.order_repo: IOrderRepository = order_repo
        self.payment_service: PaymentServiceStub = payment_service

    async def get_tariffs(self, lang: str = _DEFAULT_LANG) -> Dict[str, int]:
        return self._TARIFFS.get(lang, self._TARIFFS[self._DEFAULT_LANG])

    async def create_order(self, user_id: str, tariff: str, amount: int) -> bool:
        # Process payment first
        payment_success: bool = await self.payment_service.process_payment(amount)

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
