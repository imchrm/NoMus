from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: int
    telegram_id: int
    phone_number: str
    registered_at: datetime
