# ТЗ: Решения для хранения языка пользователя

## Контекст проблемы

При рестарте бота теряется информация о выбранном языке пользователя, так как:
- `language_code` хранится только в локальном кеше бота (`MemoryStorage`)
- Сервер NMservices не хранит язык пользователя
- При загрузке данных с сервера поле `language_code` отсутствует

Текущее временное решение — fallback на русский язык (`"ru"`).

---

## Решение 1: Хранить язык на сервере NMservices

### Цель
Добавить поле `language_code` в таблицу `users` на сервере NMservices, чтобы язык сохранялся между рестартами бота.

### Задачи для NMservices

#### 1.1 Миграция БД
- Добавить поле `language_code VARCHAR(5)` в таблицу `users`
- Поле nullable, default `NULL`
- Допустимые значения: `'ru'`, `'uz'`, `'en'`

```sql
ALTER TABLE users ADD COLUMN language_code VARCHAR(5) DEFAULT NULL;
```

#### 1.2 Обновить модель User
Файл: `src/nmservices/models/user.py`
```python
language_code: str | None = None
```

#### 1.3 Обновить endpoint регистрации
Файл: `src/nmservices/api/routes/users.py`

Endpoint `POST /users/register` должен принимать `language_code`:
```python
class UserRegisterRequest(BaseModel):
    phone_number: str
    telegram_id: int | None = None
    language_code: str | None = None  # Добавить
```

#### 1.4 Добавить endpoint обновления языка
```
PATCH /users/{user_id}/language
Request:  { "language_code": "uz" }
Response: { "status": "ok" }
```

#### 1.5 Обновить endpoint получения пользователя
`GET /users/by-telegram/{telegram_id}` должен возвращать `language_code`:
```json
{
  "id": 12,
  "phone_number": "+998901234567",
  "telegram_id": 192496135,
  "language_code": "ru",
  "created_at": "...",
  "updated_at": "..."
}
```

### Задачи для NoMus

#### 1.6 Обновить flush() для отправки language_code
Файл: `src/nomus/infrastructure/database/remote_storage.py`

При регистрации отправлять `language_code` на сервер.

#### 1.7 Добавить метод update_language_on_server()
```python
async def update_language_on_server(self, user_id: int, language_code: str) -> bool:
    await self._api_client.patch(f"/users/{user_id}/language", {"language_code": language_code})
```

#### 1.8 Обновить update_user_language()
Файл: `src/nomus/infrastructure/database/remote_storage.py`

При смене языка синхронизировать с сервером:
```python
async def update_user_language(self, telegram_id: int, language_code: str) -> None:
    await self._cache.update_user_language(telegram_id, language_code)
    user = await self._cache.get_user_by_telegram_id(telegram_id)
    if user and user.get("id"):
        await self.update_language_on_server(user["id"], language_code)
```

### Критерии приёмки
- [ ] При выборе языка в боте — язык сохраняется на сервере
- [ ] При рестарте бота — язык загружается с сервера
- [ ] API возвращает `language_code` в данных пользователя

---

## Решение 2: Запрашивать язык при отсутствии

### Цель
Если язык не найден в storage, показывать пользователю выбор языка перед продолжением работы.

### Задачи для NoMus

#### 2.1 Создать helper функцию проверки языка
Файл: `src/nomus/presentation/bot/handlers/common.py`

```python
async def ensure_user_language(
    message: Message,
    storage: IUserRepository,
    state: FSMContext
) -> str | None:
    """
    Проверяет наличие языка пользователя.
    Если язык отсутствует — показывает выбор языка и возвращает None.
    Если язык есть — возвращает language_code.
    """
    lang_code = await storage.get_user_language(message.from_user.id)
    if lang_code and lang_code in ["uz", "ru", "en"]:
        return lang_code

    # Язык не найден — показываем выбор
    await state.set_state(LanguageStates.waiting_for_language)
    await state.update_data(return_to="ordering")  # Куда вернуться после выбора
    await _send_language_selection(message)
    return None
```

#### 2.2 Добавить FSM состояние
Файл: `src/nomus/presentation/bot/states/states.py`

```python
class LanguageStates(StatesGroup):
    waiting_for_language = State()
```

#### 2.3 Обновить handler выбора языка
Файл: `src/nomus/presentation/bot/handlers/common.py`

После выбора языка — вернуться к прерванному действию:
```python
@router.callback_query(F.data.startswith("lang_"))
async def process_lang_select(callback: CallbackQuery, storage: IUserRepository, state: FSMContext, settings: Settings):
    # ... сохранение языка ...

    # Проверяем, нужно ли вернуться к прерванному действию
    data = await state.get_data()
    return_to = data.get("return_to")

    if return_to == "ordering":
        await state.clear()
        # Продолжить оформление заказа
        await start_ordering(callback.message, state, ...)
    else:
        # Обычный flow — показать agreement
        ...
```

