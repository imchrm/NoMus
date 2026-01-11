# NoMus Project - Claude Code Guide

## Обзор проекта

**NoMus** — это Telegram-бот для заказа услуг, интегрированный с backend-системой NMservices.

### Компоненты экосистемы
- **NoMus** (этот репозиторий) - Telegram-бот на aiogram 3.x
- **NMservices** - Backend сервер (uvicorn + FastAPI) - адрес в переменной `REMOTE_API_BASE_URL`
- **PostgreSQL** - База данных 'nomus' (в разработке, пока используется MemoryStorage)

### Версия
- **Версия проекта:** 0.4.1
- **Python:** 3.11+
- **Архитектура:** DDD (Domain-Driven Design) монолит

---

## Архитектура

Проект использует **DDD архитектуру** с четкой слоистостью:

```
src/nomus/
├── domain/           # Доменный слой - сущности и интерфейсы
├── application/      # Прикладной слой - бизнес-логика
├── infrastructure/   # Инфраструктурный слой - внешние сервисы, БД
└── presentation/     # Слой представления - Telegram-бот, API
```

### Ключевые принципы
- **Инверсия зависимостей**: Domain не зависит от Infrastructure
- **Protocols вместо абстрактных классов**: `ISmsService`, `IPaymentService`, `IStorageRepository`
- **Factory Pattern**: `ServiceFactory` создает сервисы в зависимости от окружения
- **Dependency Injection**: через middleware и параметры handlers

---

## Структура кодовой базы

### Основные директории

```
NoMus/
├── config/                           # Конфигурация окружений и локализация
│   ├── environments/                 # development.yaml, staging.yaml, production.yaml
│   └── localization/                 # messages.yaml (ru, uz, en)
│
├── scripts/                          # Скрипты запуска для разных окружений
│
├── src/nomus/                        # Основной код приложения
│   ├── main.py                       # Точка входа - BotApplication
│   ├── config/                       # Settings, конфигурация
│   ├── domain/                       # Entities: User, Order | Interfaces
│   ├── application/                  # AuthService, OrderService
│   ├── infrastructure/               # API clients, DB storage, SMS/Payment services
│   └── presentation/                 # Bot handlers, states, keyboards, middlewares
│
├── test/                             # Тесты pytest
│   ├── config/, domain/, infrastructure/, presentation/
│   └── manual/                       # Ручные тесты регистрационного потока
│
└── doc/                              # Документация
    ├── bot_flow.md                   # Детальный поток выполнения
    ├── DDD_Analysis.md               # Анализ архитектуры
    └── sop.md                        # Standard Operating Procedures
```

### Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `src/nomus/main.py` | Точка входа, BotApplication класс |
| `src/nomus/config/settings.py` | Конфигурация приложения (Pydantic Settings) |
| `src/nomus/application/services/auth_service.py` | Регистрация, SMS верификация |
| `src/nomus/application/services/order_service.py` | Создание заказов, выбор тарифов |
| `src/nomus/infrastructure/services/remote_api_client.py` | HTTP клиент для NMservices API |
| `src/nomus/presentation/bot/handlers/` | Обработчики команд бота |
| `config/environments/*.yaml` | Конфигурация по окружениям |
| `config/localization/messages.yaml` | Многоязычные сообщения |

---

## Технологический стек

### Основные библиотеки (pyproject.toml)

```toml
dependencies = [
    "aiogram>=3.22.0",              # Telegram Bot Framework
    "pydantic-settings>=2.0.0",     # Конфигурация через Settings
    "pyyaml>=6.0.3",                # YAML конфиги
    "httpx>=0.27.0",                # Асинхронный HTTP-клиент
    "pytest>=9.0.2",                # Тестирование
]
```

### Технологии
- **Python 3.11+** - язык программирования
- **aiogram 3.x** - Telegram Bot API framework
- **async/await** - асинхронное программирование (все I/O операции асинхронны)
- **Pydantic** - валидация данных и конфигурация
- **httpx** - HTTP-клиент для интеграции с NMservices
- **PyYAML** - конфигурационные файлы
- **pytest** - модульное и интеграционное тестирование
- **Poetry** - управление зависимостями

