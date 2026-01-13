"""
Quick environment check script
"""
import os
from pathlib import Path

print("=" * 60)
print("Environment Variables Check")
print("=" * 60)

# Get project root (go up two levels: manual -> tests -> project root)
project_root = Path(__file__).parent.parent.parent

# Check .env file
env_file = project_root / ".env"
if env_file.exists():
    print("\n.env file found")
    with open(env_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if 'ENV=' in line or 'REMOTE_API' in line or 'BOT_TOKEN' in line:
                    # Hide sensitive data
                    if 'KEY' in line or 'TOKEN' in line:
                        key, value = line.split('=', 1)
                        print(f"  {key}={'*' * min(len(value), 10)}")
                    else:
                        print(f"  {line}")
else:
    print("\n[WARNING] .env file not found!")

print(f"\n{'-' * 60}")
print("OS Environment Variables")
print(f"{'-' * 60}")
print(f"  ENV = {os.getenv('ENV', '(not set)')}")
print(f"  REMOTE_API_BASE_URL = {os.getenv('REMOTE_API_BASE_URL', '(not set)')}")
print(f"  REMOTE_API_KEY = {'*' * len(os.getenv('REMOTE_API_KEY', '')) if os.getenv('REMOTE_API_KEY') else '(not set)'}")
print(f"  BOT_TOKEN = {'*' * len(os.getenv('BOT_TOKEN', '')) if os.getenv('BOT_TOKEN') else '(not set)'}")

print(f"\n{'-' * 60}")
print("YAML Config Files")
print(f"{'-' * 60}")
for env_name in ['development', 'development-remote', 'staging', 'production']:
    config_file = project_root / f"config/environments/{env_name}.yaml"
    if config_file.exists():
        print(f"  [OK] {env_name}.yaml")
    else:
        print(f"  [MISS] {env_name}.yaml")

print("\n" + "=" * 60)
