# Программное flow бота NoMus

Ниже представлен детальный поток выполнения программы (flow) от класса к классу / модулю, описывающий цикл от получения команды `/start` до успешного создания заказа.

**Легенда:**
*   `[Presentation]` - Слой представления (Handlers, States)
*   `[Application]` - Слой приложения (Services)
*   `[Infrastructure]` - Слой инфраструктуры (Repositories, External APIs)
*   `->` - Передача управления (вызов функции, отправка сообщения, переход состояния)

---

## 1. Старт и Меню

1.  **User** (отправляет `/start`)
2.  `->` **main.py** (Dispatcher запускает polling)
3.  `->` **Router** (в `presentation.bot.handlers.common.py`) маршрутизирует запрос
4.  `->` **common.cmd_start** (Handler)
    *   `->` `FSMContext.clear()` (Сброс состояния)
    *   `->` `common.get_start_kb()` (Генерация клавиатуры: "Регистрация", "Сделать заказ")
    *   `->` `Message.answer` (Отправка приветствия и клавиатуры)
5.  `->` **User** (видит меню)

## 2. Попытка заказа без регистрации (неуспешная ветка)

1.  **User** (нажимает "Сделать заказ")
2.  `->` **ordering.start_ordering** (Handler в `presentation.bot.handlers.ordering.py`)
    *   `->` **AuthService.is_user_registered** (Application Service)
        *   `->` **MemoryStorage.get_user** (Infrastructure / Repo)
        *   `->` Возврат `False`
    *   `->` `Message.answer` ("...необходимо сначала зарегистрироваться...")
3.  `->` **User** (остается в меню)

## 3. Регистрация

1.  **User** (нажимает "Регистрация")
2.  `->` **registration.start_registration** (Handler в `presentation.bot.handlers.registration.py`)
    *   `->` `Message.answer` (Запрос контакта, клавиатура `request_contact=True`)
    *   `->` `FSMContext.set_state(RegistrationStates.waiting_for_phone)`
3.  `->` **User** (отправляет контакт)

4.  **Router** (ловит `F.contact` в состоянии `waiting_for_phone`)
5.  `->` **registration.process_phone** (Handler)
    *   `->` `FSMContext.update_data` (Сохранение телефона)
    *   `->` **AuthService.send_verification_code** (Application Service)
        *   `->` **SmsServiceStub.send** (Infrastructure)
    *   `->` `Message.answer` ("Код подтверждения отправлен...", удаление клавиатуры)
    *   `->` `FSMContext.set_state(RegistrationStates.waiting_for_sms_code)`
6.  `->` **User** (вводит код "1234")

7.  **Router** (ловит текст в состоянии `waiting_for_sms_code`)
8.  `->` **registration.process_code** (Handler)
    *   `->` Проверка формата кода (цифры, длина)
    *   `->` Проверка кода (упрощенно `== "1234"`)
    *   `->` Создание сущности **User** (Domain Entity)
    *   `->` **AuthService.register_user** (Application Service)
        *   `->` **MemoryStorage.save_user** (Infrastructure / Repo)
    *   `->` `Message.answer` ("Регистрация успешно завершена!")
    *   **Переход к заказу:**
        *   `->` **OrderService.get_tariffs** (Application Service)
        *   `->` `FSMContext.update_data` (Сохранение тарифов)
        *   `->` `Message.answer` (Предложение выбрать тариф, клавиатура тарифов)
        *   `->` `FSMContext.set_state(OrderStates.selecting_tariff)`

## 4. Выбор заказа и Оплата

1.  **User** (выбирает тариф, например "Start")
2.  `->` **Router** (ловит текст в состоянии `selecting_tariff`)
3.  `->` **ordering.process_tariff** (Handler в `presentation.bot.handlers.ordering.py`)
    *   `->` Валидация тарифа (проверка наличия в `tariffs` из `state`)
    *   `->` `FSMContext.update_data` (Сохранение выбранного тарифа и суммы)
    *   `->` Создание `InlineKeyboardMarkup` (Кнопка "Оплатить X сум")
    *   `->` `Message.answer` (Инвойс/Сумма к оплате)
    *   `->` `FSMContext.set_state(OrderStates.waiting_for_payment)`
4.  `->` **User** (нажимает "Оплатить")

5.  **Router** (ловит `CallbackQuery` "pay" в состоянии `waiting_for_payment`)
6.  `->` **ordering.process_payment** (Handler)
    *   `->` `CallbackQuery.message.edit_text` ("Обработка платежа...")
    *   `->` `FSMContext.get_data` (Получение тарифа и суммы)
    *   `->` **OrderService.create_order** (Application Service)
        *   `->` **PaymentServiceStub.process_payment** (Infrastructure / Stub - симуляция оплаты)
        *   `->` Если оплата успешна:
            *   `->` **MemoryStorage.save_order** (Infrastructure / Repo - сохранение заказа)
            *   `->` Возврат `True`
    *   `->` `CallbackQuery.message.edit_text` ("Заказ успешно оплачен и создан!")
    *   `->` `FSMContext.clear()` (Завершение сценария)
