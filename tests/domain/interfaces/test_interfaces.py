"""
Простой скрипт для проверки, что все интерфейсы работают корректно.
Запустить: poetry run python test_interfaces.py
"""

import asyncio
from nomus.config.settings import Settings
from nomus.infrastructure.factory import ServiceFactory


async def test_user_repository():
    """Тестируем IUserRepository"""
    print("🧪 Testing IUserRepository...")
    
    settings = Settings()
    storage = ServiceFactory.create_storage(settings)
    
    # Создаем пользователя
    await storage.save_or_update_user(12345, {
        "phone_number": "+998901234567",
        "language_code": "uz"
    })
    print("✅ User created")
    
    # Получаем по telegram_id
    user = await storage.get_user_by_telegram_id(12345)
    assert user is not None
    assert user["phone_number"] == "+998901234567"
    print("✅ Get user by telegram_id works")
    
    # Получаем по телефону
    user_by_phone = await storage.get_user_by_phone("+998901234567")
    assert user_by_phone is not None
    print("✅ Get user by phone works")
    
    # Получаем язык
    language = await storage.get_user_language(12345)
    assert language == "uz"
    print("✅ Get user language works")
    
    # Обновляем пользователя
    await storage.save_or_update_user(12345, {"language_code": "ru"})
    language = await storage.get_user_language(12345)
    assert language == "ru"
    print("✅ Update user works")
    
    # Удаляем пользователя
    deleted = await storage.delete_user(12345)
    assert deleted is True
    user = await storage.get_user_by_telegram_id(12345)
    assert user is None
    print("✅ Delete user works")
    
    print("✅ All IUserRepository tests passed!\n")


async def test_order_repository():
    """Тестируем IOrderRepository"""
    print("🧪 Testing IOrderRepository...")
    
    settings = Settings()
    storage = ServiceFactory.create_storage(settings)
    
    # Создаем заказ
    await storage.save_or_update_order("ORD-001", {
        "telegram_id": 12345,
        "tariff": "Premium",
        "amount": 30000,
        "status": "pending"
    })
    print("✅ Order created")
    
    # Получаем заказ
    order = await storage.get_order_by_id("ORD-001")
    assert order is not None
    assert order["amount"] == 30000
    print("✅ Get order by ID works")
    
    # Получаем статус
    status = await storage.get_order_status("ORD-001")
    assert status == "pending"
    print("✅ Get order status works")
    
    # Обновляем статус
    await storage.update_order_status("ORD-001", "completed")
    status = await storage.get_order_status("ORD-001")
    assert status == "completed"
    print("✅ Update order status works")
    
    # Создаем еще заказы для пользователя
    await storage.save_or_update_order("ORD-002", {
        "telegram_id": 12345,
        "status": "pending"
    })
    await storage.save_or_update_order("ORD-003", {
        "telegram_id": 67890,
        "status": "pending"
    })
    
    # Получаем все заказы пользователя
    user_orders = await storage.get_orders_by_user(12345)
    print(f"Total orders for user: {len(user_orders)}")
    assert len(user_orders) == 2
    print("✅ Get orders by user works")
    
    print("✅ All IOrderRepository tests passed!\n")


async def main():
    print("=" * 50)
    print("🚀 Testing Repository Interfaces")
    print("=" * 50 + "\n")
    
    await test_user_repository()
    await test_order_repository()
    
    print("=" * 50)
    print("🎉 All tests passed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
