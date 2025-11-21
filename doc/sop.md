##The Structure of Project (Src Layout)
##Структура проекта

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
        │   └── settings.py
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
                ├── handlers/
                │   ├── __init__.py
                │   ├── common.py
                │   ├── registration.py
                │   └── ordering.py
                ├── keyboards/
                │   ├── __init__.py
                │   ├── reply.py
                │   └── inline.py
                ├── lexicon/
                │   ├── __init__.py
                │   └── ru.py
                └── states/
                    ├── __init__.py
                    └── user_states.py

##Описание

