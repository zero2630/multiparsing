from aiogram.fsm.state import StatesGroup, State

class NewParserTask(StatesGroup):
    deal_type: str = State()
    price_lims: list[int] = State()


class AvitoParserTask(StatesGroup):
    query: str = State()
    region_name: str = State()
    last_time_str: str = State()
    price_lims: list[int] = State()
