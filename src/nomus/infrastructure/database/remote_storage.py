import logging
from typing import Any, Dict, List, Set
from nomus.domain.interfaces.repo_interface import IStorageRepository
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.services.remote_api_client import RemoteApiClient, RemoteApiError

log: logging.Logger = logging.getLogger(__name__)


class RemoteStorage(IStorageRepository):
    """
    Remote storage с локальным кешированием.
    Использует MemoryStorage как кеш для минимизации запросов к API.

    Применяет Write-Behind Cache Pattern:
    - Все операции сначала выполняются в локальном кеше (быстро)
    - Изменения помечаются как "dirty"
    - При вызове flush() все изменения отправляются в remote API
    """

    def __init__(self, api_client: RemoteApiClient):
        self._cache = MemoryStorage()  # Композиция, не наследование!
        self._api_client = api_client
        self._dirty_users: Set[int] = set()  # Пользователи, требующие синхронизации
        self._dirty_orders: Set[str] = set()  # Заказы, требующие синхронизации

    # ==========================================
    # IUserRepository implementation
    # ==========================================

    async def save_or_update_user(self, telegram_id: int, data: Dict[str, Any]) -> None:
        """Сохраняет пользователя в кеш и помечает для синхронизации"""
        await self._cache.save_or_update_user(telegram_id, data)
        self._dirty_users.add(telegram_id)
        log.debug("User %s saved to cache and marked dirty", telegram_id)

    async def get_user_by_phone(self, phone: str) -> Dict[str, Any] | None:
        """Получает пользователя из кеша по телефону"""
        return await self._cache.get_user_by_phone(phone)

    async def get_user_by_telegram_id(self, telegram_id: int) -> Dict[str, Any] | None:
        """Получает пользователя из кеша или remote API (Read-Through)"""
        # 1. Проверяем кеш
        user = await self._cache.get_user_by_telegram_id(telegram_id)
        if user:
            return user

        # 2. Если нет в кеше, пробуем загрузить с сервера
        try:
            user = await self._api_client.get(f"/users/{telegram_id}")
            if user:
                # Сохраняем в кеш, но не помечаем как dirty (данные свежие)
                await self._cache.save_or_update_user(telegram_id, user)
                log.debug("User %s loaded from remote API", telegram_id)
                return user
        except RemoteApiError as e:
            log.warning("Failed to load user %s from remote: %s", telegram_id, e)

        return None

    async def get_user_language(self, telegram_id: int) -> str | None:
        """Получает язык пользователя из кеша"""
        return await self._cache.get_user_language(telegram_id)

    async def update_user_language(self, telegram_id: int, language_code: str) -> bool:
        """Обновляет язык пользователя в кеше и помечает для синхронизации"""
        result = await self._cache.update_user_language(telegram_id, language_code)
        if result:
            self._dirty_users.add(telegram_id)
            log.debug("User %s language updated in cache and marked dirty", telegram_id)
        return result

    async def delete_user(self, telegram_id: int) -> bool:
        """Удаляет пользователя из кеша (TODO: синхронизация удаления)"""
        result = await self._cache.delete_user(telegram_id)
        if result:
            # Удаляем из dirty set, если был там
            self._dirty_users.discard(telegram_id)
            # TODO: добавить синхронизацию удаления с remote API
            log.warning("User %s deleted from cache, but remote deletion not implemented", telegram_id)
        return result

    # ==========================================
    # IOrderRepository implementation
    # ==========================================

    async def save_or_update_order(self, order_id: str, data: Dict[str, Any]) -> None:
        """Сохраняет заказ в кеш и помечает для синхронизации"""
        await self._cache.save_or_update_order(order_id, data)
        self._dirty_orders.add(order_id)
        log.debug("Order %s saved to cache and marked dirty", order_id)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any] | None:
        """Получает заказ из кеша"""
        return await self._cache.get_order_by_id(order_id)

    async def get_order_status(self, order_id: str) -> str | None:
        """Получает статус заказа из кеша"""
        return await self._cache.get_order_status(order_id)

    async def get_orders_by_user(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получает все заказы пользователя из кеша"""
        return await self._cache.get_orders_by_user(telegram_id)

    async def update_order_status(self, order_id: str, status: str) -> None:
        """Обновляет статус заказа в кеше и помечает для синхронизации"""
        await self._cache.update_order_status(order_id, status)
        self._dirty_orders.add(order_id)
        log.debug("Order %s status updated in cache and marked dirty", order_id)

    # ==========================================
    # Flush mechanism
    # ==========================================

    async def flush(self) -> None:
        """
        Синхронизирует все изменения с remote API.
        Отправляет данные о всех "dirty" пользователях и заказах.
        """
        if not self._dirty_users and not self._dirty_orders:
            log.debug("No dirty data to flush")
            return

        log.info("Flushing %d users and %d orders to remote API",
                len(self._dirty_users), len(self._dirty_orders))

        # Синхронизация пользователей
        for telegram_id in self._dirty_users:
            user_data = await self._cache.get_user_by_telegram_id(telegram_id)
            if user_data:
                try:
                    await self._api_client.post("/users/register", user_data)
                    log.debug("User %s synced to remote API", telegram_id)
                except RemoteApiError as e:
                    log.error("Failed to sync user %s: %s", telegram_id, e)
                    # TODO: решить, что делать с ошибками (retry, rollback, etc.)

        # Синхронизация заказов
        for order_id in self._dirty_orders:
            order_data = await self._cache.get_order_by_id(order_id)
            if order_data:
                try:
                    await self._api_client.post("/orders", order_data)
                    log.debug("Order %s synced to remote API", order_id)
                except RemoteApiError as e:
                    log.error("Failed to sync order %s: %s", order_id, e)

        # Очищаем dirty sets
        self._dirty_users.clear()
        self._dirty_orders.clear()
        log.info("Flush completed")
