# Quick Start: Database & API Testing

This guide helps you quickly set up and test the NoMus bot with the remote NMservices API.

---

## Prerequisites

- NMservices running on `192.168.1.191:8000`
- Poetry installed
- Python 3.11+

---

## Step 1: Sync .env with .env.example

The `.env.example` file has been updated with the correct configuration for remote API testing.

**Copy the following values to your `.env` file**:

```bash
ENV=development-remote
REMOTE_API_BASE_URL=http://192.168.1.191:8000
REMOTE_API_KEY=troxivasine23
```

**Note**: The `DB_*` variables (DB_HOST, DB_USER, DB_PASSWORD) are **not required** for `development-remote` mode, as it uses in-memory storage. You can leave them as-is for future PostgreSQL migration.

---

## Step 2: Verify Environment

Run the environment check script:

```bash
poetry run python tests/manual/test_env_check.py
```

**Expected output**:
```
.env file found
  ENV=development-remote
  REMOTE_API_BASE_URL=http://192.168.1.191:8000
  REMOTE_API_KEY=**********
```

---

## Step 3: Test API Connection

Run the API connection test:

```bash
poetry run python tests/manual/test_api_connection.py
```

**Expected output**:
```
============================================================
NMservices API Connection Test
============================================================

[OK] Settings loaded
  Environment: development-remote
  Remote API enabled: True
  Remote API base URL: http://192.168.1.191:8000

[OK] RemoteApiClient created
[OK] Registration successful! User ID: X
[OK] Order created successfully! Order ID: Y
```

---

## Step 4: Run the Bot

Once API testing is successful, start the bot:

```bash
poetry run python -m nomus.main
```

The bot will:
- Connect to Telegram API
- Use remote NMservices for user registration (SMS)
- Use remote NMservices for order creation (Payment)
- Store data in memory (MemoryStorage)

---

## Troubleshooting

### Issue: "Remote API is disabled in config"

**Cause**: `.env` file not loaded or `ENV` variable not set correctly.

**Solution**:
1. Ensure `.env` exists in project root
2. Verify `ENV=development-remote` in `.env`
3. If running custom scripts, add:
   ```python
   from dotenv import load_dotenv
   load_dotenv(override=True)
   ```

### Issue: "Failed to connect to API"

**Cause**: NMservices not accessible.

**Solution**:
1. Check NMservices is running:
   ```bash
   curl http://192.168.1.191:8000/
   ```
   Should return: `{"message":"NoMus API is running"}`

2. Verify network connectivity
3. Check firewall settings

### Issue: "Authentication failed: invalid API key"

**Cause**: Incorrect `REMOTE_API_KEY`.

**Solution**:
1. Verify API key in `.env` matches NMservices configuration
2. Current key should be: `troxivasine23`

---

## Configuration Files Reference

### .env (Main configuration)
```bash
ENV=development-remote              # Environment selection
BOT_TOKEN=<your_telegram_bot_token> # From @BotFather
REMOTE_API_BASE_URL=http://192.168.1.191:8000
REMOTE_API_KEY=troxivasine23
```

### config/environments/development-remote.yaml
```yaml
environment: development
database:
  type: memory  # No PostgreSQL needed
services:
  sms:
    type: remote  # Use NMservices API
  payment:
    type: remote  # Use NMservices API
remote_api:
  enabled: true
  base_url: "${REMOTE_API_BASE_URL}"
  api_key: "${REMOTE_API_KEY}"
```

---

## Key Points

1. **Environment**: `development-remote` uses remote services but in-memory database
2. **Database**: PostgreSQL not required, uses `MemoryStorage`
3. **Services**: Both SMS and Payment use remote NMservices API
4. **server_user_id**: Registration returns `user_id` which must be stored and used for orders

---

## Next Steps

After successful testing:

1. Test bot registration flow with real Telegram user
2. Test order creation flow
3. Monitor NMservices logs for any errors
4. When ready for production, switch to PostgreSQL (update config)

---

**See also**:
- `TEST_RESULTS.md` - Detailed test results
- `CLAUDE.MD` - Complete project documentation
- `doc/bot_flow.md` - Detailed bot flow diagram
