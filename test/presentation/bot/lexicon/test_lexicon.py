
import os
import sys

from nomus.config.settings import I18nConfig

# Add src to path so we can import nomus
current_dir: str = os.path.dirname(os.path.abspath(__file__))
project_root: str = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_path: str = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

try:
    from nomus.config.settings import Settings

    settings = Settings()
    print("Settings loaded successfully:")
    print(f"Messages: {settings.messages}")
    assert settings.messages is not None, "Messages not loaded from YAML"

    # 1. Static access (when you know the language beforehand)
    print(f"EN (static): {settings.messages.en.welcome}")
    print(f"RU (static): {settings.messages.ru.welcome}")

    # 2. Dynamic access (using a variable)
    LANG = 'uz'
    # FIX: It!
    print(f"UZ (dynamic): {settings.messages[LANG].welcome}")
    # lang_config = I18nConfig()
    # print(f"UZ (dynamic): {settings.messages[lang_config.ru].welcome}")

except ImportError as e:
    print(f"ImportError: {e}")
    print("Make sure pydantic-settings and pyyaml are installed.")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc()
