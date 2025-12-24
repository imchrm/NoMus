"""
Тест для проверки сохранения server_user_id при регистрации.

Этот скрипт симулирует процесс регистрации и проверяет:
1. Вызов AuthService.register_user()
2. Получение server_user_id от SmsServiceRemote
3. Сохранение server_user_id в User модели
"""

import asyncio
from datetime import datetime

# Импортируем необходимые компоненты
from nomus.domain.entities.user import User
from nomus.application.services.auth_service import AuthService
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.services.sms_stub import SmsServiceStub
from nomus.infrastructure.services.sms_remote import SmsServiceRemote
from nomus.infrastructure.services.remote_api_client import (
    RemoteApiClient,
    RemoteApiConfig,
)


async def test_registration_with_stub():
    """Тест регистрации в stub-режиме (локальная разработка)."""
    print("\n" + "=" * 60)
    print("ТЕСТ 1: Регистрация в STUB-режиме")
    print("=" * 60)

    # Настройка
    storage = MemoryStorage()
    sms_service = SmsServiceStub()
    auth_service = AuthService(user_repo=storage, sms_service=sms_service)

    # Симуляция данных пользователя
    telegram_id = 123456789
    phone = "+998901234567"
    latitude = 41.2995
    longitude = 69.2401

    # 1. Вызов register_user
    print(f"\n1. Вызываем auth_service.register_user('{phone}')...")
    server_user_id = await auth_service.register_user(phone)
    print(f"   Получен server_user_id: {server_user_id}")

    # 2. Создание пользователя
    print(f"\n2. Создаем User модель с server_user_id={server_user_id}...")
    user_data = User(
        id=telegram_id,
        telegram_id=telegram_id,
        phone_number=phone,
        registered_at=datetime.now(),
        latitude=latitude,
        longitude=longitude,
        server_user_id=server_user_id,
    ).model_dump()

    # 3. Сохранение в хранилище
    print(f"\n3. Сохраняем пользователя в storage...")
    await storage.save_or_update_user(telegram_id, user_data)

    # 4. Проверка сохранения
    print(f"\n4. Проверяем сохраненные данные...")
    saved_user = await storage.get_user_by_telegram_id(telegram_id)

    print(f"\n   Сохраненные данные пользователя:")
    print(f"   - telegram_id: {saved_user.get('telegram_id')}")
    print(f"   - phone_number: {saved_user.get('phone_number')}")
    print(f"   - server_user_id: {saved_user.get('server_user_id')}")
    print(f"   - latitude: {saved_user.get('latitude')}")
    print(f"   - longitude: {saved_user.get('longitude')}")

    # Проверки
    assert saved_user is not None, "Пользователь должен быть сохранен"
    assert saved_user.get("phone_number") == phone, "Номер телефона должен совпадать"
    assert (
        saved_user.get("server_user_id") == server_user_id
    ), "server_user_id должен быть сохранен"

    print(f"\n✅ STUB-режим: server_user_id = {server_user_id} (None - норма для stub)")
    print("=" * 60)


