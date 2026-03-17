# Программное flow бота NoMus

Ниже представлен детальный поток выполнения программы (flow) от класса к классу / модулю, описывающий цикл от получения команды `/start` до успешного создания заказа.
Включены основные ветви сценария, а также альтернативные потоки и обработка исключительных ситуаций.

**Легенда:**
*   `[Presentation]` - Слой представления (Handlers, States)
*   `[Application]` - Слой приложения (Services)
*   `[Infrastructure]` - Слой инфраструктуры (Repositories, External APIs)
*   `[Remote]` - Взаимодействие с внешним API (NMservices / PostgreSQL backend)
*   `->` - Передача управления (вызов функции, отправка сообщения, переход состояния)

---

## 1. Старт и Проверка статуса (New!)

1.  **User** (отправляет `/start`)
2.  `->` **main.py** (Dispatcher запускает polling)
3.  `->` **Router** (в `presentation.bot.handlers.common.py`) маршрутизирует запрос
4.  `->` **common.cmd_start** (Handler)
    *   `->` `FSMContext.clear()` (Сброс состояния)

    **Режим разработки (Development Mode):**
    *   Если `ENV=development` и `SKIP_REGISTRATION=True`:
        *   `->` Создание фиктивного (mock) зарегистрированного пользователя в БД
        *   `->` `FSMContext.update_data(is_registered=True)` (Установка FSM-флага)
        *   `->` `Message.answer` (Сообщение о Dev Mode)
        *   `->` **Переход к п. 3 (Главное меню)**

    *   `->` **IUserRepository.get_user_by_telegram_id** (Infrastructure - Проверка существования пользователя)

    **Ветвление:**

    *   **Сценарий А: Пользователь зарегистрирован** (Найден в БД и есть `phone_number`)
        *   `->` **IUserRepository.get_user_language** (Загрузка языка)
        *   `->` `FSMContext.update_data(is_registered=True)` (Установка FSM-флага)
        *   `->` **common.get_main_kb** (Генерация главной клавиатуры: [🛒 Сделать заказ] [📋 Мои заказы] [⚙️ Настройки])
        *   `->` `Message.answer` (Приветствие "С возвращением!", Главное меню)
        *   `->` **Переход к п. 3 (Главное меню)**

    *   **Сценарий Б: Новый или незарегистрированный пользователь** (Не найден или нет телефона)
        *   `->` **IUserRepository.save_or_update_user** (Создание "черновика" пользователя в БД с `username`, `full_name`, `language_code`, но без телефона)
        *   Если язык пользователя (из Telegram) совпадает с поддерживаемыми (ru, uz, en):
            *   `->` `Message.answer` ("Язык определен: ...")
        *   `->` **common._send_language_selection** (Вызов функции отображения выбора языка)
        *   `->` `Message.answer` (Отправка сообщения: "Выберите язык...", Inline клавиатура)
        *   `->` **Переход к п. 2 (Выбор языка)**

## 2. Обработка выбора языка и Пользовательское соглашение

1.  **User** (нажимает кнопку языка, например "🇷🇺 Русский")
2.  `->` **Router** (в `presentation.bot.handlers.common.py`) ловит `CallbackQuery` (`lang_ru`)
3.  `->` **common.process_lang_select** (Handler)
    *   `->` **IUserRepository.update_user_language** (Сохранение языка в БД)
    *   `->` **Settings** (Загрузка текстов для выбранного языка)
    *   `->` `CallbackQuery.message.edit_text` (Подтверждение смены языка)
    *   `->` **common.get_agreement_kb** (Генерация клавиатуры: "Открыть соглашение", "Принять условия")
    *   `->` `Message.answer` (Отправка: "Пожалуйста, примите условия...", Inline клавиатура)
4.  `->` **User** (видит предложение принять условия)

   > **Примечание:** Если пользователь игнорирует кнопку "Принять условия", он не получает доступа к главному меню. Данные пользователя еще не отправлены на сервер (в БД).

