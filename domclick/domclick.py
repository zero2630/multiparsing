import asyncio
import subprocess

import requests
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert


def price_str_to_int(price):
    print(int(price[:price.find("₽")].replace(" ", "")))


class DomclickParser:
    def __init__(
        self,
        offer_types: list[str],
        rooms: list[str],
        price_lims: list[int],
        deal_type: str,
        location: int,
    ):

        self.offer_types: str = "".join(
            [f"&offer_type={offer_types[i]}" for i in range(len(offer_types))]
        )
        self.rooms: str = "".join([f"&rooms={rooms[i]}" for i in range(len(rooms))])
        self.location: str = f"&aids={location}"
        self.deal_type: str = f"deal_type={deal_type}"
        self.price_low: str = ""
        self.price_up: str = ""
        self.active: bool = True

        if price_lims[0]:
            self.price_low = f"&{deal_type}_price__gte={price_lims[0]}"
        if price_lims[1]:
            self.price_up = f"&{deal_type}_price__lte={price_lims[1]}"

    async def search(self):
        query = (
            f"curl --location 'https://domclick.ru/search?{self.deal_type}{self.offer_types}{self.location}{self.price_low}{self.price_up}{self.rooms}"
            + "&category=living&sort=published&sort_dir=desc&offset=0' \
        --header 'Accept:  text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
        --header 'Accept-Encoding:  gzip, deflate, br, zstd' \
        --header 'Accept-Language:  ru' \
        --header 'Cache-Control:  max-age=0' \
        --header 'Connection:  keep-alive' \
        --header 'Cookie:  ns_session=2b6ed433-8fca-46b3-a920-ec68cb0dd957; RETENTION_COOKIES_NAME=2608b6a465f34932a3ca179716216078:gebvfIP-8dXlh0lXi9sNQHthvYQ; sessionId=e40b9560ed0a4ef1af66d0fbdceab62e:-bYl2M0UF4Qtag-kcMtvn_EGRxA; UNIQ_SESSION_ID=e530411f5efe4baab4173a3efe93079f:y8wKUyyfdcHoq2F-YATVxSFPYMQ; is-green-day-banner-hidden=true; is-ddf-banner-hidden=true; _ym_uid=1750664453215549468; _ym_d=1750664453; logoSuffix=; iosAppLink=; _ym_isad=2; ___dmpkit___=02218970-ef99-4a96-9094-52101856fba8; adtech_uid=d0ec572d-ec13-4df0-9a57-dee782990bd3%3Adomclick.ru; top100_id=t1.7711713.1198048448.1750664453594; region={%22data%22:{%22name%22:%22%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%22%2C%22kladr%22:%2277%22%2C%22guid%22:%221d1463ae-c80f-4d19-9331-a1b68a85b553%22}%2C%22isAutoResolved%22:true}; _sv=SV1.106a5417-3a0f-42ed-9580-6322173e1f83.1750664448; autoDefinedRegion=1d1463ae-c80f-4d19-9331-a1b68a85b553:1d1463ae-c80f-4d19-9331-a1b68a85b553:%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0:; tmr_lvid=6479d3e3d58e595e507acd918c6b1d15; tmr_lvidTS=1750664454519; adrdel=1750664457538; adrcid=A6UoYfSrq6eXjayFuzR-JRQ; iosAppAvailable=true; is-lotto-banner-hidden=true; is-ddd-banner-hidden=true; tmr_detect=0%7C1750667001442; tmr_reqNum=16; qrator_jsr=v2.0.1750674726.068.5e19ade7eAU36ayB|qgOy5PVD4TAEiAiN|C/6b8nu4Qsor4VkMXHzRmi4fcknJmvrpOYiVHrbViO55GsbwTH/V5+F08zAruWUPTOYSE9UzVtvLIxaK79wmZg==-xdPrqgxp3PXlVTTDAMHBvsZCBRk=-00; t3_sid_7711713=s1.816248871.1750674554627.1750674726143.2.6.0.1; _sas.2c534172f17069dd8844643bb4eb639294cd4a7a61de799648e70dc86bc442b9=SV1.106a5417-3a0f-42ed-9580-6322173e1f83.1750664448.1750674726; _sas=SV1.106a5417-3a0f-42ed-9580-6322173e1f83.1750664448.1750674726; qrator_jsid2=v2.0.1750674726.068.5e19ade7eAU36ayB|UrAvQwJVInCX9IQa|0m1DTHy+L++6oywPgRjTAnj7UUqeg+9JskWo+ioNuCnxsS6OzqkhkQOA9MoX98uzbCDkG8xY10zvoCqu/3GBrzaHX30UI8cIJWWQZFR3p4/L49NbjkrR9us1uIUYsTTRdDKErMjsIz93O9V3PjbE5Q==-9maIGtkjlJ5gQBby4QgS6yVhxIc=' \
        --header 'Host:  domclick.ru' \
        --header 'Referer:  https://domclick.ru/?utm_referrer=https%3A%2F%2Fwww.google.com%2F' \
        --header 'Sec-Fetch-Dest:  document' \
        --header 'Sec-Fetch-Mode:  navigate' \
        --header 'Sec-Fetch-Site:  same-origin' \
        --header 'Sec-Fetch-User:  ?1' \
        --header 'Upgrade-Insecure-Requests:  1' \
        --header 'User-Agent:  Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36' \
        --header 'sec-ch-ua:  \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"' \
        --header 'sec-ch-ua-mobile:  ?0' \
        --header 'sec-ch-ua-platform:  \"Linux\"' \
        --compressed"
        )

        while self.active:
            res = subprocess.run(
                query, shell=True, stdout=subprocess.PIPE, encoding="utf-8"
            )
            txt = res.stdout
            soup = BeautifulSoup(txt, features="html.parser")
            blocks = soup.find_all("div", {"class": "YQzvsc"})
            for block in blocks:
                title = " ".join([text.text for text in block.find_all("span", {"class": "_6KKuHL iaB6kz"})])
                description = block.find("div", {"class": "_8MNxzN"}).text
                price = block.find("p", {"class": "_5oAgZI Z4r7pA"})
                published = block.find("div", {"class": "MekcYs"})
                url = block.find("a", {"class": "Q7TuMJ"}, href=True)
                price_str_to_int(price.text)
                print(price.text)
                # print(price.text)
                # print(desc)
                # for text in texts:
                #     print(text.text, end=" ")
                print("")

            await asyncio.sleep(10)


class DomclickManager:
    def __init__(self):
        self.tasks = {}
        self.loop = asyncio.get_event_loop()

    def new_task(self, offer_types, rooms, price_lims, deal_type, location):
        str_uid = f"{offer_types} - {rooms} - {price_lims} - {deal_type} - {location}"
        if str_uid not in self.tasks:
            self.tasks[str_uid] = DomclickParser(offer_types, rooms, price_lims, deal_type, location)
            asyncio.run(self.tasks[str_uid].search())

    def stop_task(self, offer_types, rooms, price_lims, deal_type, location):
        self.tasks[str_uid].is_active = False


p = DomclickManager()
p.new_task(
    ["flat"],
    ["st"],
    [None, None],
    "sale",
    2299,
)
