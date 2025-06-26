import asyncio  # noqa: F401

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from bot.keyboards.reply import deal_type
from main.database import async_session_maker
from main.models import BotUser, ParserTask, UserToTask
from bot.states import NewParserTask
from bot.keyboards import reply

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
    await state.set_state(NewParserTask.deal_type)
    await message.answer("выберите тип сделки:", reply_markup=reply.deal_type)


@router.message(NewParserTask.deal_type, F.text.in_(["аренда", "покупка"]))
async def deal_type(message: Message, state: FSMContext):
    types = {
        "аренда": "rent",
        "покупка": "sale"
    }
    await state.update_data(deal_type=types[message.text])
    await state.set_state(NewParserTask.price_lims)
    await message.answer("укажите ценовой диапозон в формате <i> мин. цена - макс. цена </i> например: 1000000 - 1500000", reply_markup=reply.price_lims)


@router.message(NewParserTask.price_lims, F.text.contains("-"))
async def price_lims(message: Message, state: FSMContext):
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
            status="active"
        ).on_conflict_do_update(index_elements=["search_query"], set_=dict(status="active")).returning(ParserTask.id)
        parser_task_id = (await session.execute(stmt)).first()[0]

        stmt = insert(UserToTask).values(user_id=message.from_user.id, task_id=parser_task_id)
        await session.execute(stmt)

        await session.commit()

    await message.answer("новый поиск задан", reply_markup=reply.main)


@router.message(F.text == "отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("действие отменено", reply_markup=reply.main)


