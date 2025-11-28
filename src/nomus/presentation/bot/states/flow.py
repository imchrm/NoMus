from aiogram.fsm.state import State, StatesGroup


class FlowStates(StatesGroup):
    after_start = State()
