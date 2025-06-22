import os

from dotenv import load_dotenv

load_dotenv() # загружаем переменные окружения

BOT_TOKEN = os.getenv("BOT_TOKEN", None) # получаем токен тг бота
BOT_CHAT_ID = int(os.getenv("BOT_CHAT_ID", None)) # получаем id чата, в который нужно отправлять сообщения