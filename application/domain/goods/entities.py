from decimal import Decimal

from pydantic import HttpUrl, Field

from .types import GoodsID, ProductName
from ..entities import Entity, EncodedModel


class ProductAttribute(EncodedModel):
    name: str = Field(max_length=256)
    value: str = Field(max_length=1024)


class ProductCategory(EncodedModel):
    name: ProductName


class ProductImage(EncodedModel):
    name: str = Field(max_length=256)
    url: HttpUrl


class ProductEntity(Entity):
    goods_id: GoodsID = Field(description='Штрихкод')
    name: ProductName
    price: Decimal

    categories: list[ProductCategory]
    images: list[ProductImage]
    attributes: list[ProductAttribute]

    @property
    def is_empty(self) -> bool:
        if not any(
            [self.name, self.price, self.categories, self.images, self.attributes]
        ):
            return True
        return False
