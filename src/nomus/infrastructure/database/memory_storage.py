import logging
from typing import Dict, Any, List

log: logging.Logger = logging.getLogger(__name__)


class MemoryStorage:
    def __init__(self):
        # self.users: Dict[str, Any] = {}
        # Давайте сменим ключ на telegram_id (int), как вы и предложили.
        # Это гораздо более надежный и эффективный подход.
        self.users: Dict[int, Any] = {}
        self.orders: Dict[str, Any] = {}

    # --- User Repository Implementation ---

    async def save_or_update_user(self, telegram_id: int, data: Dict[str, Any]) -> None:
        """Saves or updates user data using telegram_id as the key."""
        if telegram_id in self.users:
            self.users[telegram_id].update(data)
            log.info("User %s updated with data: %s", telegram_id, data)
        else:
            self.users[telegram_id] = data
            log.info("User %s created with data: %s", telegram_id, data)

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
        language_code = user.get("language_code")  # Получаем значение
        # Проверяем, что это непустая строка
        if language_code and isinstance(language_code, str):
            return language_code
        raise ValueError(f"Invalid language_code: {language_code}")

    async def delete_user(self, telegram_id: int) -> bool:
        if telegram_id in self.users:
            del self.users[telegram_id]
            log.info("User %s deleted", telegram_id)
            return True
        return False

    # --- Order Repository Implementation ---

    async def save_or_update_order(self, order_id: str, data: Dict[str, Any]) -> None:
        self.orders[order_id] = data
        log.info("[DB] Order %s saved: %s", order_id, data)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any] | None:
        return self.orders.get(order_id)

    async def get_order_status(self, order_id: str) -> str | None:
        order = self.orders.get(order_id)
        if order:
            return order.get("status")
        return None

    async def get_orders_by_user(self, telegram_id: int) -> List[Dict[str, Any]]:
        user_orders = []
        for order in self.orders.values():
            if (
                order.get("user") == telegram_id
            ):  # Assuming "user" field holds telegram_id
                user_orders.append(order)
        return user_orders

    async def update_order_status(self, order_id: str, status: str) -> None:
        order = self.orders.get(order_id)
        if not order:
            raise KeyError(f"Order {order_id} not found")
        order["status"] = status
        log.info("Order %s status updated to %s", order_id, status)
