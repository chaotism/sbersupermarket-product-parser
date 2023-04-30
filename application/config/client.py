"""Config for external clients"""

from pydantic import BaseSettings, Field, HttpUrl

SBER_DEFAULT_URL = 'https://sbermegamarket.ru'
DEFAULT_POOL_SIZE = 1


class ParserSettings:
    """Base parse settings"""

    url: HttpUrl
    pool_size: int
    has_headless: bool = True
    has_fast_load_strategy: bool = True
    has_proxies: bool = True
    has_random_useragent: bool = True
    has_experimental_options: bool = False


class SberSuperMarketParserSettings(BaseSettings):
    """Sber supermarket parser env values"""

    url: HttpUrl = Field(default=SBER_DEFAULT_URL, env='SBER_SUPERMARKET_URI')
    pool_size: int = Field(default=DEFAULT_POOL_SIZE, env='SBER_PARSER_POOL_SIZE')
    has_headless: bool = Field(default=True, env='SBER_PARSER_POOL_HEADLESS')
    has_fast_load_strategy: bool = Field(default=True, env='SBER_PARSER_POOL_FASTLOAD')
    has_proxies: bool = Field(default=False, env='SBER_PARSER_POOL_HAS_PROXY')
    has_random_useragent: bool = Field(
        default=False, env='SBER_PARSER_POOL_RANDOM_USERAGENT'
    )
    has_experimental_options: bool = Field(
        default=False, env='SBER_PARSER_EXPERIMENTAL'
    )
