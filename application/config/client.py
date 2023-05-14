"""Config of DBS"""

from pydantic import BaseSettings, Field, HttpUrl

from .application import ApplicationSettings

SBER_DEFAULT_URL = 'https://sbermegamarket.ru'
SBER_DEFAULT_TEST_URL = 'https://web.goodsteam.tech'
DEFAULT_POOL_SIZE = 3


class ParserSettings:
    url: HttpUrl
    pool_size: int
    has_headless: bool = True
    has_proxies: bool = True
    has_random_useragent: bool = True


class SberSuperMarketParserSettings(BaseSettings):
    """Sber supermarket parser env values"""

    url: HttpUrl = Field(default=SBER_DEFAULT_URL, env='SBER_SUPERMARKET_URI')
    pool_size: int = Field(default=DEFAULT_POOL_SIZE, env='SBER_PARSER_POOL_SIZE')
    has_headless: bool = True
    has_proxies: bool = True
    has_random_useragent: bool = True

    @classmethod
    def generate(cls):
        """Generate SberParser settings (with sqlite if tests)"""
        application_settting = ApplicationSettings()
        if application_settting.is_test:
            return SberSuperMarketParserSettings(url=SBER_DEFAULT_TEST_URL)
        return SberSuperMarketParserSettings()
