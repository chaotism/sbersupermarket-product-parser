from fastapi import APIRouter, Depends
from loguru import logger
from web.routers.deps import get_common_data

from .deps import get_db_info, get_system_info
from .schemas import AppStateResponseData, DbStateResponseData


router = APIRouter()


@router.get('/ping', response_model=str)
async def ping() -> str:
    return 'pong'


@router.get('/system-status', response_model=AppStateResponseData)
async def status(
    app_data=Depends(get_system_info),
    common_data=Depends(get_common_data),
) -> AppStateResponseData:
    logger.info('Application-status start')
    logger.debug(f'app attrs: {common_data}')
    app_info_data = await app_data.check()
    return app_info_data['application']


@router.get('/readiness-probe', response_model=DbStateResponseData)
async def readiness_prob(
    db_data=Depends(get_db_info),
) -> DbStateResponseData:  # TODO: add check logic
    logger.info('Health-status start')
    db_info = await db_data.check()
    return db_info


@router.get('/liveness-probe', response_model=DbStateResponseData)
async def liveness_prob(
    db_data=Depends(get_db_info),
) -> DbStateResponseData:  # TODO: add check logic
    logger.info('liveness_prob')
    db_info = await db_data.check()
    return db_info
