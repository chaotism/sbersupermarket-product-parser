from typing import Optional

from loguru import logger

from common.errors import ServiceError, ProviderError, NotFoundError
from common.utils import duration_measure
from .entities import ProductEntity
from .provider import ProductProvider
from .repositories import ProductRepository
from .types import GoodsID, CategoryName
from ..types import Service


class ProductInfoService(Service):
    def __init__(
        self, product_repo: ProductRepository, product_provider: ProductProvider
    ) -> None:
        self.product_repo = product_repo
        self.product_provider = product_provider

    async def register_provider_product_info(self, goods_id: GoodsID) -> ProductEntity:
        try:
            product_data = await self.product_provider.get_product(goods_id)
        except ProviderError as err:
            logger.warning(f'Get provider error {err} for goods_id {goods_id} ')
            raise NotFoundError(f'Cannot find information for goods_id: {goods_id}')
        return await self._update_product(goods_id, product_data)

    @duration_measure
    async def find_product_info(self, goods_id: GoodsID) -> Optional[ProductEntity]:
        if product := await self._get_product(goods_id):
            return product
        try:
            return await self.register_provider_product_info(goods_id)
        except NotFoundError as err:
            logger.warning(str(err))
            return None
        except Exception as err:
            logger.exception('Get unknown exception')
            raise ServiceError from err

    async def search_category_products(
        self, category: CategoryName
    ) -> list[ProductEntity]:
        products = await self.product_repo.select_by_category(category)
        if not products:
            return []
        return products

    async def _get_product(self, goods_id: GoodsID) -> Optional[ProductEntity]:
        products = await self.product_repo.find_by_goods_id(goods_id)
        return products

    async def _update_product(
        self,
        goods_id: GoodsID,
        product_data: ProductEntity,
    ) -> ProductEntity:
        async with self.product_repo.atomic():
            if exist_product_data := await self._get_product(goods_id):
                exist_product_data.update(product_data)
                await self.product_repo.update(exist_product_data)
                logger.debug(
                    f'Successfully update {exist_product_data} with key {exist_product_data.get_id()}'
                )
                return await self.product_repo.get_by_id(exist_product_data.get_id())

            instance_id = await self.product_repo.insert(product_data)
            saved_product_data = await self.product_repo.get_by_id(instance_id)
            logger.debug(f'Create {saved_product_data} with key {instance_id}')
            return await self.product_repo.get_by_id(instance_id)

    async def _remove_product(
        self, goods_id: GoodsID
    ):  # TODO: add logic for using this method
        products = await self._get_product(goods_id)
        if not products:
            raise NotFoundError(
                f'Cannot find product for deleting with goods_id {goods_id}'
            )
        await self.product_repo.delete(products)

    async def _have_products(self) -> bool:  # TODO: add logic for using this method
        return await self.product_repo.get_count() > 0
