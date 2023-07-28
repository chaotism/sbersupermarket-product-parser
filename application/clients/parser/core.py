from enum import Enum
from datetime import datetime
from queue import Queue
from pathlib import Path
from typing import Optional

import undetected_chromedriver as uc
from loguru import logger
from pydantic import HttpUrl
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By as SeleniumBy
from selenium.webdriver.remote.webelement import WebElement

from clients.parser.proxies import get_proxy
from clients.parser.useragent import get_useragent
from common.errors import ClientError
from common.utils import retry_by_exception
from config.client import ParserSettings

DEFAULT_TIME_TO_WAIT = 3


class By(Enum):  # could be rewritten by Enum from dict
    CLASS_NAME = SeleniumBy.CLASS_NAME
    XPATH = SeleniumBy.XPATH
    ID = SeleniumBy.ID


class LoadStrategies(Enum):
    NORMAL = 'normal'  # default WebDriver waits until the load event fire is returned.
    EAGER = 'eager'  # WebDriver waits until DOMContentLoaded event fire is returned.
    NONE = 'none'  # WebDriver only waits until the initial page is downloaded.


def get_web_driver(
    headless: bool = True,
    page_load_strategy: Optional[LoadStrategies] = None,
    user_data_dir: Optional[Path] = None,
    useragent: Optional[str] = None,
    proxy: Optional[str] = None,
    experimental_options: bool = False,
    chrome_version_main: Optional[int] = None,
) -> uc.Chrome:
    options = uc.ChromeOptions()

    if headless:
        options.add_argument('--headless')
    if page_load_strategy:
        options.page_load_strategy = page_load_strategy.value

    if user_data_dir:
        logger.debug(f'Use user_data_dir: {user_data_dir}')
        options.user_data_dir = str(user_data_dir)
    if useragent:
        logger.debug(f'Use useragent: {useragent}')
        options.add_argument(
            f'--user-agent={useragent}'
        )  # could make driver detectable
    if proxy:
        logger.debug(f'Use proxy: {proxy}')
        options.add_argument(f'--proxy-server={proxy}')  # could make driver detectable

    if experimental_options:  # TODO:  experimental_options could break chrome driver
        logger.debug(f'Use experimental_options: {experimental_options}')
        options.add_argument('--single-process')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-gpu')

    chrome = uc.Chrome(
        advanced_elements=True, options=options, version_main=chrome_version_main
    )
    chrome.maximize_window()
    chrome.implicitly_wait(time_to_wait=DEFAULT_TIME_TO_WAIT)
    return chrome


class BaseParser:
    """
    Base wrapper on undetectable chromium.
    """

    RETRY_COUNT = 3

    config: Optional[ParserSettings] = None
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
            page_load_strategy=(
                LoadStrategies.NONE if config.has_fast_load_strategy else None
            ),
            useragent=get_useragent() if config.has_random_useragent else None,
            proxy=get_proxy() if config.has_proxies else None,
            experimental_options=config.has_experimental_options,
            chrome_version_main=config.chrome_version,
            user_data_dir=config.chrome_data_dir,
        )
        self.client = client
        logger.info('Chrome client ready')

    @retry_by_exception(
        exceptions=(WebDriverException, TimeoutException, TimeoutError), max_tries=3
    )
    def close_client(self):
        if not self.is_inited:
            logger.warning('Chrome client is not inited')
            return
        logger.info('Start closing client...')
        try:
            if isinstance(self.client, uc.Chrome):
                self.client.close()
                self.client.quit()
        except WebDriverException as err:
            logger.warning(f'Get problem with closing chrome driver: {str(err)}')
            if 'failed to check if window was closed' not in str(err):
                raise
        logger.info('Client closed')
        self.client = None

    def restart(self):
        self.close_client()
        self.init(self.config)

    def get_page(self, url: HttpUrl) -> uc.Chrome:
        if not self.is_inited:
            raise ClientError(f'{self.__class__.__name__} is not inited')
        assert isinstance(self.client, uc.Chrome)

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
            raise ClientError(f'{self.__class__.__name__} is not inited')
        logger.debug(f'Get elements by {by} with value {name}')
        for _ in range(self.RETRY_COUNT):
            try:
                elements = self.client.find_elements(by.value, name)  # type: ignore[union-attr]
                if not elements:
                    continue
                return elements
            except TimeoutException as err:
                logger.warning(
                    f'Get webdriver exception {str(err)} try to restart client'
                )
                self.restart()
            except WebDriverException as err:
                logger.warning(
                    f'Get webdriver exception {str(err)} try to restart client'
                )
                self.restart()
        return []

    def get_screenshot(self):
        log_folder_path = Path(self.config.log_folder)  # type: ignore[union-attr]
        if not log_folder_path.exists():
            log_folder_path.mkdir(parents=True)
        name = Path(self.client.current_url).name  # type: ignore[union-attr]
        self.client.save_screenshot(  # type: ignore[union-attr]
            f'{log_folder_path.absolute()}/{name}-{datetime.utcnow()}.png'
        )


class ParserPool:
    config: Optional[ParserSettings] = None
    pool: Optional[Queue] = None

    @property
    def is_inited(self):
        return (
            self.config is not None and self.pool is not None and not self.pool.empty()
        )

    def init(self, config: ParserSettings):
        if self.is_inited:
            logger.info('Already inited')
            return

        self.config = config
        self.pool = Queue(maxsize=self.config.pool_size)

        for _ in range(self.pool.maxsize):
            parser = BaseParser()
            parser.init(self.config)

            self.pool.put(parser)  # type: ignore[union-attr]

    def close(self):
        if not self.is_inited:
            logger.warning('Pool is not inited')
            return

        while not self.pool.empty():  # type: ignore[union-attr]
            parser = self.pool.get()  # type: ignore[union-attr]
            parser.close_client()

    def get(self) -> BaseParser:
        if not self.is_inited:
            raise ClientError('Pool is not inited')

        return self.pool.get()  # type: ignore[union-attr]

    def put(self, parser: BaseParser):
        if self.pool is None:
            raise ClientError('Pool is not inited')

        return self.pool.put(parser)  # type: ignore[union-attr]


parser_pool = ParserPool()
