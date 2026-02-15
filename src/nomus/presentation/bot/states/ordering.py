from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    selecting_service = State()
    entering_address = State()
    confirming_order = State()
