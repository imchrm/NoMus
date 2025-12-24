"""
Интерфейс для SMS-сервиса.
Определяет контракт для всех реализаций SMS-сервисов (stub, remote, real).
"""

from typing import Protocol, Optional


class ISmsService(Protocol):
    """
    Интерфейс для SMS-сервиса.

    Используется для абстракции от конкретной реализации:
    - SmsServiceStub - заглушка для разработки
    - SmsServiceRemote - удаленный API NMservices
    - SmsServiceReal - реальный SMS провайдер (будущая реализация)
    """

    async def send_sms(self, phone: str, code: str) -> bool:
        """
        Отправляет SMS с кодом верификации.

        Args:
            phone: Номер телефона в формате +998XXXXXXXXX
            code: Код верификации (обычно 4-6 цифр)

        Returns:
            True если SMS успешно отправлено, False иначе
        """
        ...

    @property
    def last_user_id(self) -> Optional[int]:
        """
        Возвращает ID пользователя с сервера (для remote-режима).

        Returns:
            ID пользователя после регистрации или None для stub-режима
        """
        ...
