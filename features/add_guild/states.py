from aiogram.fsm.state import StatesGroup, State

class AddGuildStates(StatesGroup):
    first_input_name = State()
    input_name = State()