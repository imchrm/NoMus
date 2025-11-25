from typing import Any
from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.services.sms_stub import SmsServiceStub


class AuthService:
    def __init__(self, user_repo: MemoryStorage, sms_service: SmsServiceStub):
        self.user_repo = user_repo
        self.sms_service = sms_service

    async def send_verification_code(self, phone: str) -> str:
        # In a real app, generate a random code. For PoC, use fixed '1234'
        code = "1234"
        await self.sms_service.send_sms(phone, code)
        return code

    async def register_user(self, phone: str) -> None:
        # Simple registration logic
        await self.user_repo.save_user(phone, {"phone": phone, "registered": True})
