"""
Test settings loading with debug output
"""
import os
import sys
from pathlib import Path

# Load .env manually first
from dotenv import load_dotenv

print("=" * 60)
print("Settings Loading Test")
print("=" * 60)

# Try to load .env file manually (from project root)
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    print(f"\n[1] Loading .env file manually...")
    load_dotenv(env_file, override=True)
    print(f"    ENV after dotenv load: {os.getenv('ENV', '(not set)')}")
    print(f"    REMOTE_API_BASE_URL: {os.getenv('REMOTE_API_BASE_URL', '(not set)')}")
else:
    print(f"\n[1] .env file not found!")

# Add module path
sys.path.insert(0, str(project_root / "src"))

print(f"\n[2] Importing Settings class...")
from nomus.config.settings import Settings

print(f"\n[3] Creating Settings instance...")
try:
    settings = Settings()
    print(f"    [OK] Settings created")
    print(f"\n[4] Settings values:")
    print(f"    env: {settings.env.value}")
    print(f"    remote_api.enabled: {settings.remote_api.enabled}")
    print(f"    remote_api.base_url: {settings.remote_api.base_url}")
    print(f"    remote_api.api_key: {'*' * len(settings.remote_api.api_key) if settings.remote_api.api_key else '(empty)'}")
    print(f"    bot_token: {'*' * len(settings.bot_token) if settings.bot_token else '(empty)'}")
except Exception as e:
    print(f"    [ERROR] Failed to create settings: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
