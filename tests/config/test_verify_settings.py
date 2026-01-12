import os
import sys

# Add src to path so we can import nomus
current_dir: str = os.path.dirname(os.path.abspath(__file__))
project_root: str = os.path.dirname(current_dir)
src_path: str = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Set environment variables to simulate .env file
os.environ["DEBUG"] = "True"
os.environ["REMOTE_API_BASE_URL"] = "http://localhost:9800"
os.environ["REMOTE_API_KEY"] = "test_key"

try:
    from nomus.config.settings import Settings

    settings = Settings()
    print("Settings loaded successfully:")
    print(f"Bot Token: {settings.bot_token}")
    print(f"Debug: {settings.debug}")
    print(f"Remote API Base URL: {settings.remote_api.base_url}")
    print(f"Remote API Key: {settings.remote_api.api_key}")
    if settings.messages:
        print(f"English Welcome: {settings.messages.en.welcome}")
        print(f"Russian Welcome: {settings.messages.ru.welcome}")
        print(f"Uzbek Welcome: {settings.messages.uz.welcome}")
    else:
        print("Messages not loaded from YAML")

except ImportError as e:
    print(f"ImportError: {e}")
    print("Make sure pydantic-settings and pyyaml are installed.")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback

    traceback.print_exc()
