from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    telegram_id: int
    phone_number: str
    registered_at: datetime
    