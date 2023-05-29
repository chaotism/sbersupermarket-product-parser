from fastapi import APIRouter, Depends
from web.core.auths import verify_auth_token

from .api.endpoints import api_router
from .health.endpoints import health_router

base_router = APIRouter()

base_router.include_router(
    api_router,
    prefix='/api',
    dependencies=[
        Depends(verify_auth_token),
    ],
)
base_router.include_router(
    health_router,
    prefix='/health',
)
