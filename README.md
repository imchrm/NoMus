# NoMus

**Telegram-бот для заказа услуг массажа на дом**

NoMus — Telegram-бот (aiogram 3.x), интегрированный с backend NMservices (FastAPI + PostgreSQL). Пользователь регистрируется, выбирает услугу из каталога, указывает адрес и получает уведомления о статусе заказа. Администратор управляет услугами, заказами и пользователями через Admin Panel (React).

---

## Функционал

### Для пользователя (Telegram-бот)

| Сценарий | Описание |
|----------|----------|
| **Регистрация** | Выбор языка (🇺🇿 🇬🇧 🇷🇺) → Пользовательское соглашение → Геолокация → Телефон (share contact) → SMS-код → Готово |
| **Создание заказа** | 🛒 Сделать заказ → Каталог услуг из API (inline-кнопки) → Ввод адреса → Summary + [Подтвердить] / [Отмена] → «Заказ #N создан!» |
| **Мои заказы** | 📋 Мои заказы → Текстовый список активных заказов (номер, услуга, сумма, адрес, статус) |
| **Настройки** | ⚙️ Настройки → Язык / Профиль / О сервисе |
| **Уведомления** | Push при смене статуса заказа + Pull при заходе в бот (пропущенные уведомления) |

**Главная клавиатура:**
```
Незарегистрированный:       Зарегистрированный:
┌─────────────────────┐    ┌─────────────────────┐
│ Регистрация         │    │ 🛒 Сделать заказ     │
│ ⚙️ Настройки        │    │ 📋 Мои заказы        │
└─────────────────────┘    │ ⚙️ Настройки         │
                           └─────────────────────┘
```

**Команды:** `/start`, `/cancel`, `/language`

### Для администратора (Admin Panel)

| Раздел | Возможности |
|--------|-------------|
| **Dashboard** | Статистика: пользователи, заказы, услуги; заказы по статусам |
| **Услуги** | CRUD + деактивация (soft delete), фильтрация, сортировка |
| **Заказы** | CRUD, фильтр по статусу/дате/user_id, смена статуса → push-уведомление |
| **Пользователи** | Список, поиск по ID/телефону, expand-панель с заказами |

---

## Архитектура

```
┌──────────────────────────────────────────┐
│ NoMus Bot (Telegram)                     │
│  ├─ DDD: Domain → Application →         │
│  │       Infrastructure → Presentation   │
│  ├─ FSM (aiogram): регистрация, заказ    │
│  ├─ L10nMiddleware: ru / uz / en         │
│  ├─ NotificationMiddleware: pull-on-visit│
│  └─ RemoteApiClient (httpx)              │
│     ├─ POST /users/register              │
│     ├─ GET  /services                    │
│     ├─ POST /orders                      │
│     ├─ GET  /orders/active               │
│     ├─ GET  /orders/pending-notifications│
│     └─ POST /orders/notifications/ack    │
└──────────────┬───────────────────────────┘
               │ HTTP (X-API-Key)
┌──────────────▼───────────────────────────┐
│ NMservices (Backend)                     │
│  ├─ FastAPI + uvicorn                    │
│  ├─ SQLAlchemy 2.0 (async) + Alembic    │
│  ├─ TelegramNotifier (push → Bot API)   │
│  └─ PostgreSQL                           │
│     ├─ users                             │
│     ├─ services                          │
│     └─ orders (status, notified_status)  │
└──────────────▲───────────────────────────┘
               │ HTTP (X-Admin-Key)
┌──────────────┴───────────────────────────┐
│ NMservices-Admin (React)                 │
│  ├─ react-admin + Vite + TypeScript      │
│  └─ Dashboard, Services, Orders, Users   │
└──────────────────────────────────────────┘
```

**Важно**: Бот **не подключается к PostgreSQL напрямую**. Вся работа с БД — через REST API NMservices.

---

## Структура проекта

