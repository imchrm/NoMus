# NoMus

Project for providing services to the population.

## Structure

The project follows the `src` layout structure:

```text
NoMus/
├── src/
│   └── nomus/          # Main package
│       ├── main.py     # Entry point
│       └── ...
├── pyproject.toml
└── ...
```

## Clone

```bash
git clone https://github.com/imchrm/NoMus.git
cd NoMus
```

## Install Poetry

Official installation [guide](https://python-poetry.org/docs/#installation).

## Setup Dependencies of Project

1. Make sure you're inside your "NoMus" project.
2. To install the virtual environment specifically within your project, rather than in a single location for all project environments, run the following command:

```bash
poetry config virtualenvs.in-project true
```
, and then install dependencies:
```bash
poetry install
```

## Activate Enviroment

1. Windows:
```bash
.venv\Scripts\activate
```
2. Linux/MacOS:
```bash
source .venv/bin/activate
```

## Environment Configuration

The project supports multiple environments: **development**, **staging**, and **production**.

### Setting Up Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and set your environment variables:
```bash
# Select environment: development, staging, production
ENV=development

DEBUG=True
BOT_TOKEN=your_token_from_BotFather

API_KEY=your_api_key
API_SECRET=your_api_secret
API_PASSWORD=your_api_password
API_URL=your_api_url

# For staging/production (PostgreSQL)
DB_HOST=localhost
DB_USER=nomus_user
DB_PASSWORD=secure_password
```

### Environment Differences

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| Database | In-memory | PostgreSQL | PostgreSQL |
| SMS Service | Stub (logs to console) | Real (test mode) | Real (live) |
| Payment Service | Stub (instant) | Real (test mode) | Real (live) |
| Logging Level | DEBUG | INFO | WARNING |
| Monitoring | Disabled | Optional | Enabled |

### Configuration Files

Environment-specific settings are stored in:
- `config/environments/development.yaml` - Development settings
- `config/environments/staging.yaml` - Staging settings
- `config/environments/production.yaml` - Production settings
- `config/localization/messages.yaml` - Localization messages (all environments)

## Usage

### Running in Different Environments

**Development (default):**
```bash
# Using scripts
./scripts/run_dev.sh      # Linux/MacOS
scripts\run_dev.bat       # Windows

# Or manually
ENV=development poetry run python -m nomus.main
```

**Staging:**
```bash
# Using scripts
./scripts/run_staging.sh   # Linux/MacOS
scripts\run_staging.bat    # Windows

# Or manually
ENV=staging poetry run python -m nomus.main
```

**Production:**
```bash
# Using scripts
./scripts/run_prod.sh      # Linux/MacOS
scripts\run_prod.bat       # Windows

# Or manually
ENV=production poetry run python -m nomus.main
```

**Legacy method (uses development by default):**
```bash
poetry run python -m nomus.main
# or in virtual environment:
nomus
```

## Development

The source code is located in `src/nomus`.