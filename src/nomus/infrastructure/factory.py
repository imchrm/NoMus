"""
Фабрика для создания инфраструктурных сервисов в зависимости от окружения.
Реализует паттерн Factory для инстанцирования конкретных реализаций интерфейсов.
"""

from typing import Any
from nomus.config.settings import Settings
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.services.sms_stub import SmsServiceStub
from nomus.infrastructure.services.payment_stub import PaymentServiceStub


class ServiceFactory:
    """
    Фабрика для создания сервисов инфраструктурного слоя.

    Создает конкретные реализации в зависимости от настроек окружения:
    - Development: использует заглушки (stubs)
    - Staging: использует реальные сервисы в тестовом режиме
    - Production: использует реальные сервисы в боевом режиме
    """

    @staticmethod
    def create_storage(settings: Settings) -> Any:
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
        if settings.database.type == "memory":
            return MemoryStorage()
        elif settings.database.type == "postgres":
            # TODO: Реализовать PostgresStorage
            # from nomus.infrastructure.database.postgres_storage import PostgresStorage
            # return PostgresStorage(settings.database)
            raise NotImplementedError(
                "PostgreSQL storage not implemented yet. "
                "Use 'memory' type for development."
            )
        else:
            raise ValueError(f"Unknown database type: {settings.database.type}")

    @staticmethod
    def create_sms_service(settings: Settings) -> Any:
        """
        Создает SMS сервис в зависимости от настроек окружения.

        Args:
            settings: Настройки приложения

        Returns:
            Реализация SMS сервиса (заглушка или реальная)

        Raises:
            ValueError: Если указан неизвестный тип сервиса
            NotImplementedError: Если реализация еще не готова
        """
        sms_config = settings.services.get("sms")

        if not sms_config or sms_config.type == "stub":
            return SmsServiceStub()
        elif sms_config.type == "real":
            # TODO: Реализовать реальный SMS сервис
            # from nomus.infrastructure.services.sms_real import SmsServiceReal
            # return SmsServiceReal(sms_config)
            raise NotImplementedError(
                f"Real SMS service not implemented yet. "
                f"Provider: {sms_config.provider}, Test mode: {sms_config.test_mode}"
            )
        else:
            raise ValueError(f"Unknown SMS service type: {sms_config.type}")

    @staticmethod
    def create_payment_service(settings: Settings) -> Any:
        """
        Создает платежный сервис в зависимости от настроек окружения.

        Args:
            settings: Настройки приложения

        Returns:
            Реализация платежного сервиса (заглушка или реальная)

        Raises:
            ValueError: Если указан неизвестный тип сервиса
            NotImplementedError: Если реализация еще не готова
        """
        payment_config = settings.services.get("payment")

        if not payment_config or payment_config.type == "stub":
            return PaymentServiceStub()
        elif payment_config.type == "real":
            # TODO: Реализовать реальный платежный сервис
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
        """
        return {
            "storage": cls.create_storage(settings),
            "sms_service": cls.create_sms_service(settings),
            "payment_service": cls.create_payment_service(settings),
        }
