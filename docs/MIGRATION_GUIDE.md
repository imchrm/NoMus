# Environment Management Migration Guide

## Что изменилось

Проект был реорганизован для поддержки нескольких окружений (development, staging, production).

### Новая структура файлов

```
NoMus/
├── config/                           # НОВАЯ директория
│   ├── environments/
│   │   ├── development.yaml         # Настройки для разработки
│   │   ├── staging.yaml             # Настройки для staging
│   │   └── production.yaml          # Настройки для production
│   └── localization/
│       └── messages.yaml            # Сообщения локализации (перемещено)
│
├── scripts/                          # НОВАЯ директория
│   ├── run_dev.sh / run_dev.bat
│   ├── run_staging.sh / run_staging.bat
│   └── run_prod.sh / run_prod.bat
│
├── src/nomus/
│   ├── config/
│   │   ├── environment.py           # НОВЫЙ: Enum для окружений
│   │   └── settings.py              # ОБНОВЛЕН: Поддержка окружений
│   │
│   └── infrastructure/
│       └── factory.py                # НОВЫЙ: Фабрика для сервисов
│
├── .env.example                      # НОВЫЙ: Шаблон переменных
└── .env                              # Локальный файл (не в git)
```

## Основные изменения

### 1. Система окружений

Теперь приложение поддерживает 3 окружения:

- **Development**: Разработка (по умолчанию)
  - In-memory БД
  - Stub-сервисы для SMS и платежей
  - DEBUG логирование

- **Staging**: Тестирование перед релизом
  - PostgreSQL (когда реализуется)
  - Реальные сервисы в тестовом режиме
  - INFO логирование

- **Production**: Боевое окружение
  - PostgreSQL (когда реализуется)
  - Реальные сервисы
  - WARNING логирование
  - Мониторинг

### 2. Конфигурационные файлы

#### Секреты (.env)
```bash
ENV=development
BOT_TOKEN=your_token
API_KEY=your_key
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
```

#### Настройки окружения (YAML)
```yaml
# config/environments/development.yaml
logging:
  level: DEBUG
database:
  type: memory
services:
  sms:
    type: stub
  payment:
    type: stub
```

### 3. Фабрика сервисов

Создание сервисов теперь централизовано в `ServiceFactory`:

```python
from nomus.infrastructure.factory import ServiceFactory

# Автоматически создает правильные реализации
storage = ServiceFactory.create_storage(settings)
sms = ServiceFactory.create_sms_service(settings)
payment = ServiceFactory.create_payment_service(settings)
```

### 4. Обновленный Settings

Класс `Settings` теперь загружает конфигурацию из нескольких источников:

1. `.env` файл (секреты)
2. `config/environments/{ENV}.yaml` (настройки окружения)
3. `config/localization/messages.yaml` (локализация)

## Как использовать

### Запуск в разных окружениях

**Development:**
```bash
./scripts/run_dev.sh           # Linux/MacOS
scripts\run_dev.bat            # Windows
```

**Staging:**
```bash
./scripts/run_staging.sh
scripts\run_staging.bat
```

**Production:**
```bash
./scripts/run_prod.sh
scripts\run_prod.bat
```

### Ручной запуск

```bash
# Установить окружение
export ENV=development  # Linux/MacOS
set ENV=development     # Windows

# Запустить
poetry run python -m nomus.main
```

## Миграция существующего кода

### Если у вас уже был .env файл

1. Добавьте в начало: `ENV=development`
2. Остальные переменные остаются без изменений

### Если вы изменяли configuration.yaml

Теперь этот файл находится в `config/localization/messages.yaml`
Старый файл остался для обратной совместимости.

## Что делать дальше

1. **Для development**: Ничего! Все работает из коробки
2. **Для staging**: Настроить PostgreSQL и реальные сервисы (TODO)
3. **Для production**: Настроить мониторинг, секреты, и деплой

## Обратная совместимость

- ✅ Старый `configuration.yaml` все еще работает (fallback)
- ✅ Если ENV не указан, используется `development`
- ✅ Существующий код работает без изменений

## Проверка работоспособности

```bash
# Проверить настройки
poetry run python -c "from nomus.config.settings import Settings; s = Settings(); print(f'Env: {s.env.value}, DB: {s.database.type}')"

# Должно вывести:
# Env: development, DB: memory
```

## Часто задаваемые вопросы

**Q: Где хранить секреты?**
A: В `.env` файле (не коммитить в git!)

**Q: Как добавить новое окружение?**
A: Создать `config/environments/имя.yaml` и запустить с `ENV=имя`

**Q: Можно ли переопределить настройки локально?**
A: Да, создать `config/environments/development.local.yaml` (игнорируется git)

**Q: Как переключаться между окружениями в коде?**
A: `settings.is_development()`, `settings.is_staging()`, `settings.is_production()`

## Поддержка

При возникновении проблем проверьте:
1. Установлен ли ENV правильно
2. Существуют ли конфигурационные файлы
3. Правильно ли заполнен .env

Для отладки запустите:
```bash
ENV=development poetry run python -c "from nomus.config.settings import Settings; Settings()"
```