async def test_registration_with_remote():
    """Тест регистрации в remote-режиме (подключение к NMservices)."""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Регистрация в REMOTE-режиме")
    print("=" * 60)

    # Настройка
    config = RemoteApiConfig(
        base_url="http://94.158.50.119:9800",
        api_key="troxivasine23",
        timeout=10.0,
        max_retries=2,
    )

    storage = MemoryStorage()
    api_client = RemoteApiClient(config)
    sms_service = SmsServiceRemote(api_client=api_client)
    auth_service = AuthService(user_repo=storage, sms_service=sms_service)

    # Симуляция данных пользователя
    telegram_id = 987654321
    phone = "+998909999999"
    latitude = 41.2995
    longitude = 69.2401

    try:
        # 1. Вызов register_user
        print(f"\n1. Вызываем auth_service.register_user('{phone}')...")
        server_user_id = await auth_service.register_user(phone)
        print(f"   Получен server_user_id: {server_user_id}")

        # 2. Создание пользователя
        print(f"\n2. Создаем User модель с server_user_id={server_user_id}...")
        user_data = User(
            id=telegram_id,
            telegram_id=telegram_id,
            phone_number=phone,
            registered_at=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            server_user_id=server_user_id,
        ).model_dump()

        # 3. Сохранение в хранилище
        print(f"\n3. Сохраняем пользователя в storage...")
        await storage.save_or_update_user(telegram_id, user_data)

        # 4. Проверка сохранения
        print(f"\n4. Проверяем сохраненные данные...")
        saved_user = await storage.get_user_by_telegram_id(telegram_id)

        print(f"\n   Сохраненные данные пользователя:")
        print(f"   - telegram_id: {saved_user.get('telegram_id')}")
        print(f"   - phone_number: {saved_user.get('phone_number')}")
        print(f"   - server_user_id: {saved_user.get('server_user_id')}")
        print(f"   - latitude: {saved_user.get('latitude')}")
        print(f"   - longitude: {saved_user.get('longitude')}")

        # Проверки
        assert saved_user is not None, "Пользователь должен быть сохранен"
        assert (
            saved_user.get("phone_number") == phone
        ), "Номер телефона должен совпадать"
        assert (
            saved_user.get("server_user_id") is not None
        ), "server_user_id НЕ должен быть None в remote-режиме"
        assert isinstance(
            saved_user.get("server_user_id"), int
        ), "server_user_id должен быть integer"

        print(
            f"\n✅ REMOTE-режим: server_user_id = {server_user_id} (реальный ID с сервера)"
        )
        print("=" * 60)

    finally:
        await api_client.close()


async def test_full_flow_comparison():
    """Сравнение поведения stub vs remote режимов."""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Сравнение STUB vs REMOTE")
    print("=" * 60)

    # Stub режим
    print("\n[STUB] Создание SMS сервиса...")
    stub_sms = SmsServiceStub()
    await stub_sms.send_sms("+998901111111", "1234")
    stub_user_id = stub_sms.last_user_id
    print(f"[STUB] last_user_id = {stub_user_id}")

    # Remote режим
    print("\n[REMOTE] Создание SMS сервиса...")
    config = RemoteApiConfig(
        base_url="http://94.158.50.119:9800",
        api_key="troxivasine23",
        timeout=10.0,
    )
    remote_sms = SmsServiceRemote(config=config)

    try:
        await remote_sms.send_sms("+998902222222", "1234")
        remote_user_id = remote_sms.last_user_id
        print(f"[REMOTE] last_user_id = {remote_user_id}")

        # Сравнение
        print("\n" + "-" * 60)
        print("РЕЗУЛЬТАТЫ СРАВНЕНИЯ:")
        print(f"  STUB mode:   last_user_id = {stub_user_id} (None)")
        print(f"  REMOTE mode: last_user_id = {remote_user_id} (integer > 0)")
        print("-" * 60)

        assert stub_user_id is None, "Stub должен возвращать None"
        assert remote_user_id is not None, "Remote должен возвращать integer"
        assert isinstance(remote_user_id, int), "Remote user_id должен быть int"

        print("\n✅ Различия между режимами подтверждены!")
        print("=" * 60)

    finally:
        await remote_sms.close()


async def main():
    """Запуск всех тестов."""
    print("\n" + "=" * 60)
    print("  ТЕСТИРОВАНИЕ СОХРАНЕНИЯ server_user_id ПРИ РЕГИСТРАЦИИ")
    print("=" * 60)

    try:
        # Тест 1: Stub режим
        await test_registration_with_stub()

        # Тест 2: Remote режим
        await test_registration_with_remote()

        # Тест 3: Сравнение
        await test_full_flow_comparison()

        print("\n" + "=" * 60)
        print("  ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        print("\nВЫВОД:")
        print("- В STUB-режиме: server_user_id = None (локальная разработка)")
        print("- В REMOTE-режиме: server_user_id = integer (ID с NMservices)")
        print("- Оба значения корректно сохраняются в User модели")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
