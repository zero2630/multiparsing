import asyncio  # noqa: F401
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from bot.keyboards.reply import deal_type
from main.database import async_session_maker
from main.models import BotUser, ParserTask, UserToTask
from bot.states import NewParserTask, AvitoParserTask
from bot.keyboards import reply, inline
from conf import PARSER_TYPE

router = Router()


@router.message(CommandStart())
async def command_start(message: Message, command: Command):
    async with async_session_maker() as session:
        stmt = select(BotUser).where(BotUser.telegram_id == message.from_user.id)
        res = (await session.execute(stmt)).first()
        if not res:
            stmt = insert(BotUser).values(telegram_id=message.from_user.id)
            await session.execute(stmt)
            await session.commit()
    await message.answer("hello", reply_markup=reply.main)


@router.message(F.text == "создать поиск")
async def create_search(message: Message, state: FSMContext):
    if PARSER_TYPE == "domclick":
        await state.set_state(NewParserTask.deal_type)
        await message.answer("выберите тип сделки:", reply_markup=reply.deal_type)
    elif PARSER_TYPE == "avito":
        await state.set_state(AvitoParserTask.query)
        await message.answer("введите поисковой запрос:", reply_markup=reply.cancel)


@router.message(AvitoParserTask.query, F.text)
async def avito_query(message: Message, state: FSMContext):
    await state.update_data(query=message.text)
    await state.set_state(AvitoParserTask.region_name)
    await message.answer("Укажите регион", reply_markup=reply.region)


@router.message(AvitoParserTask.region_name, F.text)
async def avito_region(message: Message, state: FSMContext):
    await state.update_data(region_name=message.text)
    await state.set_state(AvitoParserTask.last_time_str)
    await message.answer("Введите дату, с которой начать искать, например: 01.01.2025", reply_markup=reply.last_time)


@router.message(AvitoParserTask.last_time_str, F.text)
async def avito_time(message: Message, state: FSMContext):
    if message.text == "День назад":
        date = (datetime.today() - timedelta(days=1)).strftime("%d.%m.%Y")
    elif message.text == "Неделю назад":
        date = (datetime.today() - timedelta(days=7)).strftime("%d.%m.%Y")
    elif message.text == "Месяц назад":
        date = (datetime.today() - timedelta(days=30)).strftime("%d.%m.%Y")
    elif message.text == "Без срока":
        date = None
    else:
        date = message.text
    await state.update_data(last_time_str=date)
    await state.set_state(AvitoParserTask.price_lims)
    await message.answer("укажите ценовой диапозон в формате <i> мин. цена - макс. цена </i> например: 1000000 - 1500000", reply_markup=reply.price_lims)


@router.message(AvitoParserTask.price_lims, (F.text.contains("-") | F.text.contains("без ограничений")))
async def avito_price(message: Message, state: FSMContext):
    if message.text == "без ограничений":
        prices = [None, None]
    else:
        prices = list(map(int, message.text.split("-")))
    res = await state.update_data(price_lims=prices)
    await state.clear()

    async with async_session_maker() as session:
        stmt = insert(ParserTask).values(
            search_query={
                "item_name": res["query"],
                "region_name": res["region_name"],
                "last_time_str": res["last_time_str"],
                "min_price": res["price_lims"][0],
                "max_price": res["price_lims"][1]
            },
            periodicity=0,
            status="avito"
        ).on_conflict_do_update(index_elements=["search_query"], set_=dict(status=PARSER_TYPE)).returning(ParserTask.id)
        parser_task_id = (await session.execute(stmt)).first()[0]

        stmt = insert(UserToTask).values(user_id=message.from_user.id, task_id=parser_task_id, uniq_val=f"{message.from_user.id}-{parser_task_id}")
        stmt = stmt.on_conflict_do_nothing(index_elements=["uniq_val"])
        await session.execute(stmt)

        await session.commit()

    await message.answer("новый поиск задан", reply_markup=reply.main)


