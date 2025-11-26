from nomus.infrastructure.database.memory_storage import MemoryStorage
from nomus.infrastructure.services.sms_stub import SmsServiceStub
from nomus.domain.entities.user import User


class AuthService:

    def __init__(self, user_repo: MemoryStorage, sms_service: SmsServiceStub):
        self.user_repo: MemoryStorage = user_repo
        self.sms_service: SmsServiceStub = sms_service

    async def send_verification_code(self, phone: str) -> str:
        # In a real app, generate a random code. For PoC, use fixed '1234'
        code = "1234"
        await self.sms_service.send_sms(phone, code)
        return code

    async def register_user(self, user: User) -> None:
        # Simple registration logic
        # The repository should ideally also work with the User entity
        # For now, we can adapt it here, but the repo should be updated later.
        user_data = {"id": user.id, "telegram_id": user.telegram_id, "phone_number": user.phone_number, "registered_at": user.registered_at}
        await self.user_repo.save_user(user.phone_number, user_data)

    async def is_user_registered(self, telegram_id: int) -> bool:
        return await self.user_repo.get_user_by_telegram_id(telegram_id) is not None
