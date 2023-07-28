from pydantic import BaseModel, Field

from domain.goods import GoodsID, ProductEntity
from domain.entities import EncodedModel


class ProductIds(BaseModel):
    goods_ids: list[GoodsID] = Field(
        min_items=1, max_items=100, description='Goods ids for update db data'
    )


# Properties for manual creation from json data
class ProductManualUploadRequest(EncodedModel):
    data: list[ProductEntity] = Field(
        min_items=1,
        max_items=1000,
        description='Goods entities for manual update db data',
    )


class ProductManualUploadResponse(EncodedModel):
    data: ProductIds


# Properties for creation by scrapper
class ProductSeedRequest(BaseModel):
    data: ProductIds


class ProductSeedResponse(EncodedModel):
    data: list[ProductEntity]


class ProductsInfoResponse(EncodedModel):
    data: list[ProductEntity]


# Additional data
class ProductInfoCountResponse(BaseModel):
    count: int
