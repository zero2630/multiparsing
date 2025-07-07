from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="создать поиск (avito)")],
        [KeyboardButton(text="создать поиск (domclick)")],
        [KeyboardButton(text="мои подписки")],
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


region = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Москва")],
        [KeyboardButton(text="отмена")],
    ],
    resize_keyboard=True,
)


last_time = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="День назад")],
        [KeyboardButton(text="Неделю назад")],
        [KeyboardButton(text="Месяц назад")],
        [KeyboardButton(text="Без срока")],
        [KeyboardButton(text="отмена")],
    ],
    resize_keyboard=True,
)



cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="отмена")]], resize_keyboard=True
)