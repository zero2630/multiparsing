from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="создать поиск")],
        [KeyboardButton(text="stop")],
    ],
    resize_keyboard=True,
)


cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="отмена")]], resize_keyboard=True
)