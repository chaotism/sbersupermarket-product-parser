"""API Middlewares"""
import time

from fastapi import Request
from loguru import logger


async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers['X-Process-Time'] = str(process_time)
    return response


async def request_logging_middleware(request: Request, call_next):
    logger.info(f'request: {request.method} {request.url.path}')
    response = await call_next(request)
    logger.info(f'response {request.method} {request.url.path} {response.status_code}')
    return response


async def logging_access_token(request: Request, call_next):
    method = request.method
    receive = request.receive
    access_token = request.headers.get('Auth-Token', '')
    remote_ip = request.headers.get('X-Real-IP', '')
    logger.info(
        '{} to {} for IP {} with token {}'.format(
            method, receive, remote_ip, access_token
        )
    )
    response = await call_next(request)
    return response
