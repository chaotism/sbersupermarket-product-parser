from copy import deepcopy
from typing import Optional

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from config import db_config


DEFAULT_TORTOISE_ORM_CONFIG = {
    'connections': {'default': str(db_config.dsn)},
    'apps': {
        'models': {
            'models': ['storages.databases.models', 'aerich.models'],
            'default_connection': 'default',
        },
    },
    'use_tz': True,
    'timezone': 'UTC',
}


def init_db(app: FastAPI, dsn: Optional[str] = None):
    config: dict[str, dict] = deepcopy(DEFAULT_TORTOISE_ORM_CONFIG)
    if dsn:
        config['connections']['default'] = dsn

    register_tortoise(
        app,
        config=DEFAULT_TORTOISE_ORM_CONFIG,
        generate_schemas=True,
        add_exception_handlers=False,
    )
