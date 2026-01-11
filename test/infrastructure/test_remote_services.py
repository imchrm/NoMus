"""
Тесты для удаленных сервисов NMservices.

Конфигурация:
    Настройте переменные окружения в .env:
        TEST_REMOTE_API_IP=your_server_ip
        TEST_REMOTE_API_PORT=your_server_port
        TEST_REMOTE_API_PASSWORD=your_api_password

Для запуска тестов с реальным сервером:
    pytest test/infrastructure/test_remote_services.py -v

Для запуска без реального сервера (только unit-тесты):
    pytest test/infrastructure/test_remote_services.py -v -m "not integration"

Для быстрой проверки без pytest:
    poetry run python test/infrastructure/test_remote_services.py

Переопределение через аргументы командной строки:
    poetry run python test/infrastructure/test_remote_services.py --ip 192.168.1.100 --port 8080 --password mypass
"""

import asyncio
import argparse

# pytest опционален для прямого запуска скрипта
try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Заглушки для декораторов pytest при прямом запуске
    class _MockMark:
        @staticmethod
        def integration(f):
            return f

        @staticmethod
        def asyncio(f):
            return f

    class _MockPytest:
        mark = _MockMark()

        @staticmethod
        def raises(exc):
            from contextlib import contextmanager

            @contextmanager
            def _raises():
                try:
                    yield
                except exc:
                    pass
                else:
                    raise AssertionError(f"Expected {exc.__name__}")

            return _raises()

    pytest = _MockPytest  # type: ignore


import os

from nomus.infrastructure.services.remote_api_client import (
    RemoteApiClient,
    RemoteApiConfig,
    RemoteApiAuthError,
)
from nomus.infrastructure.services.sms_remote import SmsServiceRemote
from nomus.infrastructure.services.payment_remote import PaymentServiceRemote


# Парсинг аргументов для возможности переопределения настроек
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "--ip",
    default=os.getenv("TEST_REMOTE_API_IP", "localhost"),
    help="IP address of the test server",
)
parser.add_argument(
    "--port",
    default=os.getenv("TEST_REMOTE_API_PORT", "9800"),
    help="Port of the test server",
)
parser.add_argument(
    "--password",
    default=os.getenv("TEST_REMOTE_API_PASSWORD", ""),
    help="API password for the test server",
)

args, _ = parser.parse_known_args()

# Конфигурация для тестов
TEST_CONFIG = RemoteApiConfig(
    base_url=f"http://{args.ip}:{args.port}",
    api_key=args.password,
    timeout=10.0,
    max_retries=2,
    retry_delay=0.5,
)

INVALID_CONFIG = RemoteApiConfig(
    base_url=f"http://{args.ip}:{args.port}",
    api_key="wrong_key",
    timeout=5.0,
)


class TestRemoteApiClient:
    """Тесты для RemoteApiClient"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Тест проверки доступности API"""
        async with RemoteApiClient(TEST_CONFIG) as client:
            result = await client.health_check()
            assert result is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_root_endpoint(self):
        """Тест GET-запроса к корневому эндпоинту"""
        async with RemoteApiClient(TEST_CONFIG) as client:
            response = await client.get("/")
            assert response["message"] == "NoMus API is running"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_auth_failure_with_wrong_key(self):
        """Тест ошибки аутентификации с неверным ключом"""
        async with RemoteApiClient(INVALID_CONFIG) as client:
            with pytest.raises(RemoteApiAuthError):
                await client.post(
                    "/users/register",
                    data={"phone_number": "+998901234567"},
                )


class TestSmsServiceRemote:
    """Тесты для SmsServiceRemote"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_send_sms_success(self):
        """Тест успешной отправки SMS (регистрации)"""
        service = SmsServiceRemote(config=TEST_CONFIG)
        try:
            result = await service.send_sms("+998901234567", "1234")
            assert result is True
            assert service.last_user_id is not None
            assert isinstance(service.last_user_id, int)
        finally:
            await service.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_send_sms_auth_failure(self):
        """Тест ошибки аутентификации при отправке SMS"""
        service = SmsServiceRemote(config=INVALID_CONFIG)
        try:
            result = await service.send_sms("+998901234567", "1234")
            assert result is False
            assert service.last_user_id is None
        finally:
            await service.close()


class TestPaymentServiceRemote:
    """Тесты для PaymentServiceRemote"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_order_success(self):
        """Тест успешного создания заказа"""
        service = PaymentServiceRemote(config=TEST_CONFIG)
        try:
            result = await service.create_order_with_payment(
                user_id=101,
                tariff_code="standard_300",
                amount=30000,
            )
            assert result is True
            assert service.last_order_id is not None
            assert isinstance(service.last_order_id, int)
        finally:
            await service.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_payment_after_order(self):
        """Тест process_payment после создания заказа"""
        service = PaymentServiceRemote(config=TEST_CONFIG)
        try:
            # Сначала создаем заказ
            await service.create_order_with_payment(
                user_id=102,
                tariff_code="premium_500",
            )

            # Теперь process_payment должен вернуть True
            result = await service.process_payment(50000, "UZS")
            assert result is True
        finally:
            await service.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_payment_without_order(self):
        """Тест process_payment без предварительного заказа"""
        service = PaymentServiceRemote(config=TEST_CONFIG)
        try:
            # Без создания заказа process_payment вернет False
            result = await service.process_payment(30000, "UZS")
            assert result is False
        finally:
            await service.close()


class TestIntegrationFlow:
    """Интеграционные тесты полного флоу"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_registration_and_order_flow(self):
        """Тест полного цикла: регистрация -> создание заказа"""
        # Создаем общий клиент
        client = RemoteApiClient(TEST_CONFIG)

        try:
            # 1. Регистрация пользователя
            sms_service = SmsServiceRemote(api_client=client)
            reg_result = await sms_service.send_sms("+998909876543", "1234")
            assert reg_result is True
            user_id = sms_service.last_user_id
            assert user_id is not None

            # 2. Создание заказа
            payment_service = PaymentServiceRemote(api_client=client)
            order_result = await payment_service.create_order_with_payment(
                user_id=user_id,
                tariff_code="economy_100",
            )
            assert order_result is True
            assert payment_service.last_order_id is not None

            print("\n[OK] Full flow completed:")
            print(f"   User ID: {user_id}")
            print(f"   Order ID: {payment_service.last_order_id}")

        finally:
            await client.close()


# Запуск тестов напрямую
if __name__ == "__main__":
    print("Running remote services tests...")
    print("=" * 50)

    async def run_quick_test():
        """Быстрый тест для проверки подключения"""
        print("\n1. Testing API connection...")
        async with RemoteApiClient(TEST_CONFIG) as client:
            if await client.health_check():
                print("   [OK] API is accessible")
            else:
                print("   [FAIL] API is not accessible")
                return

        print("\n2. Testing SMS service (registration)...")
        sms = SmsServiceRemote(config=TEST_CONFIG)
        try:
            if await sms.send_sms("+998900001111", "1234"):
                print(f"   [OK] Registration successful, user_id: {sms.last_user_id}")
            else:
                print("   [FAIL] Registration failed")
        finally:
            await sms.close()

        print("\n3. Testing Payment service (order creation)...")
        payment = PaymentServiceRemote(config=TEST_CONFIG)
        try:
            if await payment.create_order_with_payment(101, "standard_300"):
                print(f"   [OK] Order created, order_id: {payment.last_order_id}")
            else:
                print("   [FAIL] Order creation failed")
        finally:
            await payment.close()

        print("\n" + "=" * 50)
        print("All quick tests completed!")

    asyncio.run(run_quick_test())
