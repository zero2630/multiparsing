import json
from datetime import datetime
import asyncio
import time
import logging
import subprocess

import requests
from urllib.parse import quote
from urllib.parse import unquote
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from bot.keyboards.reply import last_time
from main.database import async_session_maker
from main.models import BotUser, Announcement, ParserTask, AnnouncementToTask

# инициализация логгера
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    filename="parser.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

TOKEN = "af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir"  # токен для работы с avito api

# объявление ссылок для работы с api
avito_urls = {
    "region_info": f"https://m.avito.ru/api/1/slocations?key={TOKEN}&locationId=621540&limit=10&q=",
    "categories_info": f"https://m.avito.ru/api/2/search/main?key={TOKEN}&locationId=",
    "items_info": f"https://m.avito.ru/api/11/items?key={TOKEN}&sort=date",
    "seller_info": f"https://m.avito.ru/api/1/user/profile/items?key={TOKEN}",
}

proxies = {
    "http": "http://EDum8A:kuxkYq7Av6gu@fproxy.site:11296",
    "https": "http://EDum8A:kuxkYq7Av6gu@fproxy.site:11296",
}


## класс, через который производится получение и обработка данных о товарах
class AvitoParser:
    def __init__(self):
        self.item_name = None  # имя обрабатываемого товара
        self.region_name = (
            None  # название региона для поиска (Москва, Ярославль, и т.д.)
        )
        self.last_time_str = None  # начальная дата для поиска в строчном формате
        self.min_price = None  # минимальная цена для поиска
        self.max_price = None  # максимальная цена для поиска
        self.last_time = None  # начальная дата для поиска в timestamp формате
        self.region_id = None  # id региона для поиска
        self.items_ids = []  # id полученных товаров
        self.headers = {
            "authority": "m.avito.ru",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "ru-RU,ru;q=0.9",
        }  # заголовки для запроса

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
    def get_params(self, item_name, region_name, last_time_str, min_price, max_price):
        self.item_name = item_name
        self.region_name = region_name
        self.last_time_str = last_time_str
        self.min_price = min_price
        self.max_price = max_price

        # преобразование введенной даты в timestamp формат
        if self.last_time_str:
            self.last_time = int(
                datetime.strptime(self.last_time_str, "%d.%m.%Y").timestamp()
            )

        # если указан регион, то получаем его id
        if self.region_name:
            self.region_id = self.get_region_id_by_name()

    # получение id региона по строке
    def get_region_id_by_name(self):
        json_content = requests.get(
            f"{avito_urls['region_info']}{quote(self.region_name)}",
            headers=self.headers,
        ).json()
        locations = json_content["result"]["locations"]

        return locations[0]["id"]

    # получение списка товаров
    def search_item(self, page):
        last_time = ""
        min_price = ""
        max_price = ""
        if self.last_time_str:
            last_time = f"&locationId={self.last_time}"
        if self.min_price:
            min_price = f"&priceMin={self.min_price}"
        if self.max_price:
            max_price = f"&priceMax={self.max_price}"
        query = f"curl --location 'https://m.avito.ru/api/11/items?key=af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir&sort=date&query=%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B8%D1%80%D0%B0%20%D0%B4%D0%B2%D1%83%D1%85%D0%BA%D0%BE%D0%BC%D0%BD%D0%B0%D1%82%D0%BD%D0%B0%D1%8F&page=0&locationId={self.region_id}{last_time}{min_price}{max_price}' \
--header 'Accept:  text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
--header 'Accept-encoding:  gzip, deflate, br, zstd' \
--header 'Accept-language:  ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7' \
--header 'Cache-control:  no-cache' \
--header 'Cookie:  srv_id=yXbPESUU3Moz9ZCD.10r86HZ9zsKP-8moMmgEoKXFi-FG9RitwMk8WbZWD4ni8aYHjqj7LQLYgDGKdxQ=.wCPqLh80a1fLLNx7o3FITDbLZyKDgSq3MTUT2scsR0w=.mav; gMltIuegZN2COuSe=EOFGWsm50bhh17prLqaIgdir1V0kgrvN; u=3765010y.opvjv7.1ugcfrv066j0; _gcl_au=1.1.999728986.1751388668; _ga=GA1.1.2089260368.1751388668; ma_cid=1751388667893438222; adrdel=1751388668203; adrdel=1751388668203; adrcid=AsU3Ah-dHTtMeH3Nt4DiO0w; adrcid=AsU3Ah-dHTtMeH3Nt4DiO0w; ma_id=8498578391751388667954; tmr_lvid=c45e71232694849e322f7134d894a030; tmr_lvidTS=1751388668283; acs_3=%7B%22hash%22%3A%221aa3f9523ee6c2690cb34fc702d4143056487c0d%22%2C%22nst%22%3A1751475068296%2C%22sl%22%3A%7B%22224%22%3A1751388668296%2C%221228%22%3A1751388668296%7D%7D; acs_3=%7B%22hash%22%3A%221aa3f9523ee6c2690cb34fc702d4143056487c0d%22%2C%22nst%22%3A1751475068296%2C%22sl%22%3A%7B%22224%22%3A1751388668296%2C%221228%22%3A1751388668296%7D%7D; uxs_uid=95e7ee50-569b-11f0-a028-29c0e60e15ae; ma_id_api=lnmJsgFmUNNcz4pjZgmBi9+BsHH029KMTeemRfuqKJ8+fgLRnmpFdux7xKSY2AEYhY1G6hM6nFf+f1QkP1uTFmhbasZbPF61BWY+88CPSnV2H+0MPOwZ3JUu/utRgrxJEz3lk7XPGB6RuxGq1Lctv18jxrbc1hNlVn5CwgQqatMNUuSdsOYfnI7ndVQ7sOb/yn+PT76fIj/vWFDOVWezpgeRamK+IY8Vb+3k2htVakQ5qF4JZ7PLO8B0AjPCadLo4EyexGZRILIwVTD6fCciuZDIqZiZeCNiNUO+ouLCMB86VUae0Z1dZcMA/9N+vzalJ/NFydHxLxiu/vG5x87QPg==; __ai_fp_uuid=0197f998e623bb4b%3A1; __upin=mCw/ZxxM83SjBfOVUDoaWA; domain_sid=t7OFBjkU-secvnyxbn1FW%3A1751388668613; _buzz_aidata=JTdCJTIydWZwJTIyJTNBJTIybUN3JTJGWnh4TTgzU2pCZk9WVURvYVdBJTIyJTJDJTIyYnJvd3NlclZlcnNpb24lMjIlM0ElMjIxMzUuMCUyMiUyQyUyMnRzQ3JlYXRlZCUyMiUzQTE3NTEzODg2Njg1NDUlN0Q=; _buzz_mtsa=JTdCJTIydWZwJTIyJTNBJTIyNTM4YjQ2Y2ZkYWY5ZDUyZTgwMjU2MDQ3ZWFmZjRkMzIlMjIlMkMlMjJicm93c2VyVmVyc2lvbiUyMiUzQSUyMjEzNS4wJTIyJTJDJTIydHNDcmVhdGVkJTIyJTNBMTc1MTM4ODY2ODUyMyU3RA==; cookie_consent_shown=1; f=5.0c4f4b6d233fb90636b4dd61b04726f147e1eada7172e06c47e1eada7172e06c47e1eada7172e06c47e1eada7172e06cb59320d6eb6303c1b59320d6eb6303c1b59320d6eb6303c147e1eada7172e06c8a38e2c5b3e08b898a38e2c5b3e08b890df103df0c26013a7b0d53c7afc06d0b2ebf3cb6fd35a0ac0df103df0c26013a8b1472fe2f9ba6b91772440e04006def90d83bac5e6e82bd59c9621b2c0fa58f915ac1de0d03411231a1058e37535dce34d62295fceb188df88859c11ff008953de19da9ed218fe23de19da9ed218fe2e992ad2cc54b8aa87fde300814b1e8553de19da9ed218fe23de19da9ed218fe23de19da9ed218fe23de19da9ed218fe2b5b87f59517a23f280a995c83bf64175352c31daf983fa077a7b6c33f74d335c76ff288cd99dba464707c4b7aedd335eeb9e68250eb4bf8b2c5a8413db534ca25e3d0299e398cf136c077a27e77923765240c5b3953cc2de0776829d2064eb0291e52da22a560f550df103df0c26013a0df103df0c26013aaaa2b79c1ae92595a250863d96d55ed2a91940a5dfdfab063de19da9ed218fe2c772035eab81f5e110e95b305e77352a90d338d7ba53c088bd1411da5ddf2553; ft=\"V/CubgTEo78q2olRCbpHc+7+aSvYncY1WEVGwHaew9qV6eCoQR2auMaFsYcZXlqdFST82QtuXgdLQ8XXEhJRRBMFHugp+zRBidCgEuW+iGencEXsdJ0au2+gKT6N1/jCQaU9RRV9NXr7zUXvQ463Yd9c+fzhXfALdsuAx//b5w44M44taxTK3eGMesZ9ge29\"; ma_ss_64a8dba6-67f3-4fe4-8625-257c4adae014=1751388667910580242.1.1751388713.4.1751388667; tmr_detect=0%7C1751388817057; _ga_M29JC28873=GS2.1.s1751388667$o1$g1$t1751389204$j60$l0$h0; v=1751398388; _avisc=IIBcTHdSTGR6Wbq14rLLvdcpYW9GP/o9MIOGdwQNj0Q=; v=1751398388' \
--header 'Pragma:  no-cache' \
--header 'Priority:  u=0, i' \
--header 'Sec-ch-ua:  \"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"' \
--header 'Sec-ch-ua-mobile:  ?0' \
--header 'Sec-ch-ua-platform:  \"Linux\"' \
--header 'Sec-fetch-dest:  document' \
--header 'Sec-fetch-mode:  navigate' \
--header 'Sec-fetch-site:  same-origin' \
--header 'Sec-fetch-user:  ?1' \
--header 'Upgrade-insecure-requests:  1' \
--header 'User-agent:  Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36' --compressed"

        print(query)

        res = subprocess.run(
            query, shell=True, stdout=subprocess.PIPE, encoding="utf-8"
        )
        txt = res.stdout
        print(txt)
        json_content = json.loads(txt)
        print(json_content)

        return json_content

    # проверка количества товаров у продавца
    def check_seller(self, seller_id):
        query = f"{avito_urls['seller_info']}&sellerId={seller_id}"
        response = requests.get(query, headers=self.headers).json()

        if response["result"]["categoryTree"]["count"] > 10:
            return False
        return True

    # метод обработки информации о полученных товарах
    async def search(self):
        self.load_cookies()
        datenow = (
            datetime.now().date().strftime("%d.%m.%Y")
        )  # получение сегодняшней даты
        # sheets_manager = sheets.SheetsManager()  # создание экземпляра класса для работы с google sheets
        page = 0  # страница поиска
        try:
            json_content = self.search_item(page)  # получение списка товаров
        except Exception as e:
            logger.error(
                f"request to avito error: {e}"
            )  # запись ошибибки получения товаров

        for item in json_content["result"]["items"]:
            if item["type"] == "item":  # проверка что это именно товар, а не услуга
                if (
                    item["value"]["id"] not in self.items_ids
                    and item["type"] == "item"
                    and "за услугу" not in item["value"]["price"]
                ):  # валидация товара
                    self.items_ids.append(item["value"]["id"])  # сохранение id товара
                    item_val = item["value"]  # получение основной информации о товаре
                    if True:  # проверка продавца
                        if False:
                            try:
                                asyncio.run(
                                    bot.send_msg(
                                        f"Появился новый товар!\n"
                                        f"Название: {item_val['title']}\n"
                                        f"Цена: {item_val['price']}\n"
                                        f"Время появления: {datetime.fromtimestamp(item_val['time']).strftime('%d.%m.%Y')}\n"
                                        f"Ссылка: {'https://avito.ru' + item_val['uri']}"
                                    )
                                )  # вызов функции для отправки сообщения в тг канал
                            except Exception as e:
                                logger.error(
                                    f"telegram bot error: {e}"
                                )  # логгирование ошибки об отправке сообщения ботом

                        # добавление информации о товаре для дальнейшего обновления таблицы
                        # sheets_manager.add_row(
                        #     [item_val['title'], item_val['price']['current'], "-", 'https://avito.ru' + item_val['uri'],
                        #      item_val["sellerInfo"]["name"]])
                        async with async_session_maker() as session:
                            stmt = insert(Announcement).values(
                                title=item_val['title'],
                                description="",
                                price=item_val['price']['current'],
                                url='https://avito.ru' + item_val['uri'],
                                publication_date=datetime.fromtimestamp(item_val['time']).strftime('%d.%m.%Y'),
                            )
                            stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
                            await session.execute(stmt)
                            await session.commit()

        # sheets_manager.push_rows()  # загрузка всех полученных товаров в таблицу


class AvitoManager:
    def __init__(self):
        pass

    async def run_tasks(self):
        while True:
            async with async_session_maker() as session:
                stmt = select(ParserTask).where(ParserTask.status == "avito")
                tasks = (await session.execute(stmt)).all()
                if not tasks:
                    print("no tasks\n")
                else:
                    for task in tasks:
                        data = task[0].search_query
                        p = AvitoParser()
                        p.get_params(
                            item_name=data["item_name"],
                            region_name=data["region_name"],
                            last_time_str=data["last_time_str"],
                            min_price=data["min_price"],
                            max_price=data["max_price"],
                        )
                        await p.search()
            await asyncio.sleep(60)


def main():
    logger.info("Started")
    loop = asyncio.new_event_loop()
    p = AvitoManager()
    loop.run_until_complete(p.run_tasks())


if __name__ == "__main__":
    main()
