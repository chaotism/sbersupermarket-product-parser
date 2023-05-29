from fastapi import APIRouter, Depends, HTTPException

from common.utils import duration_measure, gather_tasks
from domain.goods import CategoryName, GoodsID, ProductInfoService
from .deps import get_product_parser_service
from .schemas import ProductSeedRequest, ProductInfoCountRequest, ProductInfoResponse

router = APIRouter()


@router.post('/seed_data', response_model=ProductInfoResponse)
async def seed_product_info(
    *,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
    goods_ids_data: ProductSeedRequest,
) -> ProductInfoResponse:
    """
    Update db data for goods ids.
    """
    goods_ids = goods_ids_data.data.goods_ids
    products_seed_tasks = [
        product_info_service.register_provider_product_info(goods_id)
        for goods_id in set(goods_ids)
    ]
    results = await duration_measure(gather_tasks)(
        products_seed_tasks,
        timeout=60 * len(products_seed_tasks),
    )  # TODO: use fastapi.BackgroundTasks

    return ProductInfoResponse(data=results)


@router.get('/count', response_model=ProductInfoCountRequest)
async def get_product_info_count(
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductInfoCountRequest:
    """
    Get a count of product info.
    """
    product_info_count = await product_info_service.count()
    return ProductInfoCountRequest(count=product_info_count)


@router.get('/category/{category_name}', response_model=ProductInfoResponse)
async def get_product_category_info(
    category_name: CategoryName,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductInfoResponse:
    """
    Get a product info by product name.
    """
    product_info_entities = await product_info_service.search_category_products(
        category=category_name
    )
    if not product_info_entities:
        raise HTTPException(status_code=404, detail='Not found')
    return ProductInfoResponse(data=product_info_entities)


@router.get('/{goods_id}', response_model=ProductInfoResponse)
async def get_product_info(
    goods_id: GoodsID,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductInfoResponse:
    """
    Get a product info by product name.
    """
    product_info_entity = await product_info_service.find_product_info(
        goods_id=goods_id
    )
    if not product_info_entity:
        raise HTTPException(status_code=404, detail='Not found')
    return ProductInfoResponse(data=[product_info_entity])
