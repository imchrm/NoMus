"""
Удаленный платежный сервис, работающий через NMservices API.
Вызывает эндпоинт /orders для создания заказа и обработки платежа.
"""

from typing import Optional
from .remote_api_client import (
    RemoteApiClient,
    RemoteApiConfig,
    RemoteApiError,
    RemoteApiAuthError,
    RemoteApiValidationError,
)


class PaymentServiceRemote:
    """
    Платежный сервис, работающий через удаленный API NMservices.

    Создает заказы через вызов эндпоинта /orders на удаленном сервере.
    В реальном сценарии сервер NMservices обрабатывает платеж
    через внешний провайдер (Payme, Click, etc.).
    """

    def __init__(
        self,
        api_client: Optional[RemoteApiClient] = None,
        config: Optional[RemoteApiConfig] = None,
    ):
        """
        Инициализация сервиса.

        Args:
            api_client: Готовый клиент API (для sharing между сервисами)
            config: Конфигурация для создания нового клиента
        """
        if api_client:
            self._client = api_client
            self._owns_client = False
        elif config:
            self._client = RemoteApiClient(config)
            self._owns_client = True
        else:
            raise ValueError("Either api_client or config must be provided")

        self._last_order_id: Optional[int] = None

    @property
    def last_order_id(self) -> Optional[int]:
        """Возвращает ID последнего созданного заказа."""
        return self._last_order_id

    async def process_payment(self, amount: int, currency: str = "UZS") -> bool:
        """
        Обрабатывает платеж через удаленный API.

        Этот метод сохраняет совместимость с интерфейсом PaymentServiceStub,
        но для полноценной работы требует предварительного вызова
        create_order_with_payment(), который передает все необходимые данные.

        Args:
            amount: Сумма платежа
            currency: Валюта (по умолчанию UZS)

        Returns:
            True если последний заказ был успешно создан

        Note:
            В текущей реализации этот метод только проверяет,
            был ли успешно создан заказ ранее.
            Для создания заказа используйте create_order_with_payment().
        """
        print(f"[Payment-Remote] Processing payment of {amount} {currency}...")

        # Возвращаем True если последний заказ был успешно создан
        if self._last_order_id:
            print(f"[Payment-Remote] Payment confirmed for order {self._last_order_id}")
            return True

        print("[Payment-Remote] No order created yet. Use create_order_with_payment()")
        return False

    async def create_order_with_payment(
        self,
        user_id: int,
        tariff_code: str,
        amount: int = 30000,
    ) -> bool:
        """
        Создает заказ с обработкой платежа через удаленный API.

        Вызывает эндпоинт /orders на NMservices.
        На данном этапе (PoC) сервер симулирует обработку платежа
        и возвращает order_id.

        Args:
            user_id: ID пользователя (полученный при регистрации)
            tariff_code: Код тарифа (например, "standard_300")
            amount: Сумма платежа (не используется в текущей реализации API)

        Returns:
            True если заказ успешно создан, False при ошибках

        Note:
            При успешном создании сохраняет order_id в last_order_id.
        """
        print(
            f"[Payment-Remote] Creating order for user {user_id}, "
            f"tariff: {tariff_code}, amount: {amount}..."
        )

        try:
            response = await self._client.post(
                "/orders",
                data={
                    "user_id": user_id,
                    "tariff_code": tariff_code,
                },
            )

            if response.get("status") == "ok":
                self._last_order_id = response.get("order_id")
                print(
                    f"[Payment-Remote] Order created successfully. "
                    f"Order ID: {self._last_order_id}"
                )
                return True

            print(f"[Payment-Remote] Unexpected response: {response}")
            return False

        except RemoteApiAuthError as e:
            print(f"[Payment-Remote] Authentication failed: {e}")
            return False

        except RemoteApiValidationError as e:
            print(f"[Payment-Remote] Validation error: {e}")
            return False

        except RemoteApiError as e:
            print(f"[Payment-Remote] API error: {e}")
            return False

        except Exception as e:
            print(f"[Payment-Remote] Unexpected error: {e}")
            return False

    async def close(self) -> None:
        """Закрывает клиент, если он принадлежит этому сервису."""
        if self._owns_client:
            await self._client.close()
