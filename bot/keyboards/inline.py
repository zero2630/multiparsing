from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class Subs(CallbackData, prefix="subs"):
    action: str
    selected_task: int


def subs(tasks):
    builder = InlineKeyboardBuilder()
    for i in range(len(tasks)):
        builder.button(
            text=f"{i+1}",
            callback_data=Subs(action="get_task", selected_task=tasks[i])
        )
    builder.adjust(3, 3, 3)
    return builder.as_markup(resize_keyboard=True)


def sub_info(selected_task):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"отписаться",
        callback_data=Subs(action="del_task", selected_task=selected_task)
    )
    return builder.as_markup(resize_keyboard=True)

