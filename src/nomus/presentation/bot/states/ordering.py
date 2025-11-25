from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    selecting_tariff = State()
    waiting_for_payment = State()