---

## База данных и модели

### Текущее состояние
- **В разработке**: `MemoryStorage` (in-memory словари)
- **Планируется**: PostgreSQL с SQLAlchemy/Alembic

### Сущности (Domain Entities)

#### User (`domain/entities/user.py`)
```python
class User(BaseModel):
    id: int
    telegram_id: int              # Telegram User ID
    phone_number: str             # +998901234567
    registered_at: datetime
    latitude: float | None        # Геолокация
    longitude: float | None
    server_user_id: int | None    # ID пользователя на NMservices
```

#### Order (`domain/entities/order.py`)
```python
@dataclass
class Order:
    id: int
    user_id: int
    amount: int
    created_at: datetime
    status: str  # 'pending', 'completed', 'cancelled'
```

### Репозитории (IStorageRepository)

**Методы для пользователей:**
- `save_or_update_user(telegram_id, data)`
- `get_user_by_telegram_id(telegram_id)`
- `get_user_by_phone(phone)`
- `update_user_language(telegram_id, language_code)`
- `get_user_language(telegram_id)`
- `delete_user(telegram_id)`

**Методы для заказов:**
- `save_or_update_order(order_id, data)`
- `get_order_by_id(order_id)`
- `get_order_status(order_id)`
- `get_orders_by_user(telegram_id)`
- `update_order_status(order_id, status)`

---

## Интеграция с NMservices

### API Configuration
- **Base URL**: Устанавливается через `REMOTE_API_BASE_URL` в .env
- **API Key**: Устанавливается через `REMOTE_API_KEY` в .env
- **Authentication**: `X-API-Key` header
- **Timeout**: 30s (настраивается в settings)
- **Max Retries**: 3 (настраивается в settings)
- **Retry Delay**: 1s (настраивается в settings)

### API Endpoints

#### 1. SMS Service - Регистрация пользователя
```
POST /users/register
Request:  { "phone_number": "+998901234567" }
Response: { "status": "ok", "user_id": 123 }
```

#### 2. Payment Service - Создание заказа
```
POST /orders
Request:  { "user_id": 123, "tariff_code": "standard_300" }
Response: { "status": "ok", "order_id": 456 }
```

### Компоненты интеграции

| Компонент | Файл | Назначение |
|-----------|------|-----------|
| `RemoteApiClient` | `infrastructure/services/remote_api_client.py` | Базовый HTTP клиент с retry логикой |
| `SmsServiceRemote` | `infrastructure/services/sms_remote.py` | Отправка SMS через NMservices |
| `PaymentServiceRemote` | `infrastructure/services/payment_remote.py` | Обработка платежей через NMservices |
| `RemoteStorage` | `infrastructure/database/remote_storage.py` | Кеш с синхронизацией данных |

### server_user_id Flow (ВАЖНО!)

```
1. Пользователь отправляет номер телефона
   ↓
2. AuthService.send_verification_code() → SmsServiceRemote.send_sms()
   ↓
3. NMservices API возвращает user_id
   ↓
4. user_id сохраняется в User.server_user_id
   ↓
5. При создании заказа OrderService использует server_user_id
   ↓
6. PaymentServiceRemote отправляет заказ с server_user_id на API
```

**Файлы с server_user_id:**
- `domain/entities/user.py:9` - поле в сущности
- `application/services/auth_service.py` - получение при регистрации
- `application/services/order_service.py` - использование при заказе
- `presentation/bot/handlers/registration.py` - сохранение в БД

### Обработка ошибок API

```python
RemoteApiAuthError        # 401/403 - проблемы с API ключом
RemoteApiValidationError  # 400/422 - некорректные данные
RemoteApiConnectionError  # сетевые проблемы, таймауты
```

---

## Конфигурация и окружения

### Переменные окружения (.env)

```bash
# Выбор окружения (важно!)
ENV=development | development-remote | staging | production

# Debug режим
DEBUG=True | False

# Telegram Bot
BOT_TOKEN=<token_from_BotFather>

# Remote API (NMservices)
REMOTE_API_BASE_URL=<your_nmservices_url>
REMOTE_API_KEY=<your_api_key>

# Database (для staging/production)
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password

# Development Options
SKIP_REGISTRATION=False | True   # Пропустить регистрацию для быстрого тестирования

# Monitoring
SENTRY_DSN=<sentry_url>
```

