# NoMus

## Структура проекта (Src Layout)

```struct
NoMus/
├── .env
├── .gitignore
├── README.md
├── pyproject.toml          # Ваш конфиг с packages = [{include = "nomus", from = "src"}]
├── poetry.lock
│
└── src/
    └── nomus/              # Основной пакет приложения
        ├── __init__.py
        ├── main.py         # Точка входа (теперь запускается как модуль)
        │
        ├── config/
        │   ├── __init__.py
        │   └── settings.py # Конфигурация и тексты (I18nConfig)
        │
        ├── domain/         # (DDD) Сущности и бизнес-правила
        │   ├── __init__.py
        │   ├── entities/
        │   │   ├── __init__.py
        │   │   ├── user.py
        │   │   └── order.py
        │   └── interfaces/ # Абстракции (Protocols)
        │       ├── __init__.py
        │       ├── repo_interface.py
        │       └── sms_interface.py
        │
        ├── infrastructure/ # (DDD) Реализация заглушек для PoC [cite: 124]
        │   ├── __init__.py
        │   ├── database/
        │   │   ├── __init__.py
        │   │   └── memory_storage.py # Хранение данных в памяти (dict) [cite: 159]
        │   └── services/
        │       ├── __init__.py
        │       ├── sms_stub.py       # Заглушка SMS [cite: 155]
        │       └── payment_stub.py   # Заглушка платежей [cite: 156]
        │
        ├── application/    # (DDD) Сценарии использования
        │   ├── __init__.py
        │   └── services/
        │       ├── __init__.py
        │       ├── auth_service.py   # Логика регистрации
        │       └── order_service.py  # Логика создания заказа [cite: 151]
        │
        └── presentation/   # (MVC)
            ├── __init__.py
            ├── api/        # Бэкенд API (FastAPI/Flask) [cite: 123]
            │   ├── __init__.py
            │   ├── app.py
            │   └── routes/
            │       ├── __init__.py
            │       ├── register.py   # Эндпоинт /register [cite: 143]
            │       └── orders.py     # Эндпоинт /create_order [cite: 148]
            │
            └── bot/        # Telegram-бот (aiogram) [cite: 122]
                ├── __init__.py
                ├── loader.py
                ├── filters/
                │   ├── __init__.py
                │   └── ...
                ├── handlers/
                │   ├── __init__.py
                │   ├── common.py
                │   ├── language.py   # Выбор языка и соглашения
                │   ├── registration.py
                │   └── ordering.py
                ├── keyboards/
                │   ├── __init__.py
                │   ├── reply.py
                │   └── inline.py
                ├── middlewares/      # Промежуточное ПО
                │   ├── __init__.py
                │   ├── dependency_injection.py
                │   └── l10n_middleware.py
                └── states/
                    ├── __init__.py
                    └── user_states.py
```

## Описание
Разбор архитектуры по слоям

1. Domain (Домен) — "Чистая модель"

Здесь описано, что такое наш бизнес, не думая о базах данных или ботах.

    Пример: Класс Order содержит поля address, tariff, status. Здесь же правила: "нельзя создать заказ без тарифа".

    DDD: Этот слой не зависит ни от чего внешнего (декомпозиция).

2. Application (Приложение) — "Сценарии"

Логика процессов, описанных в PoC.

    Файл auth_service.py: Содержит функцию register_user. Она вызывает sms_stub.send() и сохраняет пользователя через репозиторий.

    Связь с PoC: Именно этот слой реализует требования "Принимает номер -> Вызывает заглушку SMS -> Пишет в лог".

3. Infrastructure (Инфраструктура) — "Реализация заглушек"

Критически важный слой (PoC). Здесь создаются фейковые сервисы, как указано в ТЗ.

    database/memory_storage.py: Вместо PostgreSQL мы используем здесь словарь dict() или список в оперативной памяти, который сбрасывается при перезапуске.

services/sms_stub.py: Функция, которая просто пишет в консоль [INFO] SMS code sent... и возвращает True.

services/payment_stub.py: Функция с time.sleep(1) для имитации задержки банка.

4. Presentation (Представление) — Бот и API

Этот слой отвечает за ввод/вывод. В нашей задаче две точки входа:

A. Telegram Bot (src/presentation/bot/) Реализация MVC внутри aiogram:

    Controller (handlers/): Ловит сообщение от пользователя (например, введенный код SMS, выбор языка, принятие соглашения).
    Включает в себя обработчики для регистрации (registration.py), заказов (ordering.py) и языковых настроек (language.py).

    Model: Хендлер передает данные в Application слой (отправляет запрос на бэкенд/сервис).

    View (keyboards/ и config/settings.py): Бот отправляет ответ, используя заготовленные тексты (из Settings, загружаемых из YAML) и клавиатуры (например, кнопку "Оплатить 30000 сум.").

    Middlewares: Промежуточные слои для внедрения зависимостей (DI) и локализации (L10n).

B. API Service (src/presentation/api/) Согласно плану PoC, у нас должен быть отдельный веб-сервис (бэкенд), который принимает запросы.

    В папке api/routes/ мы реализуем эндпоинты /register и /create_order.

### Важный момент: Бот может общаться с этим API по HTTP (как с внешним сервисом) или, если они в одном приложении, вызывать сервисный слой (Application) напрямую. Для чистоты эксперимента PoC (проверка архитектуры) лучше, чтобы бот делал HTTP-запросы к API, как указано в схеме.
