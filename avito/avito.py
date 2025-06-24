import json
from datetime import datetime
import asyncio
import time
import logging

import requests
from urllib.request import quote
from urllib.request import unquote

import bot
from main import sheets

# инициализация логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    filename="parser.log",
    filemode="a",
    format='%(asctime)s - %(levelname)s - %(message)s'
)

TOKEN = "af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir"  # токен для работы с avito api

# объявление ссылок для работы с api
avito_urls = {
    "region_info":
        f"https://m.avito.ru/api/1/slocations?key={TOKEN}&locationId=621540&limit=10&q=",

    "categories_info":
        f"https://m.avito.ru/api/2/search/main?key={TOKEN}&locationId=",

    "items_info":
        f"https://m.avito.ru/api/11/items?key={TOKEN}&sort=date&categoryId=6",

    "seller_info":
        f"https://m.avito.ru/api/1/user/profile/items?key={TOKEN}"
}

proxies = {
    "http": "http://EDum8A:kuxkYq7Av6gu@fproxy.site:11296",
    "https": "http://EDum8A:kuxkYq7Av6gu@fproxy.site:11296",
}


## класс, через который производится получение и обработка данных о товарах
class Parser():
    def __init__(self):
        self.item_name = None  # имя обрабатываемого товара
        self.region_name = None  # название региона для поиска (Москва, Ярославль, и т.д.)
        self.last_time_str = None  # начальная дата для поиска в строчном формате
        self.min_price = None  # минимальная цена для поиска
        self.max_price = None  # максимальная цена для поиска
        self.last_time = None  # начальная дата для поиска в timestamp формате
        self.region_id = None  # id региона для поиска
        self.items_ids = []  # id полученных товаров
        self.headers = {"authority": "m.avito.ru",
                        "pragma": "no-cache",
                        "cache-control": "no-cache",
                        "upgrade-insecure-requests": "1",
                        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36",
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                        "sec-fetch-site": "none",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-user": "?1",
                        "sec-fetch-dest": "document",
                        "accept-language": "ru-RU,ru;q=0.9", }  # заголовки для запроса

    # получение куки из json файла
    def load_cookies(self):
        cookies = ""  # инициализация куки для запроса

        # выгрузка списка куки
        f = open("cookies.json", "r")
        cookies_data = json.load(f)
        f.close()

        # обработка куки
        for cookie in cookies_data:
            cookies += f"{cookie['name']}={cookie['value']}; "
        cookies = cookies[:-2]

        self.headers["cookie"] = cookies  # добавляем куки к заголовкам

    # считывание аргументов для поиска товаров
    def get_params(self):
        self.item_name = input("Введите название товара: ")
        self.region_name = input("Укажите регион: ")
        self.last_time_str = input("С какой даты искать: ")
        self.min_price = input("Минимальная цена: ")
        self.max_price = input("Максимальная цена: ")

        # преобразование введенной даты в timestamp формат
        if self.last_time_str:
            self.last_time = int(datetime.strptime(self.last_time_str, "%d.%m.%Y").timestamp())

        # если указан регион, то получаем его id
        if self.region_name:
            self.region_id = self.get_region_id_by_name()

    # получение id региона по строке
    def get_region_id_by_name(self):
        json_content = requests.get(f"{avito_urls['region_info']}{quote(self.region_name)}",
                                    headers=self.headers).json()
        locations = json_content["result"]["locations"]

        return locations[0]["id"]

    # получение списка товаров
    def search_item(self, page):
        query = f"{avito_urls['items_info']}&query={self.item_name}&page={page}"

        # если есть значения у переменных то добавляем их к запросу
        if self.region_id:
            query += f"&locationId={self.region_id}"

        if self.last_time:
            query += f"&lastStamp={self.last_time}"

        if self.min_price:
            query += f"&priceMin={self.min_price}"

        if self.max_price:
            query += f"&priceMax={self.max_price}"

        json_content = requests.get(query, headers=self.headers)  # отправление запроса к api

        return json_content

    # проверка количества товаров у продавца
    def check_seller(self, seller_id):
        query = f"{avito_urls['seller_info']}&sellerId={seller_id}"
        response = requests.get(query, headers=self.headers).json()

        if response["result"]["categoryTree"]["count"] > 10:
            return False
        return True

    # метод обработки информации о полученных товарах
    def get_items(self, notifications_enabled):  # notifications_enabled отвечает за отправку сообщений в тг канал
        datenow = datetime.now().date().strftime("%d.%m.%Y")  # получение сегодняшней даты
        sheets_manager = sheets.SheetsManager()  # создание экземпляра класса для работы с google sheets
        page = 0  # страница поиска
        try:
            json_content = self.search_item(page).json()  # получение списка товаров
        except Exception as e:
            logger.error(f"request to avito error: {e}")  # запись ошибибки получения товаров

        for item in json_content["result"]["items"]:  # цикл проходится по каждому товару
            if item["type"] == "item":  # проверка чтто это именно товар, а не услуга
                if item["value"]["id"] not in self.items_ids and item["type"] == "item" and "за услугу" not in \
                        item["value"]["price"]:  # валидация товара
                    self.items_ids.append(item["value"]["id"])  # сохранение id товара
                    item_val = item["value"]  # получение основной информации о товаре
                    if item_val["sellerInfo"]["sellerTypeName"] == "Частное лицо" and self.check_seller(
                            item_val["sellerInfo"]["userKey"]):  # проверка продавца
                        if notifications_enabled:  # отправление информации о товаре в тг канал, если notifications_enabled=True
                            try:
                                asyncio.run(bot.send_msg(f"Появился новый товар!\n"
                                                         f"Название: {item_val['title']}\n"
                                                         f"Цена: {item_val['price']}\n"
                                                         f"Время появления: {datetime.fromtimestamp(item_val['time']).strftime('%d.%m.%Y')}\n"
                                                         f"Ссылка: {'https://avito.ru' + item_val['uri']}"))  # вызов функции для отправки сообщения в тг канал
                            except Exception as e:
                                logger.error(
                                    f"telegram bot error: {e}")  # логгирование ошибки об отправке сообщения ботом

                        # добавление информации о товаре для дальнейшего обновления таблицы
                        sheets_manager.add_row(
                            [item_val['title'], item_val['price']['current'], "-", 'https://avito.ru' + item_val['uri'],
                             item_val["sellerInfo"]["name"]])

        sheets_manager.push_rows()  # загрузка всех полученных товаров в таблицу


def main():
    logger.info("Started")
    p = Parser()
    p.load_cookies()
    p.get_params()
    p.get_items(False)

    # получение информации о новых товаров с перерывом в минуту
    while True:
        try:
            p.get_items(False)
            logger.info("Loaded all items")
            time.sleep(60)
        except Exception as e:
            logger.error(str(e))

    # p.save_items()


if __name__ == "__main__":
    main()