```
NoMus/
├── config/
│   ├── environments/              # Конфигурации окружений
│   │   ├── development.yaml       #   stub-сервисы, memory storage
│   │   ├── development-remote.yaml#   remote API, memory cache
│   │   ├── staging.yaml
│   │   └── production.yaml
│   └── localization/
│       └── messages.yaml          # ~45 ключей × 3 языка
│
├── docs/
│   ├── bot_flow.md                # Детальный программный flow бота
│   ├── tasks/MVP_PLAN.md          # Глобальный план + текущий функционал
│   ├── DDD_Analysis.md            # Анализ DDD архитектуры
│   └── ...
│
├── src/nomus/
│   ├── main.py                    # Точка входа (BotApplication)
│   ├── config/                    # Settings, Messages, Environment
│   ├── domain/                    # Entities (User, Order), Interfaces
│   ├── application/               # Services (Auth, Order, Language)
│   ├── infrastructure/            # Storage (Memory, Remote), API client, SMS/Payment stubs
│   └── presentation/
│       └── bot/
│           ├── handlers/          # common, registration, ordering, settings, my_order
│           ├── states/            # LanguageStates, RegistrationStates, OrderStates
│           ├── middlewares/       # L10n, Notification, DI
│           └── filters/           # EmojiPrefixEquals, TextEquals
│
├── tests/
├── .env.example
├── pyproject.toml                 # Poetry
└── CLAUDE.md
```

---

## Быстрый старт

### 1. Установка

```bash
git clone https://github.com/imchrm/NoMus.git
cd NoMus
poetry config virtualenvs.in-project true
poetry install
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```bash
ENV=development-remote          # или development (без API)
BOT_TOKEN=your_bot_token_here   # от @BotFather
REMOTE_API_BASE_URL=http://192.168.1.191:8000
REMOTE_API_KEY=your_api_key_here
SKIP_REGISTRATION=False         # True — пропустить регистрацию для тестирования
```

### 3. Запуск

```bash
# С локальными stub-сервисами (без NMservices)
ENV=development poetry run python -m nomus.main

# С удалённым NMservices API
ENV=development-remote poetry run python -m nomus.main
```

---

## Окружения

| Режим | Storage | SMS | Payment | Logging |
|-------|---------|-----|---------|---------|
| `development` | MemoryStorage | Stub (код 1234) | Stub | DEBUG |
| `development-remote` | RemoteStorage → API | Remote | Remote | DEBUG |
| `staging` | RemoteStorage → API | Real (test) | Real (test) | INFO |
| `production` | RemoteStorage → API | Real | Real | WARNING + Sentry |

Каждое окружение имеет YAML файл в `config/environments/`.

---

## Конфигурация

### Переменные окружения (.env)

| Переменная | Назначение |
|------------|------------|
| `ENV` | Окружение: `development`, `development-remote`, `staging`, `production` |
| `DEBUG` | Debug-режим |
| `BOT_TOKEN` | Токен Telegram бота |
| `REMOTE_API_BASE_URL` | Адрес NMservices API |
| `REMOTE_API_KEY` | Ключ авторизации API |
| `SKIP_REGISTRATION` | Пропуск регистрации для тестирования |
| `SENTRY_DSN` | DSN для мониторинга ошибок (production) |

### YAML конфигурации

Файлы в `config/environments/` определяют: тип хранилища, сервисы (SMS, Payment), параметры логирования, настройки бота и API.

---

## Тестирование

```bash
# Проверка окружения
poetry run python tests/manual/test_env_check.py

# Тест подключения к NMservices API
poetry run python tests/manual/test_api_connection.py

# Все тесты
pytest tests/
```

---

## Локализация

3 языка: 🇷🇺 Русский (ru), 🇺🇿 Узбекский (uz), 🇬🇧 Английский (en)

Все тексты — в `config/localization/messages.yaml` (~45 ключей). Pydantic-модель `Messages` валидирует полноту переводов.

---

## Технологический стек

- **Python 3.11+**, **aiogram 3.x** — Telegram Bot Framework
- **httpx** — Асинхронный HTTP-клиент
- **pydantic-settings** — Конфигурация с валидацией
- **Poetry** — Управление зависимостями
- **pytest** — Тестирование

---

## Документация

- [CLAUDE.md](./CLAUDE.md) — Документация для разработки с Claude Code
- [docs/bot_flow.md](./docs/bot_flow.md) — Программный flow бота (от /start до создания заказа)
- [docs/tasks/MVP_PLAN.md](./docs/tasks/MVP_PLAN.md) — Глобальный план MVP + текущий функционал системы
- [docs/DDD_Analysis.md](./docs/DDD_Analysis.md) — Анализ DDD архитектуры

---

## Контакты

- **GitHub**: [imchrm/NoMus](https://github.com/imchrm/NoMus)
- **Issues**: [Сообщить о проблеме](https://github.com/imchrm/NoMus/issues)

---

**Последнее обновление**: 2026-02-25
