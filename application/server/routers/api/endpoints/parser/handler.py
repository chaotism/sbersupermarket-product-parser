from fastapi import APIRouter, Depends, HTTPException

from common.utils import duration_measure, gather_tasks
from domain.goods import CategoryName, ProductID, ProductInfoService
from .deps import get_product_parser_service
from .schemas import ProductInfoResponse, ProductSeedRequest

router = APIRouter()


@router.post('/seed_data', response_model=ProductInfoResponse)
async def seed_product_info(
    *,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
    product_ids_data: ProductSeedRequest,
) -> ProductInfoResponse:
    """
    Update db data for product ids.
    """
    products_ids = product_ids_data.data.product_ids
    products_seed_tasks = [
        product_info_service.register_provider_product_info(products_id)
        for products_id in set(products_ids)
    ]
    results = await duration_measure(gather_tasks)(
        products_seed_tasks,
        timeout=30 * len(products_seed_tasks),
    )  # TODO: use fastapi.BackgroundTasks

    return ProductInfoResponse(data=results)


@router.get('/category/{category_name}', response_model=ProductInfoResponse)
async def get_product_category_info(
    category: CategoryName,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductInfoResponse:
    """
    Get a product info by product name.
    """
    product_info_entities = await product_info_service.find_category_products(
        category=category
    )
    if not product_info_entities:
        raise HTTPException(status_code=404, detail='Not found')
    return ProductInfoResponse(data=product_info_entities)


@router.get('/{product_id}', response_model=ProductInfoResponse)
async def get_product_info(
    product_id: ProductID,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductInfoResponse:
    """
    Get a product info by product name.
    """
    product_info_entity = await product_info_service.get_product_info(
        product_id=product_id
    )
    if not product_info_entity:
        raise HTTPException(status_code=404, detail='Not found')
    return ProductInfoResponse(data=[product_info_entity])
