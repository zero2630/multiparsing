import asyncio
import subprocess

import requests
from bs4 import BeautifulSoup


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
        --header 'Cookie:  ns_session=26fa591d-e840-412b-805d-7f1dfa05de57; RETENTION_COOKIES_NAME=bdfceb74d16f41a784fff5be181ee245:2cBTC3YfjqDTKS4268kkSzINl5s; sessionId=61273146bd344a5fb366db51c95b25e2:w5HtnkOXBfID1zuHYwWZsKO1qpQ; UNIQ_SESSION_ID=dc8f1f4329314d23be19ee209fee6a24:a12bU-YF-TH98nWp2cpCayCDDgA; is-green-day-banner-hidden=true; is-ddf-banner-hidden=true; _ym_uid=1750357480254316545; _ym_d=1750357480; logoSuffix=; iosAppLink=; region={%22data%22:{%22name%22:%22%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%22%2C%22kladr%22:%2277%22%2C%22guid%22:%221d1463ae-c80f-4d19-9331-a1b68a85b553%22}%2C%22isAutoResolved%22:true}; ___dmpkit___=97312c75-8353-4e31-9630-ed67ecb8d188; adtech_uid=66ff27b4-585a-4bda-85b2-5242f64ecc55%3Adomclick.ru; top100_id=t1.7711713.624246709.1750357480212; _sv=SV1.15b5e506-2145-49a9-99bf-52b42b32af25.1750357504; adrcid=AtJRv9YZY062RbOPALSJIEQ; iosAppAvailable=true; tmr_lvid=306cee3be45f4c50f043498dfc39a159; tmr_lvidTS=1750357656518; qrator_jsr=v2.0.1750516050.391.59168f1bpc7NdfVW|LYhCZRl8JJJzffTN|DPwbGWacqws6tAy4NOKXVmZkrQZvzIWApJ17GsfrUwrloU/52HglbWWjktGyWkHCUt2av4xkmdFz0IPnev7itA==-6PzjmB5SEy6Y65PrxWGVTEbnvmI=-00; qrator_jsid2=v2.0.1750516050.391.59168f1bpc7NdfVW|kFeOJhC26XAYhr1H|R9aOqd3zrEV9MioviV6nvBt4+GFpUnGaWFMnpxtes8Ce9ngsALta8Dgq3ahWIzUNnAblRhSn0PAGdqAO/kURvOqWiJ5t63Y2pr4D/AgNzcId7fVxMB8r+3OUU9qPc0jygON731HdLEPw+QIhMdNxMw==-lnl9e4D26fdIARc14eJRT+9gF/Q=; _ym_isad=2; _sas.2c534172f17069dd8844643bb4eb639294cd4a7a61de799648e70dc86bc442b9=SV1.15b5e506-2145-49a9-99bf-52b42b32af25.1750357504.1750516052; _visitId=d9a7218f-7e36-43c6-970e-b769331668fe-f4f0dcc432ac8ba6; adrdel=1750516052661; autoDefinedRegion=1d1463ae-c80f-4d19-9331-a1b68a85b553:1d1463ae-c80f-4d19-9331-a1b68a85b553:%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0:; tmr_detect=0%7C1750516055287; t3_sid_7711713=s1.935314493.1750516052043.1750516066433.2.5.1.0; tmr_reqNum=8' \
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
                texts = block.find_all("span", {"class": "_6KKuHL iaB6kz"})
                for text in texts:
                    print(text.text, end=" ")
                print("")

            await asyncio.sleep(10)


class DomclickManager:
    def __init__(self):
        self.tasks = {}
        self.loop = asyncio.get_event_loop()

    def new_task(self, offer_types, rooms, price_lims, deal_type, location):
        str_uid = f"{offer_types} - {rooms} - {price_lims} - {deal_type} - {location}"
        if str_uid not in self.tasks:
            self.tasks[str_uid] = DomClickTask(offer_types, rooms, price_lims, deal_type, location)
            self.loop.create_task(self.tasks[str_uid].search())

    def stop_task(self, offer_types, rooms, price_lims, deal_type, location):
        self.tasks[str_uid].is_active = False


p = DomClickParser()
p.new_task(
    ["flat"],
    ["st"],
    [None, None],
    "rent",
    2299,
)
