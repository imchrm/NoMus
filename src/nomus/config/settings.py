import yaml
from pathlib import Path
from typing import Any, Dict, Type, Tuple
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)


class Messages(BaseModel):
    welcome: str
    error: str


class I18nConfig(BaseModel):
    uz: Messages
    en: Messages
    ru: Messages


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(self, field: Any, field_name: str) -> Tuple[Any, str, bool]:
        encoding = self.config.get("env_file_encoding")
        file_content_json = yaml.safe_load(
            Path("configuration.yaml").read_text(encoding)
        )
        field_value = file_content_json.get(field_name)
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
            file_content: Dict[str, Any] = yaml.safe_load(config_file.read_text(encoding or "utf-8"))
            if file_content:
                d.update(file_content)
        except Exception as e:
            # Handle or log error if needed
            print(f"Error loading yaml: {e}")

        return d

class Settings(BaseSettings):
    # Env settings
    debug: bool = False
    api_key: str = ''
    api_secret: str = ''
    api_password: str = ''
    api_url: str = ''

    # Yaml settings
    app_name: str = "NoMus"
    version: str = "0.0.1"
    messages: I18nConfig | None = None

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
