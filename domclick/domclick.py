import asyncio
import subprocess
import time

import requests
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from main.database import async_session_maker
from main.models import BotUser, Announcement, ParserTask, AnnouncementToTask


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
        task_id: int
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

        if price_lims[0]:
            self.price_low = f"&{deal_type}_price__gte={price_lims[0]}"
        if price_lims[1]:
            self.price_up = f"&{deal_type}_price__lte={price_lims[1]}"

    async def search(self):
        query = (
            f"curl --location 'https://domclick.ru/search?{self.deal_type}{self.offer_types}{self.location}{self.price_low}{self.price_up}{self.rooms}"
            + "&category=living&sort=published&sort_dir=desc&offset=0' \
            --compressed \
            --header 'Accept:  text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
            --header 'Accept-Encoding:  gzip, deflate, br, zstd' \
            --header 'Accept-Language:  en-US,en;q=0.9' \
            --header 'Cache-Control:  no-cache' \
            --header 'Connection:  keep-alive' \
            --header 'Cookie:  ns_session=5db24a92-b7c3-4363-9a9b-44f67da36e53; _ym_uid=1750423075881510308; _ym_d=1750423075; adtech_uid=0e7da55a-309c-46ae-92e4-1309793e801e%3Adomclick.ru; top100_id=t1.7711713.835120196.1750423075263; adrcid=AsU3Ah-dHTtMeH3Nt4DiO0w; RETENTION_COOKIES_NAME=ee1da5b936f34d0386d971a2493962b9:y6rC-8oWZTd2iiNHE5xC69MLxzo; sessionId=a0c417c3aa7746868922ea312a636d56:4XYZLExDOAui2IIZHVKeoo4ugv4; UNIQ_SESSION_ID=53f151384f7b49f1835b0c1485ff95ad:g4jcGC1r5Y9FHFL5Cd-X_5AhwnM; is-green-day-banner-hidden=true; is-ddf-banner-hidden=true; logoSuffix=; iosAppLink=; tmr_lvid=56b72ecc18a5806908a336b0853a83f3; tmr_lvidTS=1750423076396; _sv=SV1.4347a3b7-5478-4288-9130-c8b6cd85fedf.1750423040; region={%22data%22:{%22name%22:%22%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%22%2C%22kladr%22:%2277%22%2C%22guid%22:%221d1463ae-c80f-4d19-9331-a1b68a85b553%22}%2C%22isAutoResolved%22:true}; regionAlert=1; iosAppAvailable=true; auto-definition-region=false; ___dmpkit___=d3f1a74c-3bd7-4a3a-a204-03726aa68794; adrcid=AsU3Ah-dHTtMeH3Nt4DiO0w; cookieAlert=1; is-lotto-banner-hidden=true; is-ddd-banner-hidden=true; currentSubDomain=; t3_sid_7711713=s1.1105852233.1751023223085.1751025483436.7.25.2.1; qrator_jsr=v2.0.1751197568.500.59168f536yfxda2e|sF1JTe2DI8LKfFy9|58FjlHTKua9LVQBHQwJQYC7jcw5Ik0DjDwNYH1jnXy80lzwoiU/fPMhuVosQP0CEw13f+Omh6PW5+cK6x/pqdg==-6JkBjA9F9mlbGk0Z+bZyEyvSvcA=-00; qrator_jsid2=v2.0.1751197568.500.59168f536yfxda2e|yjTEFJeAnwbr7Z0d|PUOJdgxm2oR0I9QLD8HBDQw+kNphsY6pHcaTSRUCPLISkNv3hspL7dgiUNInAr4TtVu1H1EhRuyESAfAqBfh02jOB/HPb6v95vUEGI2qb5DcWlvIfLh80zSp6MMfDQh9BJ+zTu9mAinf7K/vdLUKNw==-T4ggUNFuK5vsvSdsE98NtrN7r1E=; currentRegionGuid=7b4698a7-f8b8-424c-9195-e24f3ddb88f3; currentLocalityGuid=7b4698a7-f8b8-424c-9195-e24f3ddb88f3; _ym_isad=2; _sas.2c534172f17069dd8844643bb4eb639294cd4a7a61de799648e70dc86bc442b9=SV1.4347a3b7-5478-4288-9130-c8b6cd85fedf.1750423040.1751197570; regionName=7b4698a7-f8b8-424c-9195-e24f3ddb88f3:%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3; _visitId=4b8aa120-7810-4405-8ae8-3a13c884c6b7-89b4dea43c228e2d; adrdel=1751197570981; adrdel=1751197570981; tmr_detect=0%7C1751197574042; _sas=SV1.4347a3b7-5478-4288-9130-c8b6cd85fedf.1750423040.1751197577; t3_sid_7711713=s1.348188899.1751197570729.1751197639522.8.7.1.1; tmr_reqNum=105' \
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
        with open("data.html", "w") as f:
            f.write(txt)
        soup = BeautifulSoup(txt, features="html.parser")
        blocks = soup.find_all("div", {"class": "YQzvsc"})
        for block in blocks:
            title = " ".join([text.text for text in block.find_all("span", {"class": "_6KKuHL iaB6kz"})])
            description = block.find("div", {"class": "_8MNxzN"}).text
            price = price_str_to_int(block.find("p", {"class": "_5oAgZI Z4r7pA"}).text)
            published = block.find("div", {"class": "MekcYs"}).text
            url = block.find("a", {"class": "Q7TuMJ"}, href=True)["href"]
            img = block.find("img", {"class": "picture-image-object-fit--cover-820-4-0-5 picture-imageFillingContainer-4a2-4-0-5"})
            print(title, price)

            async with async_session_maker() as session:
                stmt = insert(Announcement).values(title=title, description=description, price=price, url=url, publication_date=published)
                stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
                await session.execute(stmt)
                announcement_id = (await session.execute(select(Announcement.id).where(Announcement.url == url))).first()[0]
                print(announcement_id)
                stmt = insert(AnnouncementToTask).values(announcement_id=announcement_id, task_id=self.task_id, uniq_val=f"{announcement_id}-{self.task_id}")
                stmt = stmt.on_conflict_do_nothing(index_elements=["uniq_val"])
                await session.execute(stmt)
                await session.commit()


class DomclickManager:
    def __init__(self):
        pass

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
                            task_id=task[0].id
                        )
                        await p.search()
            await asyncio.sleep(60)


def main():
    loop = asyncio.new_event_loop()
    p = DomclickManager()
    loop.run_until_complete(p.run_tasks())



if __name__ == "__main__":
    main()