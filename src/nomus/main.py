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
from nomus.presentation.bot.middlewares.l10n_middleware import L10nMiddleware
from nomus.presentation.bot.handlers import common, registration, ordering, language


async def on_startup(bot: Bot, log: logging.Logger):
    log.info("Starting bot...")


async def on_shutdown(bot: Bot, log: logging.Logger):
    log.info("Bot stopped")
    await bot.session.close()



async def main():
    logging.basicConfig(
        level=logging.DEBUG,
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

    # Подключаем middleware для локализации, передавая ему storage
    dp.update.middleware(L10nMiddleware(settings=settings, storage=storage))

    # Регистрируем хуки startup и shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Routers
    # Порядок важен! Сначала более специфичные (с состояниями), потом более общие.
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(ordering.router)
    dp.include_router(language.router) # Этот роутер должен быть последним из тех, что обрабатывают callback'и

    try:
        # Используем встроенный DI для сервисов и хранилища
        await dp.start_polling(
            bot,
            auth_service=auth_service,
            order_service=order_service,
            storage=storage,
            settings=settings,
            log=log,  # Передаем логгер в хуки
        )
    except asyncio.CancelledError:
        # Это исключение возникает при остановке бота (Ctrl+C),
        # обработка не требуется, так как aiogram сам корректно завершает работу.
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
