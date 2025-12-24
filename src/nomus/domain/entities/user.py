from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: int
    telegram_id: int
    phone_number: str
    registered_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    server_user_id: int | None = None  # ID пользователя на сервере NMservices
