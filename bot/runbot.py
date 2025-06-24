import asyncio  # noqa: F401

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from user_handler import router
from conf import BOT_TOKEN


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def main():
    dp.include_routers(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())