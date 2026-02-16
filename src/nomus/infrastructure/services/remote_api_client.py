"""
HTTP-клиент для взаимодействия с удаленными микросервисами NMservices.
Реализует базовую функциональность для HTTP-запросов с аутентификацией.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional
import httpx


@dataclass
class RemoteApiConfig:
    """Конфигурация для подключения к удаленному API."""

    base_url: str
    api_key: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


class RemoteApiError(Exception):
    """Базовое исключение для ошибок удаленного API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class RemoteApiAuthError(RemoteApiError):
    """Ошибка аутентификации (403)."""

    pass


class RemoteApiValidationError(RemoteApiError):
    """Ошибка валидации данных (422)."""

    pass


class RemoteApiConnectionError(RemoteApiError):
    """Ошибка соединения с сервером."""

    pass


class RemoteApiClient:
    """
    Асинхронный HTTP-клиент для взаимодействия с NMservices API.

    Поддерживает:
    - Аутентификацию через X-API-Key header
    - Автоматические retry при сетевых ошибках
    - Таймауты запросов
    - Обработку ошибок API
    """

    def __init__(self, config: RemoteApiConfig):
        """
        Инициализация клиента.

        Args:
            config: Конфигурация подключения к API
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def _headers(self) -> Dict[str, str]:
        """Заголовки для запросов с аутентификацией."""
        return {
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Получает или создает HTTP-клиент."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=self._headers,
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Закрывает HTTP-клиент."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Обрабатывает ответ от API.

        Args:
            response: HTTP-ответ

        Returns:
            Распарсенный JSON-ответ

        Raises:
            RemoteApiAuthError: При ошибке аутентификации (403)
            RemoteApiValidationError: При ошибке валидации (422)
            RemoteApiError: При других ошибках API
        """
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        if response.status_code == 403:
            raise RemoteApiAuthError(
                message="Authentication failed: invalid API key",
                status_code=403,
                response_body=body,
            )

        if response.status_code == 422:
            raise RemoteApiValidationError(
                message=f"Validation error: {body}",
                status_code=422,
                response_body=body,
            )

        if response.status_code >= 400:
            raise RemoteApiError(
                message=f"API error: {response.status_code}",
                status_code=response.status_code,
                response_body=body,
            )

        return body

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Выполняет HTTP-запрос с автоматическими retry.

        Args:
            method: HTTP-метод (GET, POST, etc.)
            endpoint: Путь эндпоинта (например, "/users/register")
            json_data: Данные для отправки в теле запроса

        Returns:
            Распарсенный JSON-ответ

        Raises:
            RemoteApiConnectionError: При невозможности установить соединение
            RemoteApiError: При ошибках API
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                client = await self._get_client()
                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=json_data,
                    params=params,
                )
                return await self._handle_response(response)

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    print(
                        f"[RemoteAPI] Connection failed, retrying "
                        f"({attempt + 1}/{self.config.max_retries})..."
                    )
                    await asyncio.sleep(self.config.retry_delay)
                continue

            except RemoteApiError:
                # Не retry для ошибок API (403, 422, etc.)
                raise

        raise RemoteApiConnectionError(
            message=f"Failed to connect after {self.config.max_retries} attempts: {last_exception}",
        )

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """GET-запрос к API."""
        return await self._request_with_retry("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """POST-запрос к API."""
        return await self._request_with_retry("POST", endpoint, json_data=data)

    async def patch(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """PATCH-запрос к API."""
        return await self._request_with_retry("PATCH", endpoint, json_data=data)

    async def health_check(self) -> bool:
        """
        Проверяет доступность API.

        Returns:
            True если API доступен, False иначе
        """
        try:
            response = await self.get("/")
            return response.get("message") == "NoMus API is running"
        except Exception as e:
            print(f"[RemoteAPI] Health check failed: {e}")
            return False

    async def __aenter__(self) -> "RemoteApiClient":
        """Поддержка async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрытие клиента при выходе из контекста."""
        await self.close()
