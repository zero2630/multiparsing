from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class Subs(CallbackData, prefix="subs"):
    action: str
    selected_task: int


class Watch(CallbackData, prefix="watch"):
    action: str
    cur_id: int | None


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


def watch(is_notif: bool, ids: list[int]):
    builder = InlineKeyboardBuilder()

    if is_notif:
        builder.button(
            text=f"посмотреть",
            callback_data=Subs(action="watch_first")
        )

    else:
        builder.button(text=f"⬅️", callback_data=Watch(action="watch", cur_id=ids[0]))
        builder.button(text=f"❤️", callback_data=Watch(action="watch", cur_id=ids[0]))
        builder.button(text=f"➡️", callback_data=Watch(action="watch", cur_id=ids[0]))

    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)

