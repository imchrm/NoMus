# План: Добавление поддержки telegram_id в NoMus

## Цель
Обновить NoMus для использования `telegram_id` при идентификации пользователей через NMservices API.

## Зависимости
- **Требуется сначала выполнить**: План для NMservices (добавление `telegram_id` в БД и API)

---

## Этап 1: Обновление Remote Storage

### 1.1 Изменить `get_user_by_telegram_id()`
**Файл:** `src/nomus/infrastructure/database/remote_storage.py`

**Текущее поведение:**
```python
user = await self._api_client.get(f"/users/{telegram_id}")
```

**Новое поведение:**
```python
user = await self._api_client.get(f"/users/by-telegram/{telegram_id}")
```

### 1.2 Обновить `flush()` — отправка telegram_id при регистрации
**Файл:** `src/nomus/infrastructure/database/remote_storage.py`

Убедиться, что при вызове `POST /users/register` передаётся поле `telegram_id` в данных пользователя.

**Проверить:** данные `user_data` уже содержат `telegram_id` из MemoryStorage.

---

## Этап 2: Проверка сущности User

### 2.1 Убедиться, что User entity содержит telegram_id
**Файл:** `src/nomus/domain/entities/user.py`

Поле `telegram_id: int` должно присутствовать в модели.

### 2.2 Проверить передачу telegram_id
**Файлы для проверки:**
- `src/nomus/presentation/bot/handlers/registration.py` — при сохранении пользователя
- `src/nomus/presentation/bot/handlers/common.py` — при проверке существующего пользователя

---

## Этап 3: Тестирование

### 3.1 Unit-тесты
- Тест `RemoteStorage.get_user_by_telegram_id()` — проверка вызова правильного endpoint
- Тест `RemoteStorage.flush()` — проверка передачи `telegram_id` в данных

### 3.2 Интеграционный тест
**Сценарий:**
1. Запустить бота
2. Пройти регистрацию (новый пользователь)
3. Проверить запись в БД — должен быть `telegram_id`
4. Остановить бота
5. Запустить бота заново
6. Отправить `/start`
7. **Ожидаемый результат:** Бот находит пользователя по `telegram_id`, НЕ запрашивает язык/регистрацию

---

## Чеклист

- [ ] Обновлён endpoint в `get_user_by_telegram_id()`
- [ ] `flush()` отправляет `telegram_id`
- [ ] User entity содержит `telegram_id`
- [ ] Handlers передают `telegram_id` при сохранении
- [ ] Unit-тесты написаны
- [ ] Интеграционный тест пройден
- [ ] Код закоммичен и запушен

---

## Оценка времени
- Этап 1: ~30 минут
- Этап 2: ~15 минут (проверка)
- Этап 3: ~30 минут

**Итого:** ~1.5 часа
