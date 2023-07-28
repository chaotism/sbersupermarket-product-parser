from fastapi import APIRouter, Depends, HTTPException, UploadFile

from common.cache import async_cache
from common.utils import duration_measure, gather_tasks
from domain.goods import CategoryName, GoodsID, ProductInfoService
from .deps import get_product_parser_service
from .schemas import (
    ProductManualUploadRequest,
    ProductManualUploadResponse,
    ProductSeedRequest,
    ProductSeedResponse,
    ProductInfoCountResponse,
    ProductsInfoResponse,
)

router = APIRouter()

SEC = 1
MIN = 60 * SEC


@router.post('/manual_upload_products', response_model=ProductManualUploadResponse)
async def manual_upload_products(
    *,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
    goods_entities_data: ProductManualUploadRequest,
) -> ProductManualUploadResponse:
    """
    Saving json of goods data for manual updating info in db.
    """
    map_goods_id_to_goods_entities = {
        entity_data.goods_id: entity_data for entity_data in goods_entities_data.data
    }
    products_manual_upload_tasks = [
        product_info_service.manual_upload_product_info(product_entity)
        for product_entity in map_goods_id_to_goods_entities.values()
    ]
    results = await duration_measure(gather_tasks)(
        products_manual_upload_tasks,
        timeout=SEC * len(products_manual_upload_tasks),
    )

    return ProductManualUploadResponse(data={'goods_ids': results})


@router.post('/seed_data', response_model=ProductSeedResponse)
async def seed_product_info(
    *,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
    goods_ids_data: ProductSeedRequest,
) -> ProductsInfoResponse:
    """
    Update goods data for list of goods ids. Forcefully update records in db.
    """
    goods_ids = goods_ids_data.data.goods_ids
    products_seed_tasks = [
        product_info_service.register_provider_product_info(goods_id)
        for goods_id in set(goods_ids)
    ]
    results = await duration_measure(gather_tasks)(
        products_seed_tasks,
        timeout=MIN * len(products_seed_tasks),
    )

    return ProductsInfoResponse(data=results)


@router.get('/{goods_id}', response_model=ProductsInfoResponse)
async def get_product_info(
    goods_id: GoodsID,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductsInfoResponse:
    """
    Get a product info by product id.
    """
    product_info_entity = await product_info_service.find_product_info(
        goods_id=goods_id
    )
    if not product_info_entity:
        raise HTTPException(status_code=404, detail='Not found')
    return ProductsInfoResponse(data=[product_info_entity])


@router.post('/{goods_id}', response_model=ProductsInfoResponse)
async def manual_upload_product_info(
    goods_id: GoodsID,
    product_page_file: UploadFile,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductsInfoResponse:
    """
    Upload html data as a file for parsing product data and link data to goods id.
    """
    raw_data = await product_page_file.read()
    product_info_entity = await product_info_service.register_provider_product_info(
        goods_id=goods_id, raw_data=raw_data
    )
    if not product_info_entity:
        raise HTTPException(status_code=400, detail='Bad raw data found')
    return ProductsInfoResponse(data=[product_info_entity])


@router.get('/category/{category_name}', response_model=ProductsInfoResponse)
async def get_product_category_info(
    category_name: CategoryName,
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductsInfoResponse:
    """
    Get a product info by category name.
    """
    product_info_entities = await async_cache(
        product_info_service.search_category_products
    )(category=category_name)
    if not product_info_entities:
        raise HTTPException(status_code=404, detail='Not found')
    return ProductsInfoResponse(data=product_info_entities)


@router.get('/count', response_model=ProductInfoCountResponse)
async def get_product_info_count(
    product_info_service: ProductInfoService = Depends(get_product_parser_service),
) -> ProductInfoCountResponse:
    """
    Get a count of products in db.
    """
    product_info_count = await product_info_service.count()
    return ProductInfoCountResponse(count=product_info_count)