#### 2.4 Обновить ordering.py
Файл: `src/nomus/presentation/bot/handlers/ordering.py`

```python
async def start_ordering(...):
    lang_code = await ensure_user_language(message, storage, state)
    if lang_code is None:
        return  # Ждём выбора языка

    # Продолжаем оформление заказа
    await _start_tariff_selection(...)
```

### Критерии приёмки
- [ ] Если язык не установлен — показывается выбор языка
- [ ] После выбора языка — пользователь возвращается к прерванному действию
- [ ] Не требуется повторно нажимать кнопки

---

## Решение 3: Использовать язык из Telegram API как fallback

### Цель
Если язык не найден в storage, использовать `message.from_user.language_code` из Telegram API.

### Задачи для NoMus

#### 3.1 Создать helper функцию получения языка
Файл: `src/nomus/application/services/language_service.py` (новый файл)

```python
from aiogram.types import User as TelegramUser

SUPPORTED_LANGUAGES = ["ru", "uz", "en"]
DEFAULT_LANGUAGE = "ru"

async def get_user_language_with_fallback(
    telegram_user: TelegramUser,
    storage: IUserRepository
) -> str:
    """
    Получает язык пользователя с fallback на Telegram API и default.

    Приоритет:
    1. Сохранённый язык в storage
    2. Язык из Telegram API (если поддерживается)
    3. Русский по умолчанию
    """
    # 1. Пробуем получить из storage
    lang_code = await storage.get_user_language(telegram_user.id)
    if lang_code in SUPPORTED_LANGUAGES:
        return lang_code

    # 2. Пробуем Telegram API
    telegram_lang = telegram_user.language_code
    if telegram_lang in SUPPORTED_LANGUAGES:
        # Сохраняем для будущих запросов
        await storage.update_user_language(telegram_user.id, telegram_lang)
        return telegram_lang

    # 3. Default
    return DEFAULT_LANGUAGE
```

#### 3.2 Обновить common.py
Файл: `src/nomus/presentation/bot/handlers/common.py`

```python
from nomus.application.services.language_service import get_user_language_with_fallback

@router.message(CommandStart())
async def cmd_start(message: Message, ...):
    # ...
    if user_data and user_data.get("phone_number"):
        lang_code = await get_user_language_with_fallback(message.from_user, storage)
        lexicon = getattr(settings.messages, lang_code)
        # ...
```

#### 3.3 Обновить ordering.py
Файл: `src/nomus/presentation/bot/handlers/ordering.py`

```python
from nomus.application.services.language_service import get_user_language_with_fallback

async def start_ordering(message: Message, ...):
    # ...
    lang_code = await get_user_language_with_fallback(message.from_user, storage)
    await _start_tariff_selection(message, state, order_service, lexicon, lang_code)
```

#### 3.4 Обновить l10n_middleware.py (опционально)
Файл: `src/nomus/presentation/bot/middlewares/l10n_middleware.py`

Использовать `get_user_language_with_fallback()` в middleware для автоматического определения языка.

### Критерии приёмки
- [ ] Если язык не в storage — используется язык из Telegram
- [ ] Если язык Telegram не поддерживается — используется русский
- [ ] Определённый язык сохраняется в storage для будущих запросов

---

## Сравнение решений

| Критерий | Решение 1 (Сервер) | Решение 2 (Запрос) | Решение 3 (Telegram API) |
|----------|-------------------|-------------------|-------------------------|
| Сложность | Высокая | Средняя | Низкая |
| Изменения в NMservices | Да | Нет | Нет |
| Изменения в NoMus | Средние | Средние | Минимальные |
| UX | Бесшовный | Прерывает flow | Бесшовный |
| Надёжность | Высокая | Высокая | Средняя* |
| Персистентность | Полная | Локальная | Локальная |

*Telegram API может вернуть неподдерживаемый язык или `None`.

---

## Рекомендация

**Для быстрого решения:** Решение 3 (Telegram API fallback) — минимальные изменения, работает сразу.

**Для долгосрочного решения:** Решение 1 (Хранение на сервере) — надёжно, язык сохраняется между устройствами и рестартами.

**Комбинированный подход:** Реализовать Решение 3 сейчас, затем добавить Решение 1 для полной персистентности.

---

## Связанные файлы

### NoMus
- `src/nomus/infrastructure/database/remote_storage.py`
- `src/nomus/infrastructure/database/memory_storage.py`
- `src/nomus/presentation/bot/handlers/common.py`
- `src/nomus/presentation/bot/handlers/ordering.py`
- `src/nomus/presentation/bot/middlewares/l10n_middleware.py`

### NMservices (для Решения 1)
- `src/nmservices/models/user.py`
- `src/nmservices/api/routes/users.py`
- `src/nmservices/db/` (миграции)

---

**Дата создания:** 2026-01-29
**Автор:** Claude Code Agent
