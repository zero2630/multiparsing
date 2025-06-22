import os
import httpx
import asyncio

from conf import BOT_TOKEN, BOT_CHAT_ID


API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" # объявление ссылки для работы с telegram api

# отправка сообщения с текстом через тг бота
async def send_msg(text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/sendMessage", json={"chat_id": BOT_CHAT_ID, "text": text})