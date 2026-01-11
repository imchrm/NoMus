"""
Test to verify server_user_id is saved during registration.

This script simulates the registration process and verifies:
1. AuthService.register_user() is called
2. server_user_id is received from SmsServiceRemote
3. server_user_id is saved in the User model
"""

import asyncio
import os
from datetime import datetime

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
    """Test registration in stub mode (local development)."""
    print("\n" + "=" * 60)
    print("TEST 1: Registration in STUB mode")
    print("=" * 60)

    storage = MemoryStorage()
    sms_service = SmsServiceStub()
    auth_service = AuthService(user_repo=storage, sms_service=sms_service)

    telegram_id = 123456789
    phone = "+998901234567"
    latitude = 41.2995
    longitude = 69.2401

    print(f"\n1. Calling auth_service.register_user('{phone}')...")
    server_user_id = await auth_service.register_user(phone)
    print(f"   Received server_user_id: {server_user_id}")

    print(f"\n2. Creating User model with server_user_id={server_user_id}...")
    user_data = User(
        id=telegram_id,
        telegram_id=telegram_id,
        phone_number=phone,
        registered_at=datetime.now(),
        latitude=latitude,
        longitude=longitude,
        server_user_id=server_user_id,
    ).model_dump()

    print(f"\n3. Saving user to storage...")
    await storage.save_or_update_user(telegram_id, user_data)

    print(f"\n4. Verifying saved data...")
    saved_user = await storage.get_user_by_telegram_id(telegram_id)

    print(f"\n   Saved user data:")
    print(f"   - telegram_id: {saved_user.get('telegram_id')}")
    print(f"   - phone_number: {saved_user.get('phone_number')}")
    print(f"   - server_user_id: {saved_user.get('server_user_id')}")
    print(f"   - latitude: {saved_user.get('latitude')}")
    print(f"   - longitude: {saved_user.get('longitude')}")

    assert saved_user is not None, "User should be saved"
    assert saved_user.get("phone_number") == phone, "Phone number should match"
    assert (
        saved_user.get("server_user_id") == server_user_id
    ), "server_user_id should be saved"

    print(f"\n[OK] STUB mode: server_user_id = {server_user_id} (None is normal for stub)")
    print("=" * 60)


async def test_registration_with_remote():
    """Test registration in remote mode (connected to NMservices)."""
    print("\n" + "=" * 60)
    print("TEST 2: Registration in REMOTE mode")
    print("=" * 60)

    config = RemoteApiConfig(
        base_url=os.getenv("REMOTE_API_BASE_URL", "http://localhost:9800"),
        api_key=os.getenv("REMOTE_API_KEY", "test_key"),
        timeout=10.0,
        max_retries=2,
    )

    storage = MemoryStorage()
    api_client = RemoteApiClient(config)
    sms_service = SmsServiceRemote(api_client=api_client)
    auth_service = AuthService(user_repo=storage, sms_service=sms_service)

    telegram_id = 987654321
    phone = "+998909999999"
    latitude = 41.2995
    longitude = 69.2401

    try:
        print(f"\n1. Calling auth_service.register_user('{phone}')...")
        server_user_id = await auth_service.register_user(phone)
        print(f"   Received server_user_id: {server_user_id}")

        print(f"\n2. Creating User model with server_user_id={server_user_id}...")
        user_data = User(
            id=telegram_id,
            telegram_id=telegram_id,
            phone_number=phone,
            registered_at=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            server_user_id=server_user_id,
        ).model_dump()

        print(f"\n3. Saving user to storage...")
        await storage.save_or_update_user(telegram_id, user_data)

        print(f"\n4. Verifying saved data...")
        saved_user = await storage.get_user_by_telegram_id(telegram_id)

        print(f"\n   Saved user data:")
        print(f"   - telegram_id: {saved_user.get('telegram_id')}")
        print(f"   - phone_number: {saved_user.get('phone_number')}")
        print(f"   - server_user_id: {saved_user.get('server_user_id')}")
        print(f"   - latitude: {saved_user.get('latitude')}")
        print(f"   - longitude: {saved_user.get('longitude')}")

        assert saved_user is not None, "User should be saved"
        assert (
            saved_user.get("phone_number") == phone
        ), "Phone number should match"
        assert (
            saved_user.get("server_user_id") is not None
        ), "server_user_id should NOT be None in remote mode"
        assert isinstance(
            saved_user.get("server_user_id"), int
        ), "server_user_id should be integer"

        print(
            f"\n[OK] REMOTE mode: server_user_id = {server_user_id} (real ID from server)"
        )
        print("=" * 60)

    finally:
        await api_client.close()


async def test_full_flow_comparison():
    """Compare stub vs remote mode behavior."""
    print("\n" + "=" * 60)
    print("TEST 3: Comparing STUB vs REMOTE")
    print("=" * 60)

    print("\n[STUB] Creating SMS service...")
    stub_sms = SmsServiceStub()
    await stub_sms.send_sms("+998901111111", "1234")
    stub_user_id = stub_sms.last_user_id
    print(f"[STUB] last_user_id = {stub_user_id}")

    print("\n[REMOTE] Creating SMS service...")
    config = RemoteApiConfig(
        base_url=os.getenv("REMOTE_API_BASE_URL", "http://localhost:9800"),
        api_key=os.getenv("REMOTE_API_KEY", "test_key"),
        timeout=10.0,
    )
    remote_sms = SmsServiceRemote(config=config)

    try:
        await remote_sms.send_sms("+998902222222", "1234")
        remote_user_id = remote_sms.last_user_id
        print(f"[REMOTE] last_user_id = {remote_user_id}")

        print("\n" + "-" * 60)
        print("COMPARISON RESULTS:")
        print(f"  STUB mode:   last_user_id = {stub_user_id} (None)")
        print(f"  REMOTE mode: last_user_id = {remote_user_id} (integer > 0)")
        print("-" * 60)

        assert stub_user_id is None, "Stub should return None"
        assert remote_user_id is not None, "Remote should return integer"
        assert isinstance(remote_user_id, int), "Remote user_id should be int"

        print("\n[OK] Differences between modes confirmed!")
        print("=" * 60)

    finally:
        await remote_sms.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  TESTING server_user_id SAVING DURING REGISTRATION")
    print("=" * 60)

    try:
        await test_registration_with_stub()
        await test_registration_with_remote()
        await test_full_flow_comparison()

        print("\n" + "=" * 60)
        print("  ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        print("\nCONCLUSION:")
        print("- STUB mode: server_user_id = None (local development)")
        print("- REMOTE mode: server_user_id = integer (ID from NMservices)")
        print("- Both values are correctly saved in User model")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
