from enum import Enum


class Environment(str, Enum):
    """Перечисление доступных окружений приложения"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """Создает Environment из строки, с fallback на DEVELOPMENT"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DEVELOPMENT
