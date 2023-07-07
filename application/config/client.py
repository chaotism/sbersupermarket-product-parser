"""Config for external clients"""
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field, HttpUrl

SBER_DEFAULT_URL = 'https://sbermegamarket.ru'
DEFAULT_POOL_SIZE = 1


class ParserSettings:
    """Base parse settings"""

    url: HttpUrl
    pool_size: int
    chrome_version: Optional[int] = None
    chrome_data_dir: Optional[Path] = None
    has_headless: bool = True
    has_fast_load_strategy: bool = True
    has_proxies: bool = True
    has_random_useragent: bool = True
    has_experimental_options: bool = False
    log_folder: str


class SberMegaMarketParserSettings(BaseSettings):
    """Sbermegamarket parser env values"""

    url: HttpUrl = Field(default=SBER_DEFAULT_URL, env='SBER_MEGAMARKET_URI')
    pool_size: int = Field(default=DEFAULT_POOL_SIZE, env='SBER_PARSER_POOL_SIZE')
    chrome_version: Optional[int] = Field(
        default=None, env='SBER_PARSER_CHROME_VERSION'
    )
    chrome_data_dir: Optional[Path] = Field(
        default=None, env='SBER_PARSER_CHROME_USER_DIR'
    )
    has_headless: bool = Field(default=True, env='SBER_PARSER_POOL_HEADLESS')
    has_fast_load_strategy: bool = Field(default=True, env='SBER_PARSER_POOL_FASTLOAD')
    has_proxies: bool = Field(default=False, env='SBER_PARSER_POOL_HAS_PROXY')
    has_random_useragent: bool = Field(
        default=False, env='SBER_PARSER_POOL_RANDOM_USERAGENT'
    )
    has_experimental_options: bool = Field(
        default=False, env='SBER_PARSER_EXPERIMENTAL'
    )
    log_folder: str = Field(default='var/log', env='SBER_PARSER_LOG_FOLDER')
