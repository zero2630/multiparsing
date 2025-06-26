from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="создать поиск")],
        [KeyboardButton(text="stop")],
    ],
    resize_keyboard=True,
)


deal_type = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="аренда")],
        [KeyboardButton(text="покупка")],
        [KeyboardButton(text="отмена")],
    ],
    resize_keyboard=True,
)


price_lims = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="без ограничений")],
        [KeyboardButton(text="отмена")],
    ],
    resize_keyboard=True,
)


cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="отмена")]], resize_keyboard=True
)