### YAML конфигурации

#### `config/environments/development.yaml`
```yaml
database:
  type: memory              # In-memory хранилище
services:
  sms:
    type: stub              # Эмуляция SMS (без реального API)
  payment:
    type: stub              # Эмуляция платежей
remote_api:
  enabled: false            # Отключен Remote API
logging:
  level: DEBUG
```

#### `config/environments/development-remote.yaml`
```yaml
database:
  type: memory
services:
  sms:
    type: remote            # Использует NMservices API
  payment:
    type: remote
remote_api:
  enabled: true
  base_url: "${REMOTE_API_BASE_URL}"
  api_key: "${REMOTE_API_KEY}"
```

### Запуск в разных окружениях

```bash
# Development (stub сервисы)
poetry run python scripts/run_dev.py
# или
ENV=development poetry run python -m nomus.main

# Development с Remote API
ENV=development-remote poetry run python -m nomus.main

# Staging
ENV=staging poetry run python -m nomus.main

# Production
ENV=production poetry run python -m nomus.main
```

---

## Bot Handlers и Flow

### Основные команды

#### `/start` - Старт бота
```
common.py:start_command()
  ├─ Проверка пользователя в БД
  ├─ DEV MODE: SKIP_REGISTRATION=True → сразу в меню
  └─ Выбор языка или главное меню
```

#### `/cancel` - Отмена текущей операции
```
common.py:cancel_command()
  └─ Очищение FSM состояния, возврат в главное меню
```

### Callback Handlers

```python
lang_ru / lang_uz / lang_en    # Выбор языка
agree_terms                    # Принятие пользовательского соглашения
```

### Процесс регистрации (`registration.py`)

```
1. start_registration()
   ↓ Запрос геолокации
2. process_location()
   ↓ Сохранение координат, запрос контакта
3. process_phone()
   ↓ Отправка SMS с кодом → получение server_user_id
4. process_code()
   ↓ Проверка кода, сохранение пользователя
5. Переход к выбору тарифа
```

**FSM States:**
- `RegistrationStates.waiting_for_location`
- `RegistrationStates.waiting_for_phone`
- `RegistrationStates.waiting_for_sms_code`

### Процесс заказа (`ordering.py`)

```
1. start_ordering()
   ↓ Проверка регистрации пользователя
2. _start_tariff_selection()
   ↓ Показ доступных тарифов
3. process_tariff()
   ↓ Выбор тарифа пользователем
4. process_payment()
   ↓ Обработка платежа через PaymentService
5. Подтверждение заказа
```

**FSM States:**
- `OrderStates.selecting_tariff`
- `OrderStates.waiting_for_payment`

**Маппинг тарифов:**
```python
# Локализованное название → код API
"Эконом" / "Economy" / "Iqtisodiyot" → "economy_100"
"Стандарт" / "Standard"              → "standard_300"
"Премиум" / "Premium"                → "premium_500"
```

### Middlewares

**`L10nMiddleware`** (`presentation/bot/middlewares/l10n_middleware.py`)
- Определяет язык пользователя из БД
- Внедряет объект `Messages` с локализованными текстами в handler
- Fallback на английский при отсутствии языка

**`DependencyInjectionMiddleware`**
- Внедряет сервисы (AuthService, OrderService, Storage) в handlers

### Filters

**`TextEquals`** (`presentation/bot/filters/text_equals.py`)
```python
# Динамическая фильтрация по локализованному тексту кнопки
TextEquals("registration_button")  # Проверяет текст на всех языках
```

---

## Локализация (i18n)

### Структура

```yaml
# config/localization/messages.yaml
messages:
  ru:
    welcome: "Добро пожаловать!"
    registration_button: "Регистрация"
  uz:
    welcome: "Xush kelibsiz!"
    registration_button: "Ro'yxatdan o'tish"
  en:
    welcome: "Welcome!"
    registration_button: "Registration"
```

### Использование в коде

