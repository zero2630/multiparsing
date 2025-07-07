import os

from dotenv import load_dotenv

load_dotenv() # загружаем переменные окружения

BOT_TOKEN = os.getenv("BOT_TOKEN", None)

DB_HOST = os.getenv("DB_HOST", None)
DB_NAME = os.getenv("DB_NAME", None)
DB_PASS = os.getenv("DB_PASS", None)
DB_PORT = os.getenv("DB_PORT", None)
DB_USER = os.getenv("DB_USER", None)

PARSER_TYPE = os.getenv("PARSER_TYPE", None)