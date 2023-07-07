from clients import parser_pool
from domain.goods import (
    GinoProductRepository,
    SberMegaMarketProductProvider,
    ProductInfoService,
)
from config import parser_config


async def get_product_parser_service() -> ProductInfoService:
    return ProductInfoService(
        product_repo=GinoProductRepository(),
        product_provider=SberMegaMarketProductProvider(
            parser_pool=parser_pool, base_url=parser_config.url
        ),
    )