```python
# В handler через dependency injection
async def some_handler(message: Message, messages: Messages):
    await message.answer(messages.welcome)
    # Автоматически подставляется текст на языке пользователя
```

### Поддерживаемые языки
- 🇷🇺 Русский (ru)
- 🇺🇿 Узбекский (uz)
- 🇬🇧 Английский (en)

---

## Тестирование

### Структура тестов

```
test/
├── config/              # Тесты конфигурации
├── domain/              # Тесты доменных интерфейсов
├── infrastructure/      # Тесты удаленных сервисов
├── presentation/        # Тесты локализации
└── manual/              # Ручные тесты регистрации
    ├── test_registration_flow.py     # Русский
    └── test_registration_flow_en.py  # Английский
```

### Запуск тестов

```bash
# Все тесты
pytest test/

# С подробным выводом
pytest -v test/

# Конкретный файл
pytest test/infrastructure/test_remote_services.py

# С coverage
pytest --cov=src/nomus test/
```

---

## Соглашения о коде (Code Style)

### Naming Conventions

```python
# Classes: PascalCase
class MemoryStorage, AuthService, BotApplication

# Functions & methods: snake_case
def send_verification_code(), process_payment()

# Constants: UPPER_SNAKE_CASE
DEF_SELECT_LANG_RU = "Выбрать язык"

# Private methods: leading underscore
def _get_api_client(), _start_tariff_selection()

# Protocols (interfaces): I prefix
class ISmsService, IPaymentService, IStorageRepository
```

### Type Hints

```python
# Обязательны для всех функций и методов
async def get_user(telegram_id: int) -> User | None:
    ...

# Union types - Python 3.10+ синтаксис
def save_user(user_id: int | str) -> bool:
    ...

# Protocol для интерфейсов
class IRepository(Protocol):
    def save(self, data: dict) -> None: ...
```

### Async/Await

```python
# ВСЕ I/O операции должны быть async
async def send_sms(phone: str) -> None:        # ✅
async def process_payment(user_id: int):       # ✅

# Синхронные функции только для чистой логики
def calculate_total(amount: int) -> int:       # ✅
```

### Logging

```python
# В начале каждого модуля
import logging
logger = logging.getLogger(__name__)

# Уровни: DEBUG, INFO, WARNING, ERROR
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

### Imports

```python
# Порядок импортов:
# 1. Стандартная библиотека
import logging
from datetime import datetime

# 2. Сторонние библиотеки
from aiogram import Router, F
from pydantic import BaseModel

# 3. Локальные импорты
from nomus.domain.entities.user import User
from nomus.application.services.auth_service import AuthService
```

---

## Важные паттерны и практики

### 1. Dependency Injection

```python
# Через параметры handler
async def start_handler(
    message: Message,
    state: FSMContext,
    messages: Messages,           # Внедряется через L10nMiddleware
    auth_service: AuthService,    # Внедряется через DI middleware
    storage: IStorageRepository
):
    ...
```

### 2. Factory Pattern

```python
# ServiceFactory создает сервисы на основе конфигурации
factory = ServiceFactory(settings)
sms_service = factory.create_sms_service()      # stub или remote
payment_service = factory.create_payment_service()
```

### 3. Strategy Pattern

```python
# Разные реализации одного интерфейса
class ISmsService(Protocol):
    async def send_sms(self, phone: str) -> int: ...

class SmsServiceStub(ISmsService):      # Для development
class SmsServiceRemote(ISmsService):    # Для production
```

### 4. Repository Pattern

```python
# Абстракция хранения данных
class IStorageRepository(Protocol):
    def save_or_update_user(...): ...
    def get_user_by_telegram_id(...): ...

