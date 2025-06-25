import asyncio  # noqa: F401

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, update, insert

from main.database import async_session_maker
from main.models import BotUser, ParserTask
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


@router.message(F.text == "run1")
async def run1(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = insert(ParserTask).values(
            search_query={
                "offer_types": ["flat"],
                "rooms": ["st"],
                "price_lims": [None, None],
                "deal_type": "sale",
                "location": 2299
            },
            periodicity=0,
            status="active"
        )
        await session.execute(stmt)
        await session.commit()
    await state.clear()
    await message.answer("task created", reply_markup=reply.main)


@router.message(F.text == "создать поиск")
async def ct(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = update(ParserTask).values(status="inactive")
        await session.execute(stmt)
        await session.commit()
    await state.clear()
    await message.answer("task deactivated", reply_markup=reply.main)



@router.message(F.text == "stop1")
async def stop1(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = update(ParserTask).values(status="inactive")
        await session.execute(stmt)
        await session.commit()
    await state.clear()
    await message.answer("task deactivated", reply_markup=reply.main)


@router.message(F.text == "отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("действие отменено", reply_markup=reply.main)


