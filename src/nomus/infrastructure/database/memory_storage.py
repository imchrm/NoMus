from typing import Dict, Any, Optional


class MemoryStorage:
    def __init__(self):
        self.users: Dict[str, Any] = {}
        self.orders: Dict[str, Any] = {}

    async def save_user(self, phone: str, data: Dict[str, Any]) -> None:
        self.users[phone] = data
        print(f"[DB] User {phone} saved: {data}")

    async def get_user(self, phone: str) -> Optional[Dict[str, Any]]:
        return self.users.get(phone)

    async def create_order(self, order_id: str, data: Dict[str, Any]) -> None:
        self.orders[order_id] = data
        print(f"[DB] Order {order_id} created: {data}")
