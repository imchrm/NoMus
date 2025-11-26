import logging
from typing import Dict, Any, Optional


log: logging.Logger = logging.getLogger(__name__)
class MemoryStorage:
    def __init__(self):
        self.users: Dict[str, Any] = {}
        self.orders: Dict[str, Any] = {}
        
    # TODO: change dictionary, save data by User like Dict[User, 'Any']
    async def save_user(self, phone: str, data: Dict[str, Any]) -> None:
        self.users[phone] = data
        print(f"[DB] User {phone} saved: {data}")

    async def get_user(self, phone: str) -> Optional[Dict[str, Any]]:
        return self.users.get(phone)

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Finds a user by their telegram_id by iterating through the stored users."""
        for user_data in self.users.values():
            if user_data.get("telegram_id") == telegram_id:
                return user_data
        return None

    async def create_order(self, order_id: str, data: Dict[str, Any]) -> None:
        self.orders[order_id] = data
        log.info("[DB] Order %s created: %s", order_id, data)
