import undetected_chromedriver as uc
from time import sleep

from sqlalchemy.testing.config import options
from xvfbwrapper import Xvfb

from conf import CHROME_VERSION

def update_cookies(url):
    display = Xvfb()
    display.start()

    driver = uc.Chrome(options=options, use_subprocess=False, browser_executable_path="/usr/bin/google-chrome-stable", version_main=int(CHROME_VERSION))
    driver.get(url)
    sleep(10)

    cookies = driver.get_cookies()

    cookies_str = '; '.join([f"{cookies[i]['name']}={cookies[i]['value']}" for i in range(len(cookies))])

    with open("./domclick/cookies_tmp.txt", "w") as f:
        f.write(cookies_str)

    driver.close()

if __name__ == "__main__":
    update_cookies("https://domclick.ru/search?deal_type=sale&offer_type=flat&offer_type=layout&category=living&aids=2299")