from fastapi import APIRouter

from .parser import product_parser_router

api_router = APIRouter(prefix='/v1')


api_router.include_router(
    product_parser_router,
    prefix='/product_info',
    tags=['product_info'],
)
