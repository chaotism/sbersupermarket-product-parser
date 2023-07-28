"""
Providers base entities.
"""
import datetime
import itertools
import os
import time
import urllib.parse
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from functools import lru_cache
from decimal import Decimal
from hashlib import md5
from pathlib import Path
from typing import Optional, Generator
from urllib.parse import urlparse

from loguru import logger
from pydantic import HttpUrl, parse_obj_as
from pydantic import ValidationError
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from clients.parser import BaseParser, ParserPool, By
from common.errors import ProviderError
from common.utils import async_wrapper, retry_by_exception
from .entities import ProductEntity, ProductAttribute, ProductImage, ProductCategory
from .types import GoodsID, ProductName
from ..types import Provider


MAX_TRIES = 3


class ProductProvider(Provider):
    __metaclass__ = ABCMeta

    """
    ProductProvider interface class.
    """

    @abstractmethod
    async def get_product(
        self, goods_id: GoodsID, raw_data: Optional[bytes] = None
    ) -> ProductEntity:
        """
        Get product data entity by goods id.
        """


class SberMegaMarketProductProviderUrlSearch(ProductProvider):
    """
    ProductProvider interface class for sbermegamarket.
    """

    product_name_path: dict[By, str] = {
        By.CLASS_NAME: 'pdp-header__title',
    }
    product_description_path: dict[By, str] = {By.CLASS_NAME: 'product-description'}
    product_price_path: dict[By, str] = {By.CLASS_NAME: 'pdp-sales-block__price-final'}
    product_images_path: dict[By, str] = {
        By.CLASS_NAME: 'slide__image',
    }
    product_specs_names_path: dict[By, str] = {By.CLASS_NAME: 'pdp-specs__item-name'}
    product_specs_values_path: dict[By, str] = {By.CLASS_NAME: 'pdp-specs__item-value'}
    product_categories_path: dict[By, str] = {By.CLASS_NAME: 'breadcrumb-item'}

    def __init__(
        self, parser_pool: ParserPool, base_url: HttpUrl, debug: bool = False
    ) -> None:
        self.parser_pool = parser_pool
        self.base_url = base_url
        self.debug = debug

    async def get_product(
        self, goods_id: GoodsID, raw_data: Optional[bytes] = None
    ) -> ProductEntity:
        """
        Get product entity by goods id.
        """
        return await retry_by_exception(exceptions=ProviderError, max_tries=MAX_TRIES)(
            async_wrapper(self._get_product)
        )(goods_id, raw_data)

    def _get_product(
        self, goods_id: GoodsID, raw_data: Optional[bytes] = None
    ) -> ProductEntity:
        """
        Get product entity by goods id sync version.
        """
        if raw_data:
            return self._parse_raw_product_data(goods_id, raw_data)
        return self._pull_product_data(goods_id)

    @contextmanager
    def _get_parser(self) -> Generator[BaseParser, None, None]:
        try:
            parser = self.parser_pool.get()
            assert parser.client is not None
            yield parser
        finally:
            self.parser_pool.put(parser)

    @staticmethod
    def _save_data_to_file(data: bytes) -> Path:
        application_prefix = Path(os.getcwd()).name
        tmp_folder_path = Path('/tmp').joinpath(application_prefix)
        if not tmp_folder_path.exists():
            tmp_folder_path.mkdir(parents=True)

        for _ in range(MAX_TRIES):
            time_mark = int(datetime.datetime.utcnow().timestamp() * 1000 * 1000)
            file_pattern = f'{time_mark}.html'
            file_path = tmp_folder_path.joinpath(file_pattern)
            if file_path.exists():
                continue
            file_path.touch(exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(data)

            return file_path

        raise ProviderError(
            f'Cannot create temporary file for data {md5(data).hexdigest()}'
        )

    def _parse_raw_product_data(
        self, goods_id: GoodsID, raw_data: bytes
    ) -> ProductEntity:
        """
        Get product data entity from raw html data sync version
        """
        file_path = self._save_data_to_file(raw_data)
        with self._get_parser() as parser:
            parser.get_page(HttpUrl(file_path.as_uri()))
            logger.info(
                f'Start getting info for product with goods id: {goods_id} from raw data'
            )
            return self._get_current_product_entity(goods_id, parser)

    def _pull_product_data(self, goods_id: GoodsID) -> ProductEntity:
        """
        Get product entity by goods id sync version.
        """
        with self._get_parser() as parser:
            product_data_url = self._get_product_page(goods_id, parser)
            if parser.client.current_url != product_data_url:  # type: ignore[union-attr]
                parser.get_page(product_data_url)

            logger.info(f'Start getting info for product with goods id: {goods_id}')
            return self._get_current_product_entity(goods_id, parser)

    def _get_current_product_entity(
        self, goods_id: GoodsID, parser: BaseParser
    ) -> ProductEntity:
        """
        Get product entity by goods id sync version.
        """
        logger.info(
            f'Start getting info for product from uri: {parser.client.current_url}'  # type: ignore[union-attr]
        )

        # TODO: get goods_id from page instead kwarg
        name = self._get_product_name(parser)
        description = self._get_product_description(parser)
        price = self._get_product_price(parser)
        images = self._get_product_images(parser)
        specifications = self._get_product_specifications(parser)
        categories = self._get_product_categories(parser)

        product = self._make_product_entity(
            goods_id=goods_id,
            name=name,
            description=description,
            price=price,
            images=images,
            specifications=specifications,
            categories=categories,
        )
        if product.is_empty:
            raise ProviderError(f'Product data for goods id: {goods_id} is empty')
        return product

    @staticmethod
    def _make_product_entity(
        goods_id: GoodsID,
        name: ProductName,
        description: str,
        price: Decimal,
        images: list[ProductImage],
        specifications: list[ProductAttribute],
        categories: list[ProductCategory],
    ) -> ProductEntity:
        try:
            product = ProductEntity(
                goods_id=goods_id,
                name=name,
                description=description,
                price=price,
                images=images,
                attributes=specifications,
                categories=categories,
            )
        except ValidationError as err:
            logger.warning(
                f"""Get exception for ProductEntity {err}, with data: {
                        dict(
                            goods_id=goods_id,
                            name=name,
                            description=description,
                            price=price,
                            images=images,
                            specifications=specifications,
                            categories=categories
                        )
                    }
                """
            )
            raise ProviderError from err
        logger.debug(
            f'Got getting info for product with goods id {goods_id}: \n {product.json()}'
        )
        return product

    @staticmethod
    def _get_elements_data(
        path_dict: dict[By, str], parser: BaseParser
    ) -> list[WebElement]:
        for key, value in path_dict.items():
            if data := parser.get_elements(by=key, name=value):
                return data
        return []

    def _get_product_page(self, goods_id: GoodsID, parser: BaseParser) -> HttpUrl:
        """
        Get product page entity by goods id.
        """
        product_data_url = parse_obj_as(
            HttpUrl,
            urllib.parse.urljoin(str(self.base_url), f'catalog/?q={goods_id}'),
        )
        return product_data_url

    def _get_product_name(self, parser: BaseParser) -> ProductName:
        """
        Get product name.
        """
        if name_data := self._get_elements_data(self.product_name_path, parser):
            return ProductName(name_data[0].text)
        return ProductName('')

    def _get_product_description(self, parser: BaseParser) -> str:
        """
        Get product description.
        """
        if description_data := self._get_elements_data(
            self.product_description_path, parser
        ):
            return description_data[0].text
        return ''

    def _get_product_price(self, parser: BaseParser) -> Decimal:
        """
        Get product description.
        """
        if price_data := self._get_elements_data(self.product_price_path, parser):
            price = price_data[0].text.replace(' ', '').replace('₽', '')
            return Decimal(price) if price else Decimal('0')
        return Decimal('0')

    def _get_product_images(self, parser: BaseParser) -> list[ProductImage]:
        """
        Get product images.
        """
        if images_data := self._get_elements_data(self.product_images_path, parser):
            images = [
                ProductImage(name=img.get_property('alt'), url=img.get_property('src'))
                for img in images_data
                if img.get_property('src')
            ]
            return images
        return []

    def _get_product_specifications(self, parser: BaseParser) -> list[ProductAttribute]:
        """
        Get product metadata.
        """
        if not (
            specs_names := self._get_elements_data(
                self.product_specs_names_path, parser
            )
        ):
            return []
        if not (
            specs_values := self._get_elements_data(
                self.product_specs_values_path, parser
            )
        ):
            return []

        names = [key.text for key in specs_names]
        values = [key.text for key in specs_values]
        specs_data = [
            ProductAttribute(name=key, value=value)
            for key, value in itertools.zip_longest(names, values, fillvalue='')
            if key
        ]
        return specs_data

    def _get_product_categories(self, parser: BaseParser) -> list[ProductCategory]:
        """
        Get product metadata.
        """
        if categories_data := self._get_elements_data(
            self.product_categories_path, parser
        ):
            categories = [
                ProductCategory(name=category.text)
                for category in categories_data
                if category.text
            ]
            return categories[:-1]
        return []


class SberMegaMarketProductProvider(SberMegaMarketProductProviderUrlSearch):
    """
    ProductProvider interface class for sbermegamarket with patches for searching by search field.
    """

    search_data_field_path: dict[By, str] = {
        By.CLASS_NAME: 'search-field-input',
    }

    @staticmethod
    def _clear_search_data(search_field: WebElement):
        search_field.clear()
        if data := search_field.get_attribute('value'):
            search_field.send_keys(Keys.BACKSPACE * len(data))
        if max_length := search_field.get_attribute('maxlength'):
            search_field.send_keys(Keys.BACKSPACE * int(max_length))

    def _get_search_field(self, parser: BaseParser) -> WebElement:
        """
        Get base sbermegamarket page with search field.
        """
        for _ in range(MAX_TRIES):
            if search_field_data := self._get_elements_data(
                self.search_data_field_path, parser
            ):
                search_field_input = search_field_data[0]
                self._clear_search_data(search_field_input)
                return search_field_input
            parser.get_page(self.base_url)

        if self.debug:
            parser.get_screenshot()
        raise ProviderError('Cannot find search field')

    @lru_cache(maxsize=512)
    def _get_product_page(self, goods_id: GoodsID, parser: BaseParser) -> HttpUrl:
        """
        Get product page entity by goods id.
        """
        search_field_input = self._get_search_field(parser)
        search_field_input.send_keys(goods_id)
        search_field_input.send_keys(Keys.RETURN)
        search_field_input.submit()

        for _ in range(MAX_TRIES):
            if str(goods_id) in urlparse(parser.client.current_url).path:  # type: ignore[union-attr]
                product_data_url = parse_obj_as(
                    HttpUrl,
                    parser.client.current_url,  # type: ignore[union-attr]
                )
                return product_data_url
            time.sleep(1)

        if self.debug:
            parser.get_screenshot()
        raise ProviderError('Cannot change current url to product url')
