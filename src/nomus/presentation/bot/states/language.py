from aiogram.fsm.state import State, StatesGroup


class LanguageStates(StatesGroup):
    choosing_language = State()
    # Состояние для Решения 2: ожидание выбора языка с возвратом к прерванному действию
    waiting_for_language = State()
    