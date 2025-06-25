from aiogram.fsm.state import StatesGroup, State

class NewParserTask(StatesGroup):
    deal_type: str = State()
    price_lims: list[int] = State()