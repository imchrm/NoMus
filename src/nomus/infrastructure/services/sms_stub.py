import asyncio
from typing import Optional


class SmsServiceStub:
    """
    Заглушка SMS-сервиса для локальной разработки.
    Симулирует отправку SMS без реального взаимодействия с провайдером.
    """

    def __init__(self):
        self._last_user_id: Optional[int] = None

    async def send_sms(self, phone: str, code: str) -> bool:
        print(f"[SMS-Stub] Sending code {code} to {phone}...")
        await asyncio.sleep(0.1)  # Simulate network delay
        print(f"[SMS-Stub] Code sent successfully.")
        return True

    @property
    def last_user_id(self) -> Optional[int]:
        """Возвращает None для stub-режима (нет интеграции с сервером)."""
        return self._last_user_id
