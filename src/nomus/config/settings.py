from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = False
    api_key: str
    api_secret: str
    api_password: str
    api_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
