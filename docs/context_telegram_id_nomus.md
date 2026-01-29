# Контекст задачи: NoMus — реализация поддержки telegram_id

## Цель задачи
Обновить NoMus для идентификации пользователей по `telegram_id` через NMservices API.

## Предусловие
**Задача для NMservices уже выполнена:**
- В таблицу `users` добавлено поле `telegram_id` (BIGINT, nullable, unique)
- Добавлен endpoint `GET /users/by-telegram/{telegram_id}`
- Endpoint `POST /users/register` принимает `telegram_id`

---

## Архитектура проекта

### Машины
| Имя | IP | Роль |
|-----|-----|------|
| `zum@zu` | localhost | Windows-машина разработки |
| `dm@id` | 192.168.1.191 | Linux-сервер (NoMus, NMservices, PostgreSQL) |

### SSH-доступ к dm@id
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 "команда"
```

### Доступ к БД nomus
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SQL'"
```

### Пути к проектам на dm@id
- NoMus: `~/dev/python/NoMus`
- NMservices: `~/dev/python/NMservices`

---

## Текущее состояние NoMus

### Проблема
При рестарте бота пользователь не находится в БД:
```
GET http://127.0.0.1:8000/users/192496135 "HTTP/1.1 404 Not Found"
```

Бот пытается найти пользователя по `telegram_id`, но NMservices API (до изменений) не поддерживал этот endpoint.

### Ключевые файлы для изменения

#### 1. `src/nomus/infrastructure/database/remote_storage.py`
**Метод `get_user_by_telegram_id()`** — строка ~50:
```python
# ТЕКУЩИЙ КОД (неправильный endpoint):
user = await self._api_client.get(f"/users/{telegram_id}")

# НУЖНО ИЗМЕНИТЬ НА:
user = await self._api_client.get(f"/users/by-telegram/{telegram_id}")
```

**Метод `flush()`** — уже отправляет `telegram_id` в данных (проверить).

#### 2. `src/nomus/domain/entities/user.py`
Проверить наличие поля `telegram_id: int`.

#### 3. `src/nomus/presentation/bot/handlers/registration.py`
Проверить, что `telegram_id` сохраняется при регистрации.

#### 4. `src/nomus/presentation/bot/handlers/common.py`
Проверить логику проверки существующего пользователя.

---

## План реализации

### Этап 1: Обновление Remote Storage
1. Изменить endpoint в `get_user_by_telegram_id()`:
   - С `/users/{telegram_id}` на `/users/by-telegram/{telegram_id}`
2. Проверить `flush()` — должен отправлять `telegram_id`

### Этап 2: Проверка сущности и handlers
3. Убедиться, что User entity содержит `telegram_id`
4. Проверить handlers — передают ли `telegram_id` при сохранении

### Этап 3: Тестирование
5. Запустить бота, зарегистрироваться
6. Проверить запись в БД — должен быть `telegram_id`
7. Рестартнуть бота
8. Отправить `/start` — бот должен найти пользователя (без повторной регистрации)

---

## Полезные команды

### Проверка структуры таблицы users
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c '\\d users'"
```

### Проверка пользователей с telegram_id
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SELECT id, phone_number, telegram_id FROM users ORDER BY id DESC LIMIT 5;'"
```

### Запуск бота на dm@id
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "cd ~/dev/python/NoMus && poetry run python -m nomus.main"
```

### Тест нового API endpoint
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "curl -s http://127.0.0.1:8000/users/by-telegram/192496135 -H 'X-API-Key: troxivasine23'"
```

---

## Ожидаемый результат

После реализации:
1. При `/start` бот вызывает `GET /users/by-telegram/{telegram_id}`
2. Если пользователь найден — сразу показывает меню заказа
3. Если не найден — запускает процесс регистрации
4. При регистрации `telegram_id` сохраняется в БД

---

## Связанные документы
- План реализации: `docs/plan_telegram_id_nomus.md`
- План NMservices: `docs/plan_telegram_id_nmservices.md`
- SSH-инструкция: `docs/ssh_access_dm_id.md`
