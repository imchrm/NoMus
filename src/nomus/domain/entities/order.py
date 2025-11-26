from datetime import datetime
from dataclasses import dataclass

@dataclass
class Order:
    id: int
    user_id: int
    amount: int
    created_at: datetime
    status: str  # e.g., "pending", "completed", "cancelled"
    
