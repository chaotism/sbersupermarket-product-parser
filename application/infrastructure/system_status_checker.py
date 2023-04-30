from abc import ABCMeta, abstractmethod
from enum import IntEnum

from loguru import logger
from tortoise import connections

from domain.entities import EncodedModel


class HeartbeatStatus(IntEnum):
    corrected = 0
    warning = 50
    error = 100


class HeartbeatInformation(EncodedModel):
    name: str
    status: HeartbeatStatus


class AppState(EncodedModel):
    api_version: str
    debug: bool


class HeartbeatComponent:
    __metaclass__ = ABCMeta

    @abstractmethod
    async def check(self) -> HeartbeatInformation:
        raise NotImplementedError()


class TortoiseDatabaseHeartbeat(HeartbeatComponent):
    def __init__(self, name: str):
        self.name = name

    async def check(self) -> HeartbeatInformation:
        try:
            conn = connections.get('default')
            await conn.execute_query('SELECT 1')
            status = HeartbeatStatus.corrected
        except Exception as error:
            logger.exception(f'Problem with {self.name} database', exc_info=error)
            status = HeartbeatStatus.error
            raise

        return HeartbeatInformation(name=self.name, status=status)


class SystemInfo:
    def __init__(self, api_version: str, debug: bool):
        self.api_version = api_version
        self.debug = debug

    async def check(self) -> dict:
        system_status = {
            'application': AppState(
                api_version=self.api_version,
                debug=self.debug,
            )
        }
        return system_status