## 3. Принятие соглашения и Главное меню

1.  **User** (нажимает "Принять условия")
2.  `->` **Router** (в `presentation.bot.handlers.common.py`) ловит `CallbackQuery` (`agree_terms_ru`)
3.  `->` **common.process_agreement** (Handler)
    *   `->` `CallbackQuery.message.delete` (Удаление сообщения с соглашением)
    *   `->` **common.get_main_kb** (Генерация клавиатуры: [Регистрация] [⚙️ Настройки])
    *   `->` `Message.answer` (Отправка приветствия и главного меню)
4.  `->` **User** (видит главное меню)

> **Главная клавиатура (reply keyboard)** зависит от статуса регистрации:
> - Незарегистрированный: `[Регистрация]` `[⚙️ Настройки]`
> - Зарегистрированный: `[🛒 Сделать заказ]` `[📋 Мои заказы]` `[⚙️ Настройки]`

## 4. Регистрация

1.  **User** (нажимает "Регистрация")
2.  `->` **Router** (фильтр `EmojiPrefixEquals("registration_button")`) маршрутизирует запрос
3.  `->` **registration.start_registration** (Handler в `presentation.bot.handlers.registration.py`)
    *   `->` `Message.answer` (Запрос геолокации, клавиатура `request_location=True`)
    *   `->` `FSMContext.set_state(RegistrationStates.waiting_for_location)`
3.  `->` **User** (отправляет локацию)

4.  **Router** (ловит `F.location` в состоянии `waiting_for_location`)
5.  `->` **registration.process_location** (Handler)
    *   `->` `FSMContext.update_data` (Временное сохранение координат latitude, longitude)
    *   `->` `Message.answer` (Запрос контакта, клавиатура `request_contact=True`)
    *   `->` `FSMContext.set_state(RegistrationStates.waiting_for_phone)`
6.  `->` **User** (отправляет контакт)

7.  **Router** (ловит `F.contact` в состоянии `waiting_for_phone`)
8.  `->` **registration.process_phone** (Handler)
    *   `->` **AuthService.register_user** (Application Service)
        *   `->` **SmsServiceRemote.send_sms** (Infrastructure)
            *   `->` **POST /users/register** (Remote API) — Регистрация пользователя на сервере
            *   `->` Получение `user_id` от сервера (server_id)
        *   `->` Возврат `server_user_id`
    *   `->` Создание сущности **User** (сбор данных: `phone`, `geo`, `server_user_id`)
    *   `->` **IUserRepository.save_or_update_user** (Infrastructure / RemoteStorage)
        *   `->` Сохранение в локальный кеш (MemoryStorage)
    *   `->` **RemoteStorage.flush** (Infrastructure)
        *   `->` Синхронизация всех изменений ("dirty" records) с удаленным сервером (через `RemoteApiClient`)
    *   `->` `Message.answer` ("Регистрация успешно завершена!", удаление клавиатуры)
    *   `->` `FSMContext.update_data(is_registered=True)` (Установка FSM-флага)
    *   **Переход к заказу:**
        *   `->` **ordering._start_service_selection** (Вспомогательная функция)
            *   `->` **OrderService.get_services** (Application Service → `GET /services`)
            *   `->` `FSMContext.update_data` (Сохранение списка услуг)
            *   `->` `Message.answer` ("Выберите услугу:", Inline клавиатура с услугами)
            *   `->` `FSMContext.set_state(OrderStates.selecting_service)`

## 5. Выбор услуги

