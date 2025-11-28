# src/nomus/config/default_messages.py
from .settings import I18nConfig, Messages

# Создаем "пустой" объект I18nConfig.
# Pydantic автоматически подставит пустые строки для всех полей в Messages.
# Это значение будет использоваться, если configuration.yaml не найден
# или в нем отсутствует секция 'messages'.
DEFAULT_MESSAGES = I18nConfig(
    en=Messages(),
    ru=Messages(),
    uz=Messages()
)
