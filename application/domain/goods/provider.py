"""
Providers base entities.
"""
import itertools
import time
import urllib.parse
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from typing import Optional, Generator

from loguru import logger
from pydantic import HttpUrl, parse_obj_as
from pydantic import ValidationError
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from clients.parser import BaseParser, ParserPool
from common.errors import ProviderError
from common.utils import async_wrapper, retry_by_exception
from .entities import ProductEntity
from .types import GoodsID, CategoryName, ProductName
from ..types import Provider


MAX_TRIES = 3


class ProductProvider(Provider):
    __metaclass__ = ABCMeta

    """
    ProductProvider interface class.
    """

    @abstractmethod
    async def get_product(self, goods_id: GoodsID) -> ProductEntity:
        """
        Get product data entity by goods id.
        """


class SberMegaMarketProductProviderUrlSearch(ProductProvider):
    """
    ProductProvider interface class. not-found
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

    def __init__(self, parser_pool: ParserPool, base_url: HttpUrl) -> None:
        self.parser_pool = parser_pool
        self.base_url = base_url

    async def get_product(self, goods_id: GoodsID) -> ProductEntity:
        """
        Get product entity by goods id.
        """
        return await retry_by_exception(exceptions=ProviderError, max_tries=MAX_TRIES)(
            async_wrapper(self._get_product)
        )(goods_id)

    @contextmanager
    def _get_parser(self) -> Generator[BaseParser, None, None]:
        try:
            parser = self.parser_pool.get()
            yield parser
        finally:
            self.parser_pool.put(parser)

    def _get_product(self, goods_id: GoodsID) -> ProductEntity:
        """
        Get product entity by goods id sync version.
        """
        with self._get_parser() as parser:
            self._get_product_page(goods_id, parser)
            logger.info(f'Start getting info for product with goods id: {goods_id}')

            # TODO: Sometimes drives go down - maybe better decision to use BeautifulSoup with self.parser.page_source
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
        name: Optional[ProductName],
        description: Optional[str],
        price: Optional[str],
        images: list[dict[str, str]],
        specifications: list[dict[str, str]],
        categories: list[dict[str, str]],
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

    def _get_product_page(self, goods_id: GoodsID, parser: BaseParser):
        """
        Get product page entity by goods id.
        """
        product_data_url = parse_obj_as(
            HttpUrl,
            urllib.parse.urljoin(str(self.base_url), f'catalog/?q={goods_id}'),
        )
        parser.get_page(urllib.parse.urljoin(self.base_url, product_data_url))
        return parser

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

    def _get_product_price(self, parser: BaseParser) -> str:
        """
        Get product description.
        """
        if price_data := self._get_elements_data(self.product_price_path, parser):
            price = price_data[0].text.replace(' ', '').replace('₽', '')
            return price if price else '0'
        return '0'

    def _get_product_images(self, parser: BaseParser) -> list[dict[str, str]]:
        """
        Get product images.
        """
        if images_data := self._get_elements_data(self.product_images_path, parser):
            images = [
                {'name': img.get_property('alt'), 'url': img.get_property('src')}
                for img in images_data
                if img.get_property('src')
            ]
            return images
        return []

    def _get_product_specifications(self, parser: BaseParser) -> list[dict[str, str]]:
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
            {'name': key, 'value': value}
            for key, value in itertools.zip_longest(names, values, fillvalue='')
            if key
        ]
        return specs_data

    def _get_product_categories(self, parser: BaseParser) -> list[dict[str, str]]:
        """
        Get product metadata.
        """
        if categories_data := self._get_elements_data(
            self.product_categories_path, parser
        ):
            categories = [
                {'name': CategoryName(category.text)}
                for category in categories_data
                if category.text
            ]
            return categories
        return []


class SberMegaMarketProductProvider(SberMegaMarketProductProviderUrlSearch):
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

        raise ProviderError('Cannot find search field')

    def _get_product_page(self, goods_id: GoodsID, parser: BaseParser):
        """
        Get product page entity by goods id.
        """

        search_field_input = self._get_search_field(parser)
        search_field_input.send_keys(goods_id)
        search_field_input.send_keys(Keys.RETURN)
        search_field_input.submit()

        for _ in range(MAX_TRIES):
            if str(goods_id) in parser.client.current_url:
                return parser
            time.sleep(1)
        raise ProviderError('Cannot change current url to product url')
