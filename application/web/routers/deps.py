from fastapi import Request
from starlette.requests import State


async def get_common_data(request: Request) -> State:
    return request.state
