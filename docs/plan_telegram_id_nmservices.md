# План: Добавление telegram_id в NMservices

## Цель
Добавить поле `telegram_id` в таблицу `users` и обновить API для поддержки идентификации пользователей по Telegram ID.

## Зависимости
- Нет внешних зависимостей
- **После выполнения:** можно приступать к плану для NoMus

---

## Этап 1: Миграция БД

### 1.1 Создать Alembic миграцию
**Команда:**
```bash
alembic revision --autogenerate -m "add_telegram_id_to_users"
```

**Изменения в миграции:**
```python
def upgrade():
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

def downgrade():
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_column('users', 'telegram_id')
```

**Параметры поля:**
- Тип: `BIGINT` (Telegram ID может быть большим числом)
- Nullable: `True` (для совместимости с существующими записями)
- Unique index: `ix_users_telegram_id`

### 1.2 Применить миграцию
```bash
alembic upgrade head
```

### 1.3 Проверить результат
```sql
\d users
-- Должно появиться поле telegram_id
```

---

## Этап 2: Обновление модели

### 2.1 SQLAlchemy модель User
**Файл:** `nms/models/user.py` (или аналогичный)

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)  # ДОБАВИТЬ
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

### 2.2 Pydantic схемы
**Файл:** `nms/schemas/user.py` (или аналогичный)

```python
class UserCreate(BaseModel):
    phone_number: str
    telegram_id: int | None = None  # ДОБАВИТЬ

class UserResponse(BaseModel):
    id: int
    phone_number: str
    telegram_id: int | None = None  # ДОБАВИТЬ
    created_at: datetime
    updated_at: datetime
```

---

## Этап 3: Обновление API

### 3.1 Обновить `POST /users/register`
**Файл:** `nms/routers/users.py` (или аналогичный)

Принимать `telegram_id` в теле запроса и сохранять в БД.

```python
@router.post("/users/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверить, существует ли пользователь с таким telegram_id
    if user_data.telegram_id:
        existing = db.query(User).filter(User.telegram_id == user_data.telegram_id).first()
        if existing:
            return {"status": "ok", "user_id": existing.id}

    # Создать нового пользователя
    user = User(
        phone_number=user_data.phone_number,
        telegram_id=user_data.telegram_id  # ДОБАВИТЬ
    )
    db.add(user)
    db.commit()
    return {"status": "ok", "user_id": user.id}
```

### 3.2 Добавить `GET /users/by-telegram/{telegram_id}`
**Файл:** `nms/routers/users.py`

Новый endpoint для поиска пользователя по Telegram ID.

```python
@router.get("/users/by-telegram/{telegram_id}")
async def get_user_by_telegram_id(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
```

### 3.3 (Опционально) Обновить `GET /users/{id}`
Оставить как есть — этот endpoint ищет по внутреннему `id`.

---

## Этап 4: Тестирование

### 4.1 Unit-тесты
- Тест `POST /users/register` с `telegram_id`
- Тест `GET /users/by-telegram/{telegram_id}` — пользователь найден
- Тест `GET /users/by-telegram/{telegram_id}` — пользователь не найден (404)
- Тест уникальности `telegram_id` (попытка создать дубликат)

### 4.2 Проверка миграции
```sql
-- Проверить существующие записи (telegram_id = NULL)
SELECT id, phone_number, telegram_id FROM users;

-- Проверить индекс
\di ix_users_telegram_id
```

### 4.3 Ручное тестирование API
```bash
# Регистрация с telegram_id
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: troxivasine23" \
  -d '{"phone_number": "+998901234567", "telegram_id": 192496135}'

# Поиск по telegram_id
curl http://localhost:8000/users/by-telegram/192496135 \
  -H "X-API-Key: troxivasine23"
```

---

## Чеклист

- [ ] Создана Alembic миграция
- [ ] Миграция применена к БД
- [ ] SQLAlchemy модель обновлена
- [ ] Pydantic схемы обновлены
- [ ] `POST /users/register` принимает `telegram_id`
- [ ] `GET /users/by-telegram/{telegram_id}` добавлен
- [ ] Unit-тесты написаны
- [ ] Ручное тестирование пройдено
- [ ] Код закоммичен и запушен

---

## Оценка времени
- Этап 1 (Миграция): ~20 минут
- Этап 2 (Модели): ~15 минут
- Этап 3 (API): ~30 минут
- Этап 4 (Тесты): ~30 минут

**Итого:** ~1.5 часа

---

## Риски и заметки
1. **Существующие пользователи** — у них `telegram_id = NULL`, это нормально
2. **Уникальность** — один Telegram аккаунт = один пользователь в системе
3. **BigInteger** — Telegram ID может быть > 2^31, используем BIGINT
