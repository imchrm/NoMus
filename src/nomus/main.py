import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage

from nomus.config.settings import Settings
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.services.sms_stub import SmsServiceStub
from nomus.infrastructure.services.payment_stub import PaymentServiceStub
from nomus.application.services.auth_service import AuthService
from nomus.application.services.order_service import OrderService
from nomus.presentation.bot.middlewares.dependency_injection import (
    ServiceLayerMiddleware,
)
from nomus.presentation.bot.handlers import common, registration, ordering



async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    log: logging.Logger = logging.getLogger(__name__)
    
    settings = Settings()

    # 1. Infrastructure Layer
    storage = MemoryStorage()
    sms_stub = SmsServiceStub()
    payment_stub = PaymentServiceStub()

    # 2. Application Layer
    auth_service = AuthService(user_repo=storage, sms_service=sms_stub)
    order_service = OrderService(order_repo=storage, payment_service=payment_stub)

    # 3. Presentation Layer
    bot = Bot(
        token=settings.bot_token
    )  # Assuming API_KEY is the bot token for now based on .env
    dp = Dispatcher(storage=AiogramMemoryStorage())

    # Middleware
    dp.update.middleware(ServiceLayerMiddleware(auth_service, order_service))

    # Routers
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(ordering.router)

    log.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
