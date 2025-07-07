import asyncio  # noqa: F401

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert

from user_handler import router
from conf import BOT_TOKEN, PARSER_TYPE
from main.database import async_session_maker
from main.models import BotUser, UserToTask, AnnouncementToTask, Announcement, ParserTask, Viewed

import html


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def send_slow(tg_id, announcements):
    for announcement in announcements:
        async with async_session_maker() as session:
            stmt = select(Viewed).where(Viewed.announcement_id == announcement.id).where(Viewed.user_id == tg_id)
            res = (await session.execute(stmt)).first()
            if not res:
                stmt = insert(Viewed).values(announcement_id=announcement.id, user_id=tg_id)
                await session.execute(stmt)
                await session.commit()
                await bot.send_photo(
                                        chat_id=tg_id,
                                        photo=announcement.img_url,
                                        caption=f"<b>{announcement.title}</b>\n"
                                            f"<i>{announcement.price} ₽</i>\n"
                                            f"<a href=\'{announcement.url}\'>ссылка</a>\n\n"
                                            f"{announcement.status}"
                                       )
                await asyncio.sleep(2)


async def collect_announcements():
    while True:
        async with async_session_maker() as session:
            stmt = select(ParserTask.id).where(ParserTask.status != "inactive")
            tasks = [task[0] for task in (await session.execute(stmt)).all()]

            for task in tasks:
                stmt1 = select(UserToTask.user_id).where(UserToTask.task_id == task)
                stmt2 = select(Announcement).where(Announcement.id.in_(select(AnnouncementToTask.announcement_id).where(AnnouncementToTask.task_id == task)))
                users = [user[0] for user in (await session.execute(stmt1)).all()]
                announcements = [announcement[0] for announcement in (await session.execute(stmt2)).all()]
                send_tasks = [asyncio.create_task(send_slow(user, announcements)) for user in users]
                for send_task in asyncio.as_completed(send_tasks):
                    await send_task
        await asyncio.sleep(60)


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(collect_announcements())
    dp.include_routers(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())