class MemoryStorage(IStorageRepository):    # Текущая
class PostgresStorage(IStorageRepository):  # Планируется
```

---

## Для Claude Code: Важные правила

### ✅ ВСЕГДА делать

1. **Читать файлы перед изменением** - НИКОГДА не предлагать изменения без чтения кода
2. **Проверять типы данных** - особенно при работе с API NMservices
3. **Обрабатывать ошибки** - все handler'ы должны иметь try/except
4. **Использовать async/await** - для всех I/O операций
5. **Добавлять type hints** - для новых функций и методов
6. **Логировать важные события** - регистрация, заказы, ошибки API
7. **Следовать DDD архитектуре** - не смешивать слои
8. **Тестировать новый функционал** - писать pytest тесты
9. **Обновлять локализацию** - при добавлении новых сообщений (ru, uz, en)
10. **Проверять server_user_id flow** - критически важен для интеграции

### ❌ НИКОГДА не делать

1. **Не хардкодить токены и секреты** - только через .env
2. **Не изменять схему БД без миграции** - когда будет Alembic
3. **Не блокировать event loop** - никаких sync вызовов в async коде
4. **Не пропускать обработку ошибок** - особенно в handlers
5. **Не нарушать инверсию зависимостей** - Domain не должен знать об Infrastructure
6. **Не коммитить .env файлы** - только .env.example
7. **Не использовать прямые SQL запросы** - только через Repository
8. **Не добавлять функционал без тестов** - pytest обязателен
9. **Не игнорировать локализацию** - все тексты через messages.yaml
10. **Не забывать про SKIP_REGISTRATION** - удобно для тестирования

### ⚠️ Критически важно

**server_user_id flow:**
```python
# 1. Получение при регистрации
user_id = await sms_service.send_sms(phone)  # Возвращает server_user_id
user_data["server_user_id"] = user_id        # Сохранить!

# 2. Использование при заказе
user = storage.get_user_by_telegram_id(telegram_id)
await payment_service.process_payment(
    user_id=user.server_user_id  # Не telegram_id!
)
```

**Окружения:**
- `development` - stub сервисы, без API
- `development-remote` - интеграция с NMservices API
- `staging` / `production` - боевые окружения

**Async контекст:**
```python
# ✅ Правильно
async def handler():
    result = await async_function()

# ❌ Неправильно
async def handler():
    result = sync_blocking_function()  # Блокирует event loop!
```

---

## Development Workflow

### Быстрый старт

```bash
# 1. Установка зависимостей
poetry install

# 2. Копирование .env
cp .env.example .env

# 3. Настройка .env
BOT_TOKEN=your_token_here
ENV=development
SKIP_REGISTRATION=True  # Для быстрого тестирования

# 4. Запуск бота
poetry run python -m nomus.main
```

### Тестирование с NMservices

```bash
# 1. Настройка для remote API в .env
ENV=development-remote
REMOTE_API_BASE_URL=<your_nmservices_url>
REMOTE_API_KEY=<your_api_key>

# 2. Запуск
poetry run python -m nomus.main

# 3. Проверка health (замените на ваш URL)
curl <your_nmservices_url>/health
```

### Debugging

```bash
# Включить DEBUG логирование
DEBUG=True
# В config/environments/development.yaml:
logging:
  level: DEBUG
```

### Ручное тестирование

```bash
# Запустить ручной тест регистрации
poetry run python test/manual/test_registration_flow.py
```

---

## Roadmap / Планы развития

- [x] Интеграция с NMservices (регистрация, заказы)
- [x] Pytest тесты
- [x] Многоязычность (ru, uz, en)
- [x] FSM для регистрации и заказов
- [ ] Миграция на PostgreSQL + SQLAlchemy
- [ ] Alembic для миграций БД
- [ ] Модульная архитектура (см. DDD_Analysis.md)
- [ ] Расширение функционала заказов
- [ ] Мониторинг (Sentry, метрики)
- [ ] CI/CD pipeline

---

## Полезные ссылки

- **Документация проекта**: `/doc/bot_flow.md`, `/doc/DDD_Analysis.md`
- **aiogram 3.x**: https://docs.aiogram.dev/en/latest/
- **Pydantic Settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **pytest**: https://docs.pytest.org/

---

## Контакты и поддержка

- **Git Repository**: `C:\Users\zum\dev\python\NoMus`
- **Worktree**: `C:\Users\zum\.claude-worktrees\NoMus\vibrant-mendel`
- **Branch**: `vibrant-mendel` → PR в `main`

---

**Последнее обновление**: 2026-01-11
**Версия документа**: 1.0
