from pathlib import Path
from typing import Any, Dict, Type, Tuple, Literal, Optional, Final
import os
import re
import yaml
from pydantic import BaseModel, model_validator, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
from .environment import Environment


class DatabaseConfig(BaseModel):
    """Конфигурация базы данных"""

    type: Literal["memory", "postgres"] = "memory"
    host: str = ""
    port: int = 5432
    name: str = ""
    user: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 5


class ServiceConfig(BaseModel):
    """Конфигурация внешнего сервиса"""

    type: Literal["stub", "real", "remote"] = "stub"
    provider: str = ""
    test_mode: bool = True


class RemoteApiSettings(BaseModel):
    """Конфигурация удаленного API (NMservices)"""

    enabled: bool = False
    base_url: str = "http://127.0.0.1:9800"
    api_key: str = ""
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


class LoggingConfig(BaseModel):
    """Конфигурация логирования"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(levelname)s - %(message)s"


class BotConfig(BaseModel):
    """Конфигурация Telegram бота"""

    polling_timeout: int = 30


class ApiConfig(BaseModel):
    """Конфигурация API сервера"""

    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    workers: int = 1


class MonitoringConfig(BaseModel):
    """Конфигурация мониторинга"""

    sentry_dsn: str = ""
    enable_metrics: bool = False


class Messages(BaseModel):
    """Сообщения для локализации"""

    welcome: str = ""
    welcome_back: str = ""
    language_detected: str = ""
    dev_mode_skip_registration: str = ""
    error: str = ""
    language_changed_prompt: str = ""
    confirm_phone_button: str = ""
    share_phone_number_prompt: str = ""
    start_ordering_button: str = ""
    registration_button: str = ""
    cancel_button: str = ""
    order_registration_prompt: str = ""
    send_contact_button: str = ""
    send_contact_prompt: str = ""
    share_location_prompt: str = ""
    share_location_button: str = ""
    code_sent_prompt: str = ""
    send_code_as_text_prompt: str = ""
    invalid_code_error: str = ""
    enter_4_digits_prompt: str = ""
    registration_successful: str = ""
    phone_number_error: str = ""
    user_agreement_prompt: str = ""
    user_agreement_url: str = ""
    user_agreement_button: str = ""
    user_agreement_accept_button: str = ""
    order_continue_after_language: str = ""
    # Ordering flow — services
    select_service_prompt: str = ""
    enter_address_prompt: str = ""
    order_summary: str = ""
    confirm_order_button: str = ""
    cancel_order_button: str = ""
    order_created: str = ""
    order_cancelled: str = ""
    order_creating: str = ""
    services_unavailable: str = ""
    order_creation_error: str = ""
    no_services_available: str = ""
    # Main menu buttons
    settings_button: str = ""
    my_order_button: str = ""
    # Settings submenu
    settings_title: str = ""
    settings_language_button: str = ""
    settings_profile_button: str = ""
    settings_about_button: str = ""
    settings_back_button: str = ""
    # Profile
    profile_title: str = ""
    profile_no_data: str = ""
    # About / Help
    about_text: str = ""
    # My order
    my_order_title: str = ""
    no_active_order: str = ""
    # Status labels
    status_pending: str = ""
    status_confirmed: str = ""
    status_in_progress: str = ""
    status_completed: str = ""
    status_cancelled: str = ""


class I18nConfig(BaseModel):
    """Интернационализация"""

    uz: Messages = Messages()
    en: Messages = Messages()
    ru: Messages = Messages()


class EnvironmentConfigSource(PydanticBaseSettingsSource):
    """Загружает конфигурацию из config/environments/{env}.yaml"""

    def get_field_value(
        self, field: Any, field_name: str
    ) -> Tuple[Any, str, bool]:
        """Получает значение поля из источника"""
        return None, field_name, False

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        """Подготавливает значение поля"""
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        # Определяем окружение из переменной ENV
        env_name = os.getenv("ENV", "development")
        env = Environment.from_string(env_name)

        # Путь к файлу окружения
        config_file = Path(f"config/environments/{env.value}.yaml")

        if not config_file.exists():
            print(f"Warning: Config file {config_file} not found")
            return d

        try:
            content = yaml.safe_load(config_file.read_text("utf-8"))
            if content:
                # Раскрываем переменные окружения в значениях
                d.update(self._expand_env_vars(content))
        except (OSError, yaml.YAMLError) as e:
            print(f"Error loading environment config: {e}")

        return d

    def _expand_env_vars(self, obj: Any) -> Any:
        """Рекурсивно заменяет ${VAR} на значения из переменных окружения"""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Заменяем ${VAR_NAME} на значение из переменных окружения
            pattern = r"\$\{([^}]+)\}"

            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))

            return re.sub(pattern, replace_var, obj)
        return obj


class LocalizationConfigSource(PydanticBaseSettingsSource):
    """Загружает сообщения из config/localization/messages.yaml"""

    def get_field_value(
        self, field: Any, field_name: str
    ) -> Tuple[Any, str, bool]:
        """Получает значение поля из источника"""
        return None, field_name, False

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        """Подготавливает значение поля"""
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        # Пробуем новый путь
        config_file = Path("config/localization/messages.yaml")

        # Fallback на старый путь для обратной совместимости
        if not config_file.exists():
            config_file = Path("configuration.yaml")

        if not config_file.exists():
            print("Warning: Localization file not found")
            return d

        try:
            content = yaml.safe_load(config_file.read_text("utf-8"))
            if content and "messages" in content:
                d["messages"] = content["messages"]
        except (OSError, yaml.YAMLError) as e:
            print(f"Error loading localization: {e}")

        return d

class StorageConstants:
    """Константы для работы с репозитариями"""
    DB_MEMORY_TYPE: Final[str] = "memory"
    DB_POSTGRES_TYPE: Final[str] = "postgres"


class Settings(BaseSettings):
    """Главный класс настроек приложения"""

    # Environment
    env: Environment = Field(default=Environment.DEVELOPMENT)

    # Secret variables (from .env)
    debug: bool = False
    bot_token: str = ""

    # Database credentials (from .env)
    # NOTE: Not used in current architecture. Bot communicates with NMservices API,
    # which handles PostgreSQL connection. These are kept for potential future use.
    db_host: str = ""
    db_user: str = ""
    db_password: str = ""

    # Monitoring (from .env)
    sentry_dsn: str = ""

    # Development mode options (from .env)
    skip_registration: bool = False

    # Environment-specific configs (from yaml files)
    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()
    services: Dict[str, ServiceConfig] = {}
    remote_api: RemoteApiSettings = RemoteApiSettings()
    bot: BotConfig = BotConfig()
    api: ApiConfig = ApiConfig()
    monitoring: MonitoringConfig = MonitoringConfig()

    # Localization
    messages: I18nConfig = I18nConfig()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="after")
    def setup_environment(self) -> "Settings":
        """Устанавливает окружение из переменной ENV"""
        env_name = os.getenv("ENV", "development")
        self.env = Environment.from_string(env_name)
        return self

    @model_validator(mode="after")
    def check_messages_not_empty(self) -> "Settings":
        """Проверяет, что все сообщения локализации заполнены"""
        missing_fields = []
        for lang_code, messages_obj in self.messages:
            for field_name, field_value in messages_obj:
                if field_value == "":
                    missing_fields.append(f"{lang_code}.{field_name}")

        if missing_fields:
            raise ValueError(
                f"Found empty message fields in localization file: {', '.join(missing_fields)}\n"
                f"Check that the fields in the `Messages` class match the field names in the YAML file"
            )

        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Определяет порядок загрузки настроек"""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            EnvironmentConfigSource(settings_cls),
            LocalizationConfigSource(settings_cls),
            file_secret_settings,
        )

    def is_development(self) -> bool:
        """Проверяет, запущено ли приложение в режиме разработки"""
        return self.env == Environment.DEVELOPMENT

    def is_staging(self) -> bool:
        """Проверяет, запущено ли приложение в режиме staging"""
        return self.env == Environment.STAGING

    def is_production(self) -> bool:
        """Проверяет, запущено ли приложение в режиме production"""
        return self.env == Environment.PRODUCTION

    def get_log_level(self) -> str:
        """Возвращает уровень логирования"""
        return self.logging.level

    def get_database_url(self) -> Optional[str]:
        """Формирует URL для подключения к PostgreSQL"""
        if self.database.type != "postgres":
            return None

        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.database.host}:{self.database.port}/{self.database.name}"
        )
