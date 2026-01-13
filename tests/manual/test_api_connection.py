"""
Test script for NMservices API connection
"""
import asyncio
import sys
from pathlib import Path

# Load .env file first
from dotenv import load_dotenv
load_dotenv(override=True)

# Add module path (go up two levels: manual -> tests -> project root -> src)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from nomus.config.settings import Settings
from nomus.infrastructure.services.remote_api_client import (
    RemoteApiClient,
    RemoteApiConfig,
)
from nomus.infrastructure.services.sms_remote import SmsServiceRemote
from nomus.infrastructure.services.payment_remote import PaymentServiceRemote


async def test_api_connection():
    """Test NMservices API connection"""
    print("=" * 60)
    print("NMservices API Connection Test")
    print("=" * 60)

    # Load settings
    try:
        settings = Settings()
        print(f"\n[OK] Settings loaded")
        print(f"  Environment: {settings.env.value}")
        print(f"  Remote API enabled: {settings.remote_api.enabled}")
        print(f"  Remote API base URL: {settings.remote_api.base_url}")
        print(f"  Remote API key: {'*' * len(settings.remote_api.api_key) if settings.remote_api.api_key else '(not set)'}")
    except Exception as e:
        print(f"\n[ERROR] Failed to load settings: {e}")
        return False

    # Check configuration
    if not settings.remote_api.enabled:
        print(f"\n[ERROR] Remote API is disabled in config")
        print(f"  Make sure ENV=development-remote in .env")
        return False

    if not settings.remote_api.base_url or not settings.remote_api.api_key:
        print(f"\n[ERROR] REMOTE_API_BASE_URL or REMOTE_API_KEY not configured")
        return False

    # Create client
    print(f"\n{'-' * 60}")
    print("Testing RemoteApiClient")
    print(f"{'-' * 60}")

    try:
        config = RemoteApiConfig(
            base_url=settings.remote_api.base_url,
            api_key=settings.remote_api.api_key,
            timeout=settings.remote_api.timeout,
            max_retries=settings.remote_api.max_retries,
            retry_delay=settings.remote_api.retry_delay,
        )
        client = RemoteApiClient(config)
        print(f"[OK] RemoteApiClient created")
    except Exception as e:
        print(f"[ERROR] Failed to create client: {e}")
        return False

    # Test user registration
    print(f"\n{'-' * 60}")
    print("Testing SMS Service (user registration)")
    print(f"{'-' * 60}")

    test_phone = "+998901234567"
    test_code = "1234"
    print(f"Sending registration request for: {test_phone}")

    try:
        sms_service = SmsServiceRemote(client)
        success = await sms_service.send_sms(test_phone, test_code)
        if success:
            user_id = sms_service.last_user_id
            print(f"[OK] Registration successful!")
            print(f"  User ID: {user_id}")
        else:
            print(f"[ERROR] Registration failed (API returned non-OK status)")
            user_id = None
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        import traceback
        traceback.print_exc()
        user_id = None

    # Test order creation
    if user_id:
        print(f"\n{'-' * 60}")
        print("Testing Payment Service (order creation)")
        print(f"{'-' * 60}")

        tariff_code = "standard_300"
        print(f"Creating order for user_id={user_id}, tariff={tariff_code}")

        try:
            payment_service = PaymentServiceRemote(client)
            success = await payment_service.create_order_with_payment(
                user_id=user_id,
                tariff_code=tariff_code,
                amount=30000,
            )
            if success:
                order_id = payment_service.last_order_id
                print(f"[OK] Order created successfully!")
                print(f"  Order ID: {order_id}")
            else:
                print(f"[ERROR] Order creation failed (API returned non-OK status)")
        except Exception as e:
            print(f"[ERROR] Order creation failed: {e}")
            import traceback
            traceback.print_exc()

    # Close client
    await client.close()
    print(f"\n{'-' * 60}")
    print("Test completed successfully!")
    print(f"{'-' * 60}\n")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_api_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[CRITICAL ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
