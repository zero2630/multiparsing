from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="избранное")],
        [KeyboardButton(text="мои подписки")],
        [KeyboardButton(text="создать поиск")],
        [KeyboardButton(text="помощь")],
    ],
    resize_keyboard=True,
)


cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="отмена")]], resize_keyboard=True
)