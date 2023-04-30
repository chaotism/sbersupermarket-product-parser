from fastapi import APIRouter

from .app_state import db_state_router


health_router = APIRouter()
health_router.include_router(db_state_router, tags=['app state'])
