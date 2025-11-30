from pathlib import Path
from typing import Any, Dict, Type, Tuple
import yaml
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
# from .default_messages import DEFAULT_MESSAGES


class Messages(BaseModel):
    # The field values ​​below are taken from the configuration.yaml file.
    welcome: str = ""
    error: str = ""
    start_ordering_button: str = ""
    registration_button: str = ""
    cancel_button: str = ""
    order_registration_prompt: str = ""
    send_contact_button: str = ""
    send_contact_prompt: str = ""
    code_sent_prompt: str = ""  # TODO Проверить это используется?
    send_code_as_text_prompt: str = ""
    invalid_code_error: str = ""
    enter_4_digits_prompt: str = ""
    registration_successful: str = ""
    select_tariff_prompt: str = ""
    phone_number_error: str = ""  # TODO Проверить это используется?
    choose_tariff_from_list_prompt: str = ""
    payment_button: str = ""
    payment_prompt: str = ""
    payment_processing: str = ""
    order_success: str = ""
    payment_error: str = ""


class I18nConfig(BaseModel):
    uz: Messages = Messages()
    en: Messages = Messages()
    ru: Messages = Messages()


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(self, field: Any, field_name: str) -> Tuple[Any, str, bool]:
        encoding: str | None = self.config.get("env_file_encoding")
        file_content_json: Any = yaml.safe_load(
            Path("configuration.yaml").read_text(encoding)
        )
        field_value: Any = file_content_json.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        encoding: str | None = self.config.get("env_file_encoding")
        config_file = Path("configuration.yaml")

        if not config_file.exists():
            return d

        try:
            file_content: Dict[str, Any] = yaml.safe_load(
                config_file.read_text(encoding or "utf-8")
            )
            if file_content:
                d.update(file_content)
        except Exception as e:
            # Handle or log error if needed
            print(f"Error loading yaml: {e}")

        return d


class Settings(BaseSettings):
    # Env settings
    debug: bool = False
    bot_token: str = ""
    api_key: str = ""
    api_secret: str = ""
    api_password: str = ""
    api_url: str = ""

    # Yaml settings
    # app_name: str = "NoMus" # TODO удалить
    # version: str = "0.0.1" # TODO удалить
    messages: I18nConfig = I18nConfig()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
