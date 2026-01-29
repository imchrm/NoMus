# Инструкция: SSH-доступ к dm@id и БД nomus

## Обзор

| Параметр | Значение |
|----------|----------|
| **Linux-машина** | `dm@id` (192.168.1.191) |
| **Windows-машина** | `zum@zu` |
| **SSH-ключ** | `$HOME/.ssh/id_linux_server` |
| **База данных** | PostgreSQL, БД `nomus` |
| **DB User** | `postgres` |
| **DB Password** | `postgres` |

---

## SSH-подключение

### Команда подключения
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191
```

### Выполнение команды на удалённой машине
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 "команда"
```

### Пример: проверка подключения
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 "hostname && whoami"
# Ожидаемый вывод:
# id
# dm
```

---

## Доступ к PostgreSQL

### Выполнение SQL-запроса
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SQL_ЗАПРОС'"
```

### Примеры запросов

#### Список таблиц
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c '\\dt'"
```

#### Структура таблицы users
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c '\\d users'"
```

#### Все пользователи
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SELECT * FROM users;'"
```

#### Последние 5 пользователей
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SELECT * FROM users ORDER BY id DESC LIMIT 5;'"
```

#### Все заказы
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SELECT * FROM orders;'"
```

#### Последние 5 заказов
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SELECT * FROM orders ORDER BY id DESC LIMIT 5;'"
```

#### Количество записей
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "PGPASSWORD=postgres psql -U postgres -h localhost -d nomus -c 'SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as orders FROM orders;'"
```

---

## Проверка сервисов

### Статус NMservices API
```bash
curl -s http://192.168.1.191:8000/docs | head -5
```

### Проверка процессов на dm@id
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "ps aux | grep -E 'nomus|uvicorn|postgres' | grep -v grep"
```

### Проверка порта PostgreSQL
```bash
powershell -Command "Test-NetConnection -ComputerName 192.168.1.191 -Port 5432 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded"
```

---

## Работа с проектами на dm@id

### Путь к NoMus
```
~/dev/python/NoMus
```

### Путь к NMservices
```
~/dev/python/NMservices
```

### Запуск NoMus бота
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "cd ~/dev/python/NoMus && poetry run python -m nomus.main"
```

### Копирование файла на dm@id
```bash
cat /путь/к/файлу | ssh -i /c/Users/zum/.ssh/id_linux_server dm@192.168.1.191 \
  "cat > ~/dev/python/NoMus/путь/к/файлу"
```

---

## Настройка SSH-ключа (если нужно заново)

### 1. Создать ключ на Windows
```powershell
ssh-keygen -t ed25519 -f $HOME\.ssh\id_linux_server -N ""
```

### 2. Скопировать публичный ключ на Linux
```powershell
type $HOME\.ssh\id_linux_server.pub | ssh dm@192.168.1.191 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat > ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### 3. Проверить подключение
```bash
ssh -i /c/Users/zum/.ssh/id_linux_server -o BatchMode=yes dm@192.168.1.191 "echo OK"
```

---

## Troubleshooting

### Ошибка: Permission denied
- Проверить права на `~/.ssh` (700) и `~/.ssh/authorized_keys` (600) на Linux
- Проверить, что ключ создан без passphrase

### Ошибка: Connection refused (PostgreSQL)
- Использовать `-h localhost` для TCP-подключения вместо Unix socket

### Ошибка: Peer authentication failed
- Использовать `-h localhost` для обхода peer authentication
