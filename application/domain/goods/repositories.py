from abc import ABCMeta, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional

from loguru import logger
from tortoise import transactions

from common.errors import RepositoryError, NotFoundError
from storages.databases import (
    ProductModel,
    ProductAttributeModel,
    CategoryModel,
    ProductImageModel,
)
from .entities import ProductEntity
from .types import GoodsID, CategoryName
from ..types import Repository, IntId


class ProductRepository(Repository):
    __metaclass__ = ABCMeta

    """
    Repository interface class.
    """

    @abstractmethod
    async def get_count(self) -> int:
        pass

    @abstractmethod
    async def get_by_id(self, instance_id: IntId) -> ProductEntity:
        pass

    @abstractmethod
    async def find_by_goods_id(self, goods_id: GoodsID) -> Optional[ProductEntity]:
        pass

    @abstractmethod
    async def select_by_category(self, category: CategoryName) -> List[ProductEntity]:
        pass

    @abstractmethod
    async def insert(self, instance: ProductEntity) -> IntId:
        pass

    @abstractmethod
    async def update(self, instance: ProductEntity) -> None:
        pass

    @abstractmethod
    async def delete(self, instance: ProductEntity) -> None:
        pass

    @abstractmethod
    @asynccontextmanager
    async def atomic(self):
        pass


