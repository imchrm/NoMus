"""
Удаленный SMS-сервис, работающий через NMservices API.
Вызывает эндпоинт /users/register для регистрации пользователя и отправки SMS.
"""

from typing import Optional
from .remote_api_client import (
    RemoteApiClient,
    RemoteApiConfig,
    RemoteApiError,
    RemoteApiAuthError,
    RemoteApiValidationError,
)


class SmsServiceRemote:
    """
    SMS-сервис, работающий через удаленный API NMservices.

    Эмулирует отправку SMS-кода через вызов эндпоинта регистрации
    на удаленном сервере. В реальном сценарии сервер NMservices
    отправляет SMS через внешний провайдер (Eskiz, Playmobile, etc.).
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

        self._last_user_id: Optional[int] = None

    @property
    def last_user_id(self) -> Optional[int]:
        """Возвращает ID последнего зарегистрированного пользователя."""
        return self._last_user_id

    async def send_sms(self, phone: str, code: str) -> bool:
        """
        Отправляет SMS с кодом верификации через удаленный API.

        Вызывает эндпоинт /users/register на NMservices.
        На данном этапе (PoC) сервер не отправляет реальные SMS,
        но возвращает user_id для дальнейшей работы.

        Args:
            phone: Номер телефона пользователя (например, "+998901234567")
            code: Код верификации (не используется в текущей реализации API)

        Returns:
            True если запрос успешен, False при ошибках

        Note:
            При успешном запросе сохраняет user_id в last_user_id
            для последующего использования при создании заказа.
        """
        print(f"[SMS-Remote] Sending code {code} to {phone}...")

        try:
            response = await self._client.post(
                "/users/register",
                data={"phone_number": phone},
            )

            if response.get("status") == "ok":
                self._last_user_id = response.get("user_id")
                print(
                    f"[SMS-Remote] Registration successful. "
                    f"User ID: {self._last_user_id}"
                )
                return True

            print(f"[SMS-Remote] Unexpected response: {response}")
            return False

        except RemoteApiAuthError as e:
            print(f"[SMS-Remote] Authentication failed: {e}")
            return False

        except RemoteApiValidationError as e:
            print(f"[SMS-Remote] Validation error: {e}")
            return False

        except RemoteApiError as e:
            print(f"[SMS-Remote] API error: {e}")
            return False

        except Exception as e:
            print(f"[SMS-Remote] Unexpected error: {e}")
            return False

    async def close(self) -> None:
        """Закрывает клиент, если он принадлежит этому сервису."""
        if self._owns_client:
            await self._client.close()
