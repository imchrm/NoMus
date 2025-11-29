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


class BotApplication:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.log = self._setup_logging()

        # 1. Infrastructure Layer
        self.storage = MemoryStorage()
        self.sms_stub = SmsServiceStub()
        self.payment_stub = PaymentServiceStub()

        # 2. Application Layer
        self.auth_service = AuthService(user_repo=self.storage, sms_service=self.sms_stub)
        self.order_service = OrderService(order_repo=self.storage, payment_service=self.payment_stub)

        # 3. Presentation Layer
        self.bot = Bot(token=self.settings.bot_token)
        self.dp = Dispatcher(storage=AiogramMemoryStorage())

        self._setup_middlewares()
        self._register_routers()
        self._register_lifecycle_hooks()

    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _setup_middlewares(self):
        # Подключаем middleware для локализации, передавая ему storage
        self.dp.update.middleware(L10nMiddleware(settings=self.settings, storage=self.storage))

    def _register_routers(self):
        # Порядок важен! Сначала более специфичные (с состояниями), потом более общие.
        self.dp.include_router(common.router)
        self.dp.include_router(registration.router)
        self.dp.include_router(ordering.router)
        self.dp.include_router(language.router)  # Этот роутер должен быть последним

    def _register_lifecycle_hooks(self):
        self.dp.startup.register(self.on_startup)
        self.dp.shutdown.register(self.on_shutdown)

    async def on_startup(self, bot: Bot):
        self.log.info("Starting bot...")

    async def on_shutdown(self, bot: Bot):
        self.log.info("Bot stopped")
        await bot.session.close()

    async def run(self):
        try:
            await self.dp.start_polling(
                self.bot,
                auth_service=self.auth_service,
                order_service=self.order_service,
                storage=self.storage,
                settings=self.settings,
                log=self.log,
            )
        except asyncio.CancelledError:
            # No need to do anything.
            pass


async def main():
    settings = Settings()
    app = BotApplication(settings)
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
