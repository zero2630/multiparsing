import asyncio
import subprocess
import time

import requests
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from main.database import async_session_maker
from main.models import BotUser, Announcement, ParserTask, AnnouncementToTask
from domclick import cookie_generator


def price_str_to_int(price):
    return int(price[:price.find("₽")].replace(" ", ""))


class DomclickParser:
    def __init__(
        self,
        offer_types: list[str],
        rooms: list[str],
        price_lims: list[int],
        deal_type: str,
        location: int,
        task_id: int,
        cookies: str
    ):

        self.offer_types: str = "".join(
            [f"&offer_type={offer_types[i]}" for i in range(len(offer_types))]
        )
        self.rooms: str = "".join([f"&rooms={rooms[i]}" for i in range(len(rooms))])
        self.location: str = f"&aids={location}"
        self.deal_type: str = f"deal_type={deal_type}"
        self.price_low: str = ""
        self.price_up: str = ""
        self.task_id: int = task_id
        self.cookies = cookies

        if price_lims[0]:
            self.price_low = f"&{deal_type}_price__gte={price_lims[0]}"
        if price_lims[1]:
            self.price_up = f"&{deal_type}_price__lte={price_lims[1]}"

    async def search(self):
        query = (
            f"curl --location 'https://domclick.ru/search?{self.deal_type}{self.offer_types}{self.location}{self.price_low}{self.price_up}{self.rooms}"
            + f"&category=living&sort=published&sort_dir=desc&offset=0' \
            --compressed \
            --header 'Accept:  text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
            --header 'Accept-Encoding:  gzip, deflate, br, zstd' \
            --header 'Accept-Language:  en-US,en;q=0.9' \
            --header 'Cache-Control:  no-cache' \
            --header 'Connection:  keep-alive' \
            --header 'Cookie:  {self.cookies}' \
            --header 'Host:  spb.domclick.ru' \
            --header 'Pragma:  no-cache' \
            --header 'Sec-Fetch-Dest:  document' \
            --header 'Sec-Fetch-Mode:  navigate' \
            --header 'Sec-Fetch-Site:  same-origin' \
            --header 'Sec-Fetch-User:  ?1' \
            --header 'Upgrade-Insecure-Requests:  1' \
            --header 'User-Agent:  Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36' \
            --header 'sec-ch-ua:  \"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"' \
            --header 'sec-ch-ua-mobile:  ?0' \
            --header 'sec-ch-ua-platform:  \"Linux\"'"
        )

        res = subprocess.run(
            query, shell=True, stdout=subprocess.PIPE, encoding="utf-8"
        )
        txt = res.stdout
        soup = BeautifulSoup(txt, features="html.parser")
        blocks = soup.find_all("div", {"class": "QDlRf Zp23N F7nvl"})
        for block in blocks:
            title = " ".join([text.text for text in block.find_all("span", {"class": "_6KKuHL iaB6kz"})])
            description = block.find("div", {"class": "_8MNxzN"}).text
            price = price_str_to_int(block.find("p", {"class": "_5oAgZI Z4r7pA"}).text)
            published = block.find("div", {"class": "MekcYs"}).text
            url = block.find("a", {"class": "Q7TuMJ"}, href=True)["href"]
            img = block.find("img", {"class": "picture-image-object-fit--cover-820-4-0-5 picture-imageFillingContainer-4a2-4-0-5"})["src"]

            seller_name = block.find("div", {"class": "PeBtRI"})
            seller_name = None if not seller_name else seller_name.text

            seller_status = block.find("span", {"class": "x6J2nk"})
            seller_status = None if not seller_status else seller_status.text

            address = block.find("span", {"class": "S4xsAI"})
            address = None if not address else address.text

            metro_name = block.find("span", {"class": "gzUns0"})
            metro_name = None if not metro_name else metro_name.text

            print(title, price, seller_status, seller_name, address, metro_name)

            async with async_session_maker() as session:
                stmt = insert(Announcement).values(title=title, description=description, price=price, url=url, publication_date=published, img_url=img, status="domclick")
                stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
                await session.execute(stmt)
                announcement_id = (await session.execute(select(Announcement.id).where(Announcement.url == url))).first()[0]
                stmt = insert(AnnouncementToTask).values(announcement_id=announcement_id, task_id=self.task_id, uniq_val=f"{announcement_id}-{self.task_id}")
                stmt = stmt.on_conflict_do_nothing(index_elements=["uniq_val"])
                await session.execute(stmt)
                await session.commit()


class DomclickManager:
    def __init__(self):
        cookie_generator.update_cookies("https://domclick.ru/search?deal_type=sale&offer_type=flat&offer_type=layout&category=living&aids=2299")
        with open("./domclick/cookies_tmp.txt", "r") as f:
            cookies = f.read()
        self.cookies = cookies

    async def run_tasks(self):
        while True:
            async with async_session_maker() as session:
                stmt = select(ParserTask).where(ParserTask.status == "domclick")
                tasks = (await session.execute(stmt)).all()
                if not tasks:
                    print("no tasks\n")
                else:
                    for task in tasks:
                        data = task[0].search_query
                        p = DomclickParser(
                            offer_types=["flat"],
                            rooms=["st"],
                            price_lims=data["price_lims"],
                            deal_type=data["deal_type"],
                            location=2299,
                            task_id=task[0].id,
                            cookies=self.cookies
                        )
                        await p.search()
            cookie_generator.update_cookies("https://domclick.ru/search?deal_type=sale&offer_type=flat&offer_type=layout&category=living&aids=2299")
            with open("./domclick/cookies_tmp.txt", "r") as f:
                self.cookies = f.read()
            await asyncio.sleep(60)


def main():
    loop = asyncio.new_event_loop()
    p = DomclickManager()
    loop.run_until_complete(p.run_tasks())



if __name__ == "__main__":
    main()