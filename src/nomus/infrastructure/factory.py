"""
Фабрика для создания инфраструктурных сервисов в зависимости от окружения.
Реализует паттерн Factory для инстанцирования конкретных реализаций интерфейсов.
"""

from typing import Any, Optional
from nomus.config.settings import StorageConstants, Settings
from nomus.domain.interfaces.repo_interface import IStorageRepository
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.database.remote_storage import RemoteStorage
from nomus.infrastructure.services.sms_stub import SmsServiceStub
from nomus.infrastructure.services.payment_stub import PaymentServiceStub
from nomus.infrastructure.services.remote_api_client import (
    RemoteApiClient,
    RemoteApiConfig,
)
from nomus.infrastructure.services.sms_remote import SmsServiceRemote
from nomus.infrastructure.services.payment_remote import PaymentServiceRemote


class ServiceFactory:
    """
    Фабрика для создания сервисов инфраструктурного слоя.

    Создает конкретные реализации в зависимости от настроек окружения:
    - Development: использует заглушки (stubs)
    - Development + remote: использует удаленные микросервисы NMservices
    - Staging: использует реальные сервисы в тестовом режиме
    - Production: использует реальные сервисы в боевом режиме
    """

    _api_client: Optional[RemoteApiClient] = None

    @classmethod
    def create_storage(cls, settings: Settings) -> IStorageRepository:
        """
        Создает хранилище данных в зависимости от типа БД в настройках.

        Args:
            settings: Настройки приложения

        Returns:
            Реализация репозитория пользователей и заказов

        Raises:
            ValueError: Если указан неизвестный тип БД
            NotImplementedError: Если реализация для типа БД еще не готова
        """
        if settings.database.type == StorageConstants.DB_MEMORY_TYPE:
            # Проверяем, используется ли remote API для сервисов
            # Если да, то используем RemoteStorage вместо MemoryStorage
            sms_config = settings.services.get("sms")
            payment_config = settings.services.get("payment")

            uses_remote_services = (
                (sms_config and sms_config.type == "remote") or
                (payment_config and payment_config.type == "remote")
            )

            if uses_remote_services and settings.remote_api.enabled:
                # Используем RemoteStorage с локальным кешем
                api_client = cls._get_api_client(settings)
                return RemoteStorage(api_client=api_client)
            else:
                # Обычный MemoryStorage для полностью локальной разработки
                return MemoryStorage()

        elif settings.database.type == StorageConstants.DB_POSTGRES_TYPE:
            #TODO: Реализовать PostgresStorage
            # from nomus.infrastructure.database.postgres_storage import PostgresStorage
            # return PostgresStorage(settings.database)
            raise NotImplementedError(
                "PostgreSQL storage not implemented yet. "
                "Use 'StorageConstants.DB_MEMORY_TYPE' type for development."
            )
        else:
            raise ValueError(f"Unknown database type: {settings.database.type}")

    @classmethod
    def _get_api_client(cls, settings: Settings) -> RemoteApiClient:
        """
        Получает или создает общий HTTP-клиент для удаленных сервисов.

        Args:
            settings: Настройки приложения

        Returns:
            Экземпляр RemoteApiClient
        """
        if cls._api_client is None:
            config = RemoteApiConfig(
                base_url=settings.remote_api.base_url,
                api_key=settings.remote_api.api_key,
                timeout=settings.remote_api.timeout,
                max_retries=settings.remote_api.max_retries,
                retry_delay=settings.remote_api.retry_delay,
            )
            cls._api_client = RemoteApiClient(config)
        return cls._api_client

    @classmethod
    def create_sms_service(cls, settings: Settings) -> Any:
        """
        Создает SMS сервис в зависимости от настроек окружения.

        Args:
            settings: Настройки приложения

        Returns:
            Реализация SMS сервиса (заглушка, удаленная или реальная)

        Raises:
            ValueError: Если указан неизвестный тип сервиса
            NotImplementedError: Если реализация еще не готова
        """
        sms_config = settings.services.get("sms")

        if not sms_config or sms_config.type == "stub":
            return SmsServiceStub()
        elif sms_config.type == "remote":
            # Используем удаленный API NMservices
            api_client = cls._get_api_client(settings)
            return SmsServiceRemote(api_client=api_client)
        elif sms_config.type == "real":
            #TODO: Реализовать реальный SMS сервис
            # from nomus.infrastructure.services.sms_real import SmsServiceReal
            # return SmsServiceReal(sms_config)
            raise NotImplementedError(
                f"Real SMS service not implemented yet. "
                f"Provider: {sms_config.provider}, Test mode: {sms_config.test_mode}"
            )
        else:
            raise ValueError(f"Unknown SMS service type: {sms_config.type}")

    @classmethod
    def create_payment_service(cls, settings: Settings) -> Any:
        """
        Создает платежный сервис в зависимости от настроек окружения.

        Args:
            settings: Настройки приложения

        Returns:
            Реализация платежного сервиса (заглушка, удаленная или реальная)

        Raises:
            ValueError: Если указан неизвестный тип сервиса
            NotImplementedError: Если реализация еще не готова
        """
        payment_config = settings.services.get("payment")

        if not payment_config or payment_config.type == "stub":
            return PaymentServiceStub()
        elif payment_config.type == "remote":
            # Используем удаленный API NMservices
            api_client = cls._get_api_client(settings)
            return PaymentServiceRemote(api_client=api_client)
        elif payment_config.type == "real":
            #TODO: Реализовать реальный платежный сервис
            # from nomus.infrastructure.services.payment_real import PaymentServiceReal
            # return PaymentServiceReal(payment_config)
            raise NotImplementedError(
                f"Real payment service not implemented yet. "
                f"Provider: {payment_config.provider}, Test mode: {payment_config.test_mode}"
            )
        else:
            raise ValueError(f"Unknown payment service type: {payment_config.type}")

    @classmethod
    def create_all_services(cls, settings: Settings) -> dict:
        """
        Создает все необходимые сервисы для приложения.

        Args:
            settings: Настройки приложения

        Returns:
            Словарь со всеми созданными сервисами:
            - storage: Хранилище данных
            - sms_service: SMS сервис
            - payment_service: Платежный сервис
            - api_client: HTTP-клиент для удаленного API (если используется)
        """
        return {
            "storage": cls.create_storage(settings),
            "sms_service": cls.create_sms_service(settings),
            "payment_service": cls.create_payment_service(settings),
            "api_client": cls._api_client,
        }

    @classmethod
    async def close_api_client(cls) -> None:
        """
        Закрывает HTTP-клиент для удаленного API.

        Должен вызываться при завершении работы приложения.
        """
        if cls._api_client is not None:
            await cls._api_client.close()
            cls._api_client = None