1.  **User** (нажимает "🛒 Сделать заказ")
2.  `->` **Router** (фильтр `EmojiPrefixEquals("start_ordering_button")`) маршрутизирует запрос
3.  `->` **ordering.start_ordering** (Handler) — проверка регистрации, загрузка услуг
4.  **User** (нажимает inline-кнопку услуги, например "Классический массаж — 150 000 сум (60 min)")
2.  `->` **Router** (ловит `CallbackQuery` `svc_{id}` в состоянии `selecting_service`)
3.  `->` **ordering.process_service_selection** (Handler в `presentation.bot.handlers.ordering.py`)
    *   `->` Валидация выбранной услуги (по ID из callback_data)
    *   `->` `FSMContext.update_data` (Сохранение выбранной услуги и service_id)
    *   `->` `CallbackQuery.message.edit_text` (Подтверждение выбора, убирает inline-кнопки)
    *   `->` `Message.answer` ("Укажите адрес для выезда мастера...")
    *   `->` `FSMContext.set_state(OrderStates.entering_address)`
4.  `->` **User** (видит запрос на ввод адреса)

## 6. Ввод адреса

1.  **User** (вводит текстовый адрес, например "ул. Навои 25, кв. 12")
2.  `->` **Router** (ловит текст в состоянии `entering_address`)
3.  `->` **ordering.process_address** (Handler)
    *   `->` Валидация (непустой текст)
    *   `->` `FSMContext.update_data` (Сохранение адреса)
    *   `->` Формирование summary (услуга, длительность, цена, адрес)
    *   `->` `Message.answer` (Summary + Inline клавиатура: [Подтвердить] [Отменить])
    *   `->` `FSMContext.set_state(OrderStates.confirming_order)`
4.  `->` **User** (видит summary заказа)

## 7. Подтверждение и создание заказа

1.  **User** (нажимает "Подтвердить")
2.  `->` **Router** (ловит `CallbackQuery` "order_confirm" в состоянии `confirming_order`)
3.  `->` **ordering.process_order_confirm** (Handler)
    *   `->` `CallbackQuery.message.edit_text` ("Создаём ваш заказ...")
    *   `->` **OrderService.get_server_user_id** (Получение server_user_id из кеша)
    *   `->` **OrderService.create_order** (Application Service)
        *   `->` **RemoteApiClient.post("/orders")** — `POST /orders` с `{user_id, service_id, address_text}`
        *   `->` Получение `order_id` из ответа API
    *   `->` Если успех:
        *   `->` `CallbackQuery.message.edit_text` ("Заказ #{order_id} создан!")
        *   `->` `Message.answer` (Обновление reply-клавиатуры: `get_main_kb(is_registered=True)`)
    *   `->` Если ошибка:
        *   `->` `CallbackQuery.message.edit_text` ("Ошибка создания заказа")
    *   `->` `FSMContext.clear()` (Завершение сценария)

    **Альтернатива: Отмена заказа**
    *   **User** (нажимает "Отменить")
    *   `->` **ordering.process_order_cancel** (Handler)
        *   `->` `CallbackQuery.message.edit_text` ("Заказ отменён")
        *   `->` `FSMContext.clear()`

---

## 8. Просмотр активных заказов («Мои заказы»)

1.  **User** (нажимает "📋 Мои заказы")
2.  `->` **Router** (фильтр `EmojiPrefixEquals("my_orders_button")`) маршрутизирует запрос
3.  `->` **my_order.show_my_orders** (Handler в `presentation.bot.handlers.my_order.py`)
    *   `->` **OrderService.get_active_orders** (Application Service)
        *   `->` **RemoteApiClient.get("/orders/active")** — `GET /orders/active?telegram_id=X`
        *   `->` Возвращает `{orders: [...]}` (список заказов со статусами `pending`, `confirmed`, `in_progress`)
    *   **Если список пуст:**
        *   `->` `Message.answer` ("У вас нет активных заказов.")
    *   **Если есть заказы:**
        *   `->` Формирование текстового списка (для каждого заказа: номер, услуга, сумма, адрес, статус)
        *   `->` Локализация статусов через `_STATUS_KEY_MAP` → `lexicon.status_*`
        *   `->` `Message.answer` (Заголовок + список заказов)

