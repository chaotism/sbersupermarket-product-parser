from pydantic import BaseModel, Field

from domain.goods import GoodsID, ProductEntity
from domain.entities import EncodedModel


# Properties to receive on creation
class ProductIds(BaseModel):
    goods_ids: list[GoodsID] = Field(
        min_items=1, max_items=100, description='Goods ids for update db data'
    )


class ProductSeedRequest(BaseModel):
    data: ProductIds


class ProductInfoCountRequest(BaseModel):
    count: int


# Properties to receive on getting data
class ProductInfoRequest(BaseModel):
    goods_id: GoodsID


# Properties to return to client
class ProductInfoResponse(EncodedModel):
    data: list[ProductEntity]
