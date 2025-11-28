import logging
from typing import Dict, Any, Optional


log: logging.Logger = logging.getLogger(__name__)
class MemoryStorage:
    def __init__(self):
        # self.users: Dict[str, Any] = {}
        # Давайте сменим ключ на telegram_id (int), как вы и предложили.
        # Это гораздо более надежный и эффективный подход.
        self.users: Dict[int, Any] = {}
        self.orders: Dict[str, Any] = {}
        
    async def save_or_update_user(self, telegram_id: int, data: Dict[str, Any]) -> None:
        """Saves or updates user data using telegram_id as the key."""
        if telegram_id in self.users:
            self.users[telegram_id].update(data)
            log.info("User %s updated with data: %s", telegram_id, data)
        else:
            self.users[telegram_id] = data
            log.info("User %s created with data: %s", telegram_id, data)

    async def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Finds a user by their phone number. Less efficient, used for checking duplicates."""
        for user_data in self.users.values():
            if user_data.get("phone_number") == phone:
                return user_data
        return None

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Finds a user by their telegram_id directly."""
        return self.users.get(telegram_id)

    async def update_user_language(self, telegram_id: int, lang_code: str) -> bool:
        """Updates the language for a user identified by telegram_id."""
        # Просто создаем или обновляем запись пользователя с новым языком.
        await self.save_or_update_user(telegram_id, {"language_code": lang_code})
        return True

    async def create_order(self, order_id: str, data: Dict[str, Any]) -> None:
        self.orders[order_id] = data
        log.info("[DB] Order %s created: %s", order_id, data)
