"""
Here you should do all needed actions. Standart configuration of docker container
will run your application with this file.
"""
import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware


from clients import parser_pool
from common.errors import EntityError, ProviderError, RepositoryError, ServiceError
from common.utils import async_wrapper
from config import (
    application_config,
    db_config,
    parser_config,
    openapi_config,
    sentry_config,
)
from storages.databases import init_db
from web.core.exception_handlers import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTPException,
    http_422_error_handler,
    http_error_handler,
    entity_error_handler,
    provider_error_handler,
    repository_error_handler,
    service_error_handler,
)
from web.core.loggings import setup_logging
from web.core.middlewares import (
    add_process_time_header,
    logging_access_token,
    request_logging_middleware,
)
from web.routers import base_router as routers


setup_logging(debug=application_config.is_debug)
logger.info('Starting application initialization...')


@logger.catch(reraise=True)
def init_app():
    fastapi_app = FastAPI(
        title=openapi_config.name,
        version=openapi_config.version,
        description=openapi_config.description,
        debug=application_config.is_debug,
    )
    init_db(fastapi_app, dsn=str(db_config.dsn))
    fastapi_app.add_exception_handler(HTTPException, http_error_handler)
    fastapi_app.add_exception_handler(
        HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler
    )
    fastapi_app.add_exception_handler(EntityError, entity_error_handler)
    fastapi_app.add_exception_handler(ProviderError, provider_error_handler)
    fastapi_app.add_exception_handler(RepositoryError, repository_error_handler)
    fastapi_app.add_exception_handler(ServiceError, service_error_handler)

    fastapi_app.middleware('http')(  # for func middlewares
        logging_access_token
    )  # didn't work like decorator if func not main module
    fastapi_app.middleware('http')(  # for func middlewares
        add_process_time_header
    )  # didn't work like decorator if func not main module
    fastapi_app.middleware('http')(  # for func middlewares
        request_logging_middleware
    )  # didn't work like decorator if func not main module
    if sentry_config.dsn:
        sentry_sdk.init(dsn=sentry_config.dsn)
        fastapi_app.add_middleware(SentryAsgiMiddleware)

    fastapi_app.include_router(routers)
    logger.success('Successfully initialized!')
    return fastapi_app


app = init_app()


@app.on_event('startup')
async def startup():
    """
    Startups scripts
    """
    await async_wrapper(parser_pool.init)(parser_config)


@app.on_event('shutdown')
async def shutdown():
    """
    Shutdown scripts
    """
    await async_wrapper(parser_pool.close)()


@app.get('/')
async def redirect_to_docs():
    return RedirectResponse('/docs')
