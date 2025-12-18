import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage as AiogramMemoryStorage

from nomus.config.settings import Settings
from nomus.infrastructure.factory import ServiceFactory
from nomus.application.services.auth_service import AuthService
from nomus.application.services.order_service import OrderService
from nomus.presentation.bot.middlewares.l10n_middleware import L10nMiddleware
from nomus.presentation.bot.handlers import (
    common,
    registration,
    ordering,
    language,
)


class BotApplication:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.log = self._setup_logging()

        self.log.info(
            "Starting NoMus in %s environment", settings.env.value.upper()
        )

        # 1. Infrastructure Layer - используем фабрику
        self.storage = ServiceFactory.create_storage(settings)
        self.sms_service = ServiceFactory.create_sms_service(settings)
        self.payment_service = ServiceFactory.create_payment_service(settings)

        # 2. Application Layer
        self.auth_service = AuthService(
            user_repo=self.storage, sms_service=self.sms_service
        )
        self.order_service = OrderService(
            order_repo=self.storage, payment_service=self.payment_service
        )

        # 3. Presentation Layer
        self.bot = Bot(token=self.settings.bot_token)
        self.dp = Dispatcher(storage=AiogramMemoryStorage())

        self._setup_middlewares()
        self._register_routers()
        self._register_lifecycle_hooks()

    def _setup_logging(self) -> logging.Logger:
        log_config = self.settings.logging
        logging.basicConfig(
            level=getattr(logging, log_config.level),
            format=log_config.format,
        )
        return logging.getLogger(__name__)

    def _setup_middlewares(self):
        # Подключаем middleware для локализации, передавая ему storage
        self.dp.update.middleware(
            L10nMiddleware(settings=self.settings, storage=self.storage)
        )

    def _register_routers(self):
        # Порядок важен! Сначала более специфичные (с состояниями), потом более общие.
        self.dp.include_router(common.router)
        self.dp.include_router(registration.router)
        self.dp.include_router(ordering.router)
        self.dp.include_router(
            language.router
        )  # Этот роутер должен быть последним TODO: проверить это!

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


def run():
    asyncio.run(main())


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("Bot stopped by user.")
