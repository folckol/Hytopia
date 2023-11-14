
import json
import random
import ssl
import threading
import time
import traceback
import capmonster_python
import cloudscraper
import requests
import warnings
import nickname_generator

import ua_generator

from utils.logger import MultiThreadLogger

warnings.filterwarnings("ignore", category=DeprecationWarning)



class RequestModel:

    def __init__(self, number, proxy, email, cap_key, refCode = None, logger=None):
        self.number = number
        self.logger = logger
        self.email = email
        self.refCode = refCode
        self.capKey = cap_key

        self.ua = self.generate_user_agent

        self.session = self._make_scraper
        self.proxy = proxy
        self.session.proxies = {"http": f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}",
                                "https": f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"}
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        self.session.headers.update({"user-agent": self.ua,
                                     'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'})

    def CheckUsername(self, username):

        with self.session.get("https://preregister.hytopia.com/{}?username={}&_data={}".format(f"{self.refCode}" if self.refCode != None else "",
                                                                                                username,
                                                                                               "player-by-referrer" if self.refCode != None else "routes%2F_index")) as response:

            if json.loads(response.text.split("\n")[0])["usernameAvailable"]:
                self.logger.info(f"{self.number} | Никнейм {username} свободен")
            else:
                self.logger.info(f"{self.number} | Никнейм {username} свободен")

            return json.loads(response.text.split("\n")[0])["usernameAvailable"]

    def Registration(self, nickname):

        payload = {"username": nickname,
                   "email": self.email,
                   "g-recaptcha-response": self.SolveCaptcha}
        self.logger.info(f"{self.number} | Капча решена")

        with self.session.post("https://preregister.hytopia.com/{}?_data={}".format(f"{self.refCode}" if self.refCode != None else "",
                                                                                    "player-by-referrer" if self.refCode != None else "routes%2F_index"), data=payload) as response:

            return response.json()["success"]

    @property
    def SolveCaptcha(self) -> str:
        cap = capmonster_python.RecaptchaV3Task(self.capKey)
        tt = cap.create_task("https://preregister.hytopia.com/", '6LccsxkoAAAAAM8JaxrLyR0uh9zz4mYE5Y00hR-5')
        captcha = cap.join_task_result(tt)
        captcha = captcha["gRecaptchaResponse"]

        return captcha

    @property
    def generate_user_agent(self) -> str:
        return ua_generator.generate(device='desktop',platform = 'windows', browser='chrome').text

    @property
    def _make_scraper(self):
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers(
            "ECDH-RSA-NULL-SHA:ECDH-RSA-RC4-SHA:ECDH-RSA-DES-CBC3-SHA:ECDH-RSA-AES128-SHA:ECDH-RSA-AES256-SHA:"
            "ECDH-ECDSA-NULL-SHA:ECDH-ECDSA-RC4-SHA:ECDH-ECDSA-DES-CBC3-SHA:ECDH-ECDSA-AES128-SHA:"
            "ECDH-ECDSA-AES256-SHA:ECDHE-RSA-NULL-SHA:ECDHE-RSA-RC4-SHA:ECDHE-RSA-DES-CBC3-SHA:ECDHE-RSA-AES128-SHA:"
            "ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-NULL-SHA:ECDHE-ECDSA-RC4-SHA:ECDHE-ECDSA-DES-CBC3-SHA:"
            "ECDHE-ECDSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA:AECDH-NULL-SHA:AECDH-RC4-SHA:AECDH-DES-CBC3-SHA:"
            "AECDH-AES128-SHA:AECDH-AES256-SHA"
        )
        ssl_context.set_ecdh_curve("prime256v1")
        ssl_context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1_3 | ssl.OP_NO_TLSv1)
        ssl_context.check_hostname = False

        return cloudscraper.create_scraper(
            debug=False,
            ssl_context=ssl_context
        )

def RandomNickname():
    return nickname_generator.generate()


def split_list_into_n_sublists(lst, N):
    avg_len = len(lst) // N
    remain = len(lst) % N

    start = 0
    sublists = []

    for i in range(N):
        end = start + avg_len + (1 if i < remain else 0)
        sublists.append(lst[start:end])
        start = end

    return sublists

def Thread_(thread_number, list_):

    logger = MultiThreadLogger(thread_number)

    localRefCode = None
    startRefCount = 0
    randomRefCount = None

    c = 1
    for i in list_:

        if localRefCode == None or startRefCount == randomRefCount:
            randomRefCount = random.randint(refCount[0], refCount[1])
            startRefCount = 0

        try:
            account = RequestModel(number=c,
                                   proxy=i[0],
                                   email=i[1],
                                   cap_key=capKey,
                                   refCode=localRefCode if localRefCode != None else refCode if refCode != "" else None,
                                   logger=logger)

            while True:
                nickname = RandomNickname()

                if account.CheckUsername(nickname):
                    break

                time.sleep(1)

            status = account.Registration(nickname)

            if not status:
                logger.error(f"{c} | Неудалось зарегистрировать аккаунт")

            else:

                if localRefCode == None:
                    localRefCode = nickname
                    logger.success(f'{c} | Зарегистрирован рефовод. Код - {localRefCode}')

                else:
                    startRefCount += 1
                    logger.success(f'{c} | Реферал {startRefCount}/{randomRefCount} зарегистрирован')

        except Exception as e:

            logger.error(f"{c} | Ошибка регистрации аккаунта ({str(e)})")

        logger.skip()

        time.sleep(random.randint(delay[0],delay[1]))
        c+=1

if __name__ == '__main__':

    print(' ___________________________________________________________________\n'
          '|                       Rescue Alpha Soft                           |\n'
          '|                   Telegram - @rescue_alpha                        |\n'
          '|                   Discord - discord.gg/438gwCx5hw                 |\n'
          '|___________________________________________________________________|\n\n\n')

    refCount = (1, 5)
    delay = (15, 45)
    threadsCount = 1
    capKey = ""
    refCode = ""

    try:
        with open('config', 'r', encoding='utf-8') as file:
            for i in file:

                if 'refCount=' in i.rstrip():
                    refCount = (int(i.rstrip().split('refCount=')[-1].split('-')[0]), int(i.rstrip().split('refCount=')[-1].split('-')[1]))
                if 'refCode=' in i.rstrip():
                    refCode = i.rstrip().split('refCode=')[-1]
                if 'threadsCount=' in i.rstrip():
                    threadsCount = int(i.rstrip().split('threadsCount=')[-1])
                if 'capmonster=' in i.rstrip():
                    capKey = i.rstrip().split('capmonster=')[-1]
                if 'delay=' in i.rstrip():
                    delay = (int(i.rstrip().split('delay=')[-1].split('-')[0]),
                                int(i.rstrip().split('delay=')[-1].split('-')[1]))

    except:

        print('Вы неправильно настроили конфигуратор, повторите попытку')
        input()
        exit(0)

    # print(capKey)

    proxies = []
    emails = []

    with open('InputData/Proxies.txt', 'r') as file:
        for i in file:
            proxies.append(i.rstrip())
    with open('InputData/Emails.txt', 'r') as file:
        for i in file:
            emails.append(i.rstrip().split(':')[0])

    data = []
    for i in range(len(proxies)):
        data.append([proxies[i], emails[i]])

    newData = split_list_into_n_sublists(data, threadsCount)

    threads = []

    for i in range(threadsCount):
        threads.append(threading.Thread(target=Thread_, args=(i+1, newData[i])))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    input('Скрипт завершил работу...')


