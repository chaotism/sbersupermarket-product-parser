from config import application_config, db_config, openapi_config
from infrastructure import TortoiseDatabaseHeartbeat, SystemInfo


async def get_system_info() -> SystemInfo:
    return SystemInfo(
        api_version=openapi_config.version,
        debug=application_config.is_debug,
    )


async def get_db_info() -> TortoiseDatabaseHeartbeat:
    return TortoiseDatabaseHeartbeat(
        name=f'Heart-Beat: {db_config.driver}-{db_config.db_name}',
    )