class GinoProductRepository(ProductRepository):
    model = ProductModel
    attribute_model = ProductAttributeModel
    category_model = CategoryModel
    image_model = ProductImageModel

    async def get_count(self) -> int:
        return await ProductModel.all().count()

    async def get_by_id(self, instance_id: IntId) -> ProductEntity:
        product = await (
            self.model.get_or_none(id=instance_id).prefetch_related(
                'attributes', 'categories', 'images'
            )
        )
        if product is None:
            raise RepositoryError(
                f'Cannot find object in collection {self.model.Meta.table} by id {instance_id}'
            )
        logger.debug(f'Get product instance: {product} for instance id: {instance_id}')
        return ProductEntity(**self._map_product_instance_to_dict(product))

    async def find_by_goods_id(self, goods_id: GoodsID) -> Optional[ProductEntity]:
        product = await (
            self.model.get_or_none(goods_id=goods_id).prefetch_related(
                'attributes', 'categories', 'images'
            )
        )
        logger.debug(f'Find product instance: {product} for goods_id: {goods_id}')
        if not product:
            return None
        return ProductEntity(**self._map_product_instance_to_dict(product))

    async def select_by_category(
        self, category: CategoryName, offset=0, limit=100000
    ) -> List[ProductEntity]:
        products = await (
            self.model.filter(categories__name=category)
            .offset(offset)
            .limit(limit)
            .prefetch_related('attributes', 'categories', 'images')
            .all()
        )
        logger.info(f'Select products instances: {products} for category: {category}')
        products_data = [
            ProductEntity(**self._map_product_instance_to_dict(product))
            for product in products
        ]
        return products_data

    async def insert(self, entity: ProductEntity) -> IntId:
        logger.debug(f'Try to save db data for  {entity}')
        async with self.atomic():
            product = await self.model.create(
                goods_id=entity.goods_id, name=entity.name, price=entity.price
            )
            entity.set_id(IntId(product.id))
            instance_id = entity.get_id()
            await self._update_or_create_attributes(product, entity=entity)
            await self._update_or_create_categories(product, entity=entity)
            await self._update_or_create_images(product, entity=entity)
            logger.debug(
                f'Successfully create product instance: {product} for entity {entity}'
            )
            return instance_id

    async def update(self, entity: ProductEntity):
        logger.debug(f'Try to update db data for  {entity}')
        async with self.atomic():
            instance_id = entity.get_id()
            product = await self.model.get_or_none(id=instance_id)
            if not product:
                raise NotFoundError(f'Cannot find model record for id {instance_id}')
            await product.update_from_dict(
                data={
                    'name': entity.name,
                    'price': entity.price,
                }
            ).save()

            await self._update_or_create_attributes(product, entity=entity)
            await self._update_or_create_categories(product, entity=entity)
            await self._update_or_create_images(product, entity=entity)
            logger.debug(
                f'Successfully update product instance: {product} for entity {entity}'
            )

    async def delete(self, entity: ProductEntity):
        instance_id = entity.get_id()
        async with self.atomic():
            product = await self.model.get_or_none(id=instance_id)
            if not product:
                raise NotFoundError(f'Cannot product instance for id {instance_id}')
            await product.delete()
            logger.debug(f'Delete product instance: {product} for id {instance_id}')

    @asynccontextmanager
    async def atomic(self):
        transaction_ctx = transactions.in_transaction()
        async with transaction_ctx:
            yield

    async def _update_or_create_attributes(  # TODO: add deleting attributes that absent in entity
        self, product_instance: ProductModel, entity: ProductEntity
    ):
        logger.debug(f'Try to update instance attributes for {entity}')
        attributes_for_insert: List[ProductAttributeModel] = [
            self.attribute_model(
                product_id=product_instance.id,
                name=attribute.name,
                value=attribute.value,
            )
            for attribute in entity.attributes
        ]
        attribute_instances: List[
            ProductAttributeModel
        ] = await self.attribute_model.bulk_create(  # type: ignore[assignment]
            attributes_for_insert,
            ignore_conflicts=True,
        )
        logger.debug(
            f'Successfully updated {len(attribute_instances)} instance attributes for {entity}'
        )

    async def _update_or_create_categories(  # TODO: add deleting categories that absent in entity
        self, product_instance: ProductModel, entity: ProductEntity
    ):
        logger.debug(f'Try to update instance attributes for {entity}')
        categories_for_insert: List[CategoryModel] = []
        for category in entity.categories:
            raw_instance = self.category_model(
                name=category.name,
            )
            if categories_for_insert:
                raw_instance.parent_category = categories_for_insert[-1]
            categories_for_insert.append(raw_instance)

        category_instances: List[CategoryModel] = await self.category_model.bulk_create(  # type: ignore[assignment]
            categories_for_insert,
            update_fields=['parent_category_id'],
            on_conflict=['name'],
        )
        stored_category_instances: List[CategoryModel] = await (
            self.category_model.filter(
                name__in=[
                    category_instance.name for category_instance in category_instances
                ]
            ).all()
        )
        for index, category_instance in enumerate(stored_category_instances):
            if index > 0:
                category_instance.parent_category = category_instances[index - 1]
                await category_instance.save()
            await category_instance.products.add(product_instance)

        logger.debug(
            f'Successfully updated {len(stored_category_instances)} instance categories for {entity}'
        )
        return category_instances

    async def _update_or_create_images(
        self, product_instance: ProductModel, entity: ProductEntity
    ):
        logger.debug(f'Try to update instance attributes for {entity}')
        images_for_insert: List[ProductImageModel] = [
            self.image_model(
                product_id=product_instance.id,
                name=image.name,
                url=image.url,
            )
            for image in entity.images
        ]
        image_instances: List[ProductImageModel] = await self.image_model.bulk_create(  # type: ignore[assignment]
            images_for_insert,
            ignore_conflicts=True,
        )
        logger.debug(
            f'Successfully updated {len(image_instances)} instance images for {entity}'
        )
        return image_instances

    @staticmethod
    def _map_product_instance_to_dict(
        instance: ProductModel,
    ) -> dict:
        return dict(
            id=instance.id,
            goods_id=instance.goods_id,
            name=instance.name,
            price=instance.price,
            categories=[{'name': category.name} for category in instance.categories],
            attributes=[
                {'name': attribute.name, 'value': attribute.value}
                for attribute in instance.attributes
            ],
            images=[
                {'name': image.name, 'url': image.url} for image in instance.images
            ],
        )
