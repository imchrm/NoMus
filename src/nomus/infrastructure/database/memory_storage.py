import logging
from typing import Dict, Any, List

from nomus.domain.interfaces.repo_interface import IStorageRepository

log: logging.Logger = logging.getLogger(__name__)


class MemoryStorage(IStorageRepository):
    """
    In-memory implementation of user and order repositories.
    
    This implementation stores data in Python dictionaries and is suitable
    for development and testing. Data is lost when the application stops.
    
    Implements:
        - IUserRepository interface
        - IOrderRepository interface
    """
    
    def __init__(self):
        self.users: Dict[int, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}

    # ==========================================
    # IUserRepository implementation
    # ==========================================

    async def save_or_update_user(self, telegram_id: int, data: Dict[str, Any]) -> None:
        """Saves or updates user data using telegram_id as the key."""
        if telegram_id in self.users:
            self.users[telegram_id].update(data)
            log.debug("User %s updated with data: %s", telegram_id, data)
        else:
            self.users[telegram_id] = data
            log.debug("User %s created with data: %s", telegram_id, data)

    async def get_user_by_phone(self, phone: str) -> Dict[str, Any] | None:
        """Finds a user by their phone number. Less efficient, used for checking duplicates."""
        for user_data in self.users.values():
            if user_data.get("phone_number") == phone:
                log.debug(
                    "Getting user by phone: %s, his data is:\n %s", phone, user_data
                )
                return user_data
        return None

    async def get_user_by_telegram_id(self, telegram_id: int) -> Dict[str, Any] | None:
        """Finds a user by their telegram_id directly."""
        user_data = self.users.get(telegram_id)
        log.debug("Get user data: %s", user_data)
        return user_data

    async def update_user_language(self, telegram_id: int, language_code: str) -> bool:
        """Updates the language for a user identified by telegram_id."""
        # Просто создаем или обновляем запись пользователя с новым языком.
        log.debug("Updating language for user %s to %s", telegram_id, language_code)
        await self.save_or_update_user(telegram_id, {"language_code": language_code})
        return True

    async def get_user_language(self, telegram_id: int) -> str | None:
        user = await self.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
        language_code = user.get("language_code")
        # Возвращаем language_code если это непустая строка, иначе None
        if language_code and isinstance(language_code, str):
            return language_code
        return None

    async def delete_user(self, telegram_id: int) -> bool:
        is_deleted = False
        if telegram_id in self.users:
            del self.users[telegram_id]
            log.debug("User %s deleted", telegram_id)
            is_deleted = True
        return is_deleted

    # ==========================================
    # IOrderRepository implementation
    # ==========================================

    async def save_or_update_order(self, order_id: str, data: Dict[str, Any]) -> None:
        """Creates or updates an order."""
        if order_id in self.orders:
            self.orders[order_id].update(data)
            log.debug("[DB] Order %s updated: %s", order_id, data)
        else:
            self.orders[order_id] = data
            log.debug("[DB] Order %s created: %s", order_id, data)
        log.debug("[DB] Order %s saved.", order_id)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any] | None:
        """Gets order by ID."""
        return self.orders.get(order_id)

    async def get_order_status(self, order_id: str) -> str | None:
        order = self.orders.get(order_id)
        if order:
            return order.get("status")
        return None

    async def get_orders_by_user(self, telegram_id: int) -> List[Dict[str, Any]]:
        # _user_orders = []
        # for order in self.orders.values():
        #     if (
        #         order.get("telegram_id") == telegram_id
        #     ):  # Assuming "user" field holds telegram_id
        #         _user_orders.append(order)
        _user_orders = [
            order for order in self.orders.values()
            if order.get("user_id") == telegram_id or order.get("telegram_id") == telegram_id
        ]
        log.debug("Found %d orders for user %s", len(_user_orders), telegram_id)
        return _user_orders

    async def update_order_status(self, order_id: str, status: str) -> None:
        order = self.orders.get(order_id)
        if not order:
            raise KeyError(f"Order {order_id} not found")
        order["status"] = status
        log.debug("Order %s status updated to %s", order_id, status)
