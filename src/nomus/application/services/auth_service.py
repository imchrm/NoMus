from nomus.domain.interfaces.repo_interface import IUserRepository
from nomus.infrastructure.services.sms_stub import SmsServiceStub


class AuthService:
    def __init__(self, user_repo: IUserRepository, sms_service: SmsServiceStub):
        self.user_repo: IUserRepository = user_repo
        self.sms_service: SmsServiceStub = sms_service

    async def send_verification_code(self, phone: str) -> str:
        # In a real app, generate a random code. For PoC, use fixed '1234'
        code = "1234"
        await self.sms_service.send_sms(phone, code)
        return code

    async def is_user_registered(self, telegram_id: int) -> bool:
        """
        Checks if a user is registered.
        A user is considered registered if their record exists and contains a phone number.
        """
        user_data = await self.user_repo.get_user_by_telegram_id(telegram_id)
        if not user_data:
            return False
        # The presence of a phone number indicates that the user has completed registration.
        return "phone_number" in user_data and user_data.get("phone_number") is not None
