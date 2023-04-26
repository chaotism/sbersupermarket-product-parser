from pydantic import BaseModel, Field

from domain.goods import ProductID, ProductEntity
from domain.entities import EncodedModel


# Properties to receive on creation
class ProductIds(BaseModel):
    product_ids: list[ProductID] = Field(
        min_items=1, max_items=100, description='Product ids for update db data'
    )


class ProductSeedRequest(BaseModel):
    data: ProductIds


# Properties to receive on getting data
class ProductInfoRequest(BaseModel):
    product_id: ProductID


# Properties to return to client
class ProductInfoResponse(EncodedModel):
    data: list[ProductEntity]
