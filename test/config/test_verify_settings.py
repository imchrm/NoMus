import os
import sys

# Add src to path so we can import nomus
sys.path.insert(0, os.path.abspath("src"))

# Set environment variables to simulate .env file
os.environ["DEBUG"] = "True"
os.environ["API_KEY"] = "test_key"
os.environ["API_SECRET"] = "test_secret"
os.environ["API_PASSWORD"] = "test_password"
os.environ["API_URL"] = "http://localhost:8000"

try:
    from nomus.config.settings import Settings

    settings = Settings()
    assert isinstance(settings.debug, bool)
    assert isinstance(settings.api_key, str)
    assert isinstance(settings.api_secret, str)
    assert isinstance(settings.api_password, str)
    assert isinstance(settings.api_url, str)

    print("Settings loaded successfully:")
    print(f"Debug: {settings.debug}")
    print(f"API Key: {settings.api_key}")
    print(f"API URL: {settings.api_url}")
except ImportError as e:
    print(f"ImportError: {e}")
    print("Make sure pydantic-settings is installed.")
except Exception as e:
    print(f"Error loading settings: {e}")