> **Кнопка «📋 Мои заказы» всегда видна** для зарегистрированных пользователей, независимо от наличия активных заказов.

---

## 9. Уведомления о смене статуса заказа

### Push (NMservices → Telegram API)

1.  **Admin** (меняет статус через `PATCH /admin/orders/{id}`)
2.  `->` **admin/orders.update_order** → обнаружена смена статуса
3.  `->` **_notify_status_change** (Helper)
    *   `->` Загрузка user (telegram_id, language_code) и service (name)
    *   `->` **TelegramNotifier.notify_order_status** (httpx → Telegram Bot API)
    *   `->` Если доставлено: `order.notified_status = order.status` → commit
    *   `->` Если НЕ доставлено: notified_status остаётся старым

### Pull (бот → NMservices при заходе пользователя)

1.  **User** (отправляет любое сообщение)
2.  `->` **NotificationMiddleware** (runs on every message/callback)
    *   `->` **OrderService.get_pending_notifications** (Application Service)
        *   `->` `GET /orders/pending-notifications?telegram_id=X`
        *   `->` NMservices: `SELECT ... FROM orders WHERE notified_status != status`
    *   `->` Для каждого уведомления: `Bot.send_message` (локализованный шаблон)
    *   `->` **OrderService.ack_notifications** (Application Service)
        *   `->` `POST /orders/notifications/ack` → `notified_status = status`
3.  `->` Далее обработка сообщения продолжается обычным flow

---

## Альтернативные сценарии и Обработка ошибок

### А. Попытка заказа без регистрации

Ситуация: Пользователь принял соглашение, видит меню, но сразу нажал "🛒 Сделать заказ", не пройдя регистрацию.

1.  **User** (нажимает "🛒 Сделать заказ")
2.  `->` **ordering.start_ordering** (Handler)
    *   `->` **AuthService.is_user_registered** (Application Service) -> Возвращает `False`
    *   `->` `Message.answer` (Отправка сообщения: "Для заказа необходимо зарегистрироваться")
3.  `->` **User** (остается в главном меню, должен нажать "Регистрация")

### Б. Отмена действия

Ситуация: Пользователь отправляет команду `/cancel` или нажимает кнопку отмены (если она предусмотрена) в любом состоянии.

1.  **User** (отправляет `/cancel`)
2.  `->` **common.cmd_cancel** (Handler в `presentation.bot.handlers.common.py`)
    *   `->` **_get_is_registered** (Проверка FSM-флага `is_registered`, fallback → `AuthService.is_user_registered`)
    *   `->` `FSMContext.clear()` (Сброс всех состояний)
    *   `->` `FSMContext.update_data(is_registered=True)` (Восстановление флага, если пользователь зарегистрирован)
    *   `->` **common.get_main_kb** (Генерация главной клавиатуры с учётом `is_registered`)
    *   `->` `Message.answer` ("Действие отменено", клавиатура меню)
3.  `->` **User** (возвращается в главное меню)

### В. Смена языка в настройках (обновление клавиатуры)

Ситуация: Зарегистрированный пользователь меняет язык через ⚙️ Настройки → Язык.

1.  **User** (нажимает "⚙️ Настройки" → "Язык" → выбирает новый язык)
2.  `->` **common.process_lang_select** (Handler)
    *   `->` **IUserRepository.update_user_language** (Сохранение нового языка)
    *   `->` `CallbackQuery.message.edit_text` (Подтверждение смены)
    *   `->` Чтение `is_registered` из FSMContext (fallback → `AuthService.is_user_registered`)
    *   `->` `FSMContext.clear()` + восстановление `is_registered`
    *   `->` `Message.answer` (Подтверждение + **обновлённая reply-клавиатура** на новом языке)
    *   `->` **settings._show_settings_menu** (Возврат в меню настроек)
3.  `->` **User** (видит кнопки на новом языке)
