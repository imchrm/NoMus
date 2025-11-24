from pydantic import BaseModel

from nomus.config.settings import Settings 

class Application(BaseModel):
    settings: Settings

    def start(self) -> None:
        print(f"App Name: {self.settings.app_name}")
        print(f"Version: {self.settings.version}")
        print(f"Debug: {self.settings.debug}")
        print(f"API Key: {self.settings.api_key}")
        print(f"API URL: {self.settings.api_url}")
        if self.settings.messages:
            print(f"English Welcome: {self.settings.messages.en.welcome}")
            print(f"Russian Welcome: {self.settings.messages.ru.welcome}")
            print(f"Uzbek Welcome: {self.settings.messages.uz.welcome}")

def main() -> None:
    settings = Settings()
    app = Application(settings=settings)
    app.start()

if __name__ == "__main__":
    main()