"""
Providers base entities.
"""
import itertools
import urllib.parse
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from typing import Optional, Generator

from loguru import logger
from pydantic import HttpUrl, parse_obj_as
from pydantic import ValidationError
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from clients.parser import BaseParser, ParserPool
from common.errors import ProviderError
from common.utils import async_wrapper, retry_by_exception
from .entities import ProductEntity
from .types import GoodsID, CategoryName, ProductName
from ..types import Provider


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


class SberSuperMarketProductProvider(ProductProvider):
    """
    ProductProvider interface class.
    """

    product_name_path: dict[By, str] = {
        By.CLASS_NAME: 'pdp-header__title',
        By.XPATH: '//header/h1',
    }
    product_description_path: dict[By, str] = {By.CLASS_NAME: 'product-description'}
    product_price_path: dict[By, str] = {By.CLASS_NAME: 'pdp-sales-block__price-final'}
    product_images_path: dict[By, str] = {
        By.CLASS_NAME: 'slide__image',
        By.XPATH: '//li[@class="pdp-reviews-gallery-preview__item"]/img[@class="lazy-img"]',
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
        return await retry_by_exception(exceptions=ProviderError, max_tries=3)(
            async_wrapper(self._get_product)
        )(goods_id)

    @contextmanager
    def _get_parser(self) -> Generator[BaseParser, None, None]:
        parser = self.parser_pool.get()
        yield parser
        self.parser_pool.put(parser)

    def _get_product(self, goods_id: GoodsID) -> ProductEntity:
        """
        Get product entity by goods id sync version.
        """
        with self._get_parser() as parser:
            self._get_product_page(goods_id, parser)
            # TODO: Sometimes drives go down - maybe better decision to use BeautifulSoup with self.parser.page_source
            logger.info(f'Start getting info for product with goods id: {goods_id}')
            name = self._get_product_name(parser)
            description = self._get_product_description(parser)
            price = self._get_product_price(parser)
            images = self._get_product_images(parser)
            specifications = self._get_product_specifications(parser)
            categories = self._get_product_categories(parser)

            return self._make_product_entity(
                goods_id=goods_id,
                name=name,
                description=description,
                price=price,
                images=images,
                specifications=specifications,
                categories=categories,
            )

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
        if product.is_empty:
            raise ProviderError(f'Product data for goods id: {goods_id} is empty')
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