@router.message(NewParserTask.deal_type, F.text.in_(["аренда", "покупка"]))
async def deal_type(message: Message, state: FSMContext):
    types = {
        "аренда": "rent",
        "покупка": "sale"
    }
    await state.update_data(deal_type=types[message.text])
    await state.set_state(NewParserTask.price_lims)
    await message.answer("укажите ценовой диапозон в формате <i> мин. цена - макс. цена </i> например: 1000000 - 1500000", reply_markup=reply.price_lims)


@router.message(NewParserTask.price_lims, (F.text.contains("-") | F.text.contains("без ограничений")))
async def price_lims(message: Message, state: FSMContext):
    if message.text == "без ограничений":
        prices = [None, None]
    else:
        prices = list(map(int, message.text.split("-")))
    res = await state.update_data(price_lims=prices)
    await state.clear()

    async with async_session_maker() as session:
        stmt = insert(ParserTask).values(
            search_query={
                "offer_types": ["flat"],
                "rooms": ["st"],
                "price_lims": res["price_lims"],
                "deal_type": res["deal_type"],
                "location": 2299
            },
            periodicity=0,
            status="domclick"
        ).on_conflict_do_update(index_elements=["search_query"], set_=dict(status="domclick")).returning(ParserTask.id)
        parser_task_id = (await session.execute(stmt)).first()[0]

        stmt = insert(UserToTask).values(user_id=message.from_user.id, task_id=parser_task_id, uniq_val=f"{message.from_user.id}-{parser_task_id}")
        stmt = stmt.on_conflict_do_nothing(index_elements=["uniq_val"])
        await session.execute(stmt)

        await session.commit()

    await message.answer("новый поиск задан", reply_markup=reply.main)


@router.message(F.text == "мои подписки")
async def stop(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(ParserTask).where(ParserTask.id.in_(select(UserToTask.task_id).where(UserToTask.user_id == message.from_user.id))).where(ParserTask.status == PARSER_TYPE)
        tasks = (await session.execute(stmt)).all()
        tasks_id = [task[0].id for task in tasks]

    await message.answer(text="выбирайте.", reply_markup=inline.subs(tasks_id))


@router.callback_query(inline.Subs.filter(F.action == "get_task"))
async def tap_dislike(call: CallbackQuery, callback_data: inline.Subs):
    deal_type = {"sale": "покупка", "rent": "аренда"}

    async with async_session_maker() as session:
        stmt = select(ParserTask.search_query).where(ParserTask.id == callback_data.selected_task)
        res = (await session.execute(stmt)).first()[0]

    if PARSER_TYPE == "domclick":
        await call.message.edit_text(f"Тип сделки: {deal_type[res['deal_type']]}\n"
                                 f"Минимальная цена: {res['price_lims'][0]}\n"
                                 f"Максимальная цена: {res['price_lims'][1]}\n", reply_markup=inline.sub_info(callback_data.selected_task))
    elif PARSER_TYPE == "avito":
        await call.message.edit_text(f"Поисковый запрос: {res["item_name"]}\n"
                                     f"Регион: {res["region_name"]}\n"
                                     f"С какой даты искать: {res["last_time_str"]}\n"
                                     f"Минимальная цена: {res["min_price"]}\n"
                                     f"Максимальная цена: {res["max_price"]}\n",
                                     reply_markup=inline.sub_info(callback_data.selected_task))


@router.callback_query(inline.Subs.filter(F.action == "del_task"))
async def tap_dislike(call: CallbackQuery, callback_data: inline.Subs):
    async with async_session_maker() as session:
        stmt = delete(UserToTask).where(UserToTask.task_id == callback_data.selected_task).where(UserToTask.user_id == call.from_user.id)
        await session.execute(stmt)
        await session.commit()
        stmt = select(UserToTask).where(UserToTask.task_id == callback_data.selected_task)
        res = (await session.execute(stmt)).first()
        if not res:
            stmt = delete(ParserTask).where(ParserTask.id == callback_data.selected_task)
            await session.execute(stmt)
            await session.commit()

    await call.message.edit_text("Удалено", reply_markup=None)


@router.message(F.text == "stop")
async def stop(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = update(ParserTask).values(status="inactive")
        await session.execute(stmt)
        await session.commit()
    await message.answer("stopped", reply_markup=reply.main)



@router.message(F.text == "отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("действие отменено", reply_markup=reply.main)


