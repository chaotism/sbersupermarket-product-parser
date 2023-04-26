from queue import Queue
from typing import Optional

import undetected_chromedriver as uc
from loguru import logger
from pydantic import HttpUrl
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from clients.parser.proxies import get_proxy
from clients.parser.useragent import get_useragent
from common.errors import ProviderError
from common.utils import retry_by_exception
from config.client import ParserSettings

DEFAULT_TIME_TO_WAIT = 3
DEFAULT_POOL_SIZE = 5  # TODO: move to config


def get_web_driver(
    headless: bool = True, proxy: Optional[str] = None, useragent: Optional[str] = None
) -> uc.Chrome:
    options = uc.ChromeOptions()
    # options.user_data_dir = Path(
    #     BASE_PATH, 'var', 'chrome_userdata'
    # )  # TODO: generate user data
    if headless:
        options.add_argument('--headless')

    # TODO:  all commented arguments would break chrome driver or make it detectable
    # if proxy:
    #     options.add_argument(f'--proxy-server={proxy}')
    # if useragent:
    #     options.add_argument(f'--user-agent={useragent}')

    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-setuid-sandbox')
    # options.add_argument('--window-size=1920,1080')
    # options.add_argument('--disable-extensions')
    # options.add_argument('--dns-prefetch-disable')
    # options.add_argument('--disable-gpu')

    chrome = uc.Chrome(options=options)
    chrome.maximize_window()
    chrome.implicitly_wait(time_to_wait=DEFAULT_TIME_TO_WAIT)
    # chrome.set_page_load_timeout(time_to_wait=DEFAULT_TIME_TO_WAIT)
    # assert chrome.is_connectable()
    return chrome


class BaseParser:
    """
    Base wrapper on undetectable chromium.
    """

    RETRY_COUNT = 3

    config: Optional[ParserSettings] = None  # TODO: could remove (its for debug only)
    client: Optional[uc.Chrome] = None

    @property
    def is_inited(self):
        return self.config is not None and self.client is not None

    @retry_by_exception(
        exceptions=(WebDriverException, TimeoutException, TimeoutError), max_tries=3
    )
    def init(self, config: ParserSettings):
        if self.is_inited:
            logger.info('Already inited')
            return
        logger.info('Start initialising chrome client.....')
        self.config = config
        client = get_web_driver(
            headless=config.has_headless,
            useragent=get_useragent() if config.has_random_useragent else None,
            proxy=get_proxy() if config.has_proxies else None,
        )
        self.client = client
        logger.info('Chrome client ready')

    @retry_by_exception(
        exceptions=(WebDriverException, TimeoutException, TimeoutError), max_tries=3
    )
    def close_client(self):  # TODO: migrate to pool
        if not self.is_inited:
            logger.warning('Chrome client is not inited')
            return
        logger.info('Start closing client...')
        try:
            self.client.close()  # FIXME: regular error with losing connection with dev tool
        except WebDriverException as err:
            logger.warning(f'Get problem with closing chrome driver: {str(err)}')
            if 'failed to check if window was closed' not in str(err):
                raise
        self.client.quit()
        logger.info('Client closed')
        self.client = None

    def restart(self):
        self.close_client()
        self.init(self.config)

    def get_page(self, url: HttpUrl) -> uc.Chrome:
        if not self.is_inited:
            raise ProviderError(f'{self.__class__.__name__} is not inited')
        logger.debug(f'Get page {url}')

        for i in range(self.RETRY_COUNT + 1):
            try:
                self.client.get(url)
                logger.debug(
                    f'Current page is {self.client.current_url} with source {self.client.page_source}'
                )
                return self.client
            except (WebDriverException, TimeoutException, TimeoutError) as err:
                logger.warning(
                    f'Get webdriver exception {str(err)} try to restart client'
                )
                if i == self.RETRY_COUNT:
                    raise err
                self.restart()

    def get_elements(self, by: By, name: str) -> list[WebElement]:
        if not self.is_inited:
            raise ProviderError(f'{self.__class__.__name__} is not inited')
        logger.debug(f'Get elements by {by} with value {name}')
        for _ in range(self.RETRY_COUNT):
            try:
                elements = self.client.find_elements(by, name)
                if not elements:
                    continue
                return elements
            except TimeoutException as err:
                logger.warning(
                    f'Get webdriver exception {str(err)} try to restart client'
                )
                self.restart()
            except WebDriverException as err:
                if 'unknown' not in str(err):
                    raise
                logger.warning(
                    f'Get webdriver exception {str(err)} try to restart client'
                )
                self.restart()
        return []


class ParserPool:
    def __init__(self, size: int) -> None:
        self.size = size
        self.pool = Queue(maxsize=size)

    def init(self, config: ParserSettings):
        if not self.pool.empty():
            logger.info('Already inited')
            return

        for _ in range(self.size):
            parser = BaseParser()
            parser.init(config)

            self.pool.put(parser)

    def close(self):
        while not self.pool.empty():
            parser = self.pool.get()
            parser.close_client()

    def get(self) -> BaseParser:
        return self.pool.get()

    def put(self, parser: BaseParser):
        return self.pool.put(parser)


parser_pool = ParserPool(DEFAULT_POOL_SIZE)
