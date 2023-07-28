"""Config for DBS"""
from typing import Optional

from pydantic import BaseSettings, Field
from sqlalchemy.engine.url import URL


DEFAULT_STATEMENT_CACHE_SIZE = 100


class DbSettings(BaseSettings):
    dsn: Optional[URL] = Field(None, env='DB_DSN')

    driver: Optional[str] = Field('asyncpg', env='DB_DRIVER')
    host: Optional[str] = Field('127.0.0.1', env='POSTGRES_HOST')
    port: Optional[int] = Field(5432, env='POSTGRES_PORT')

    db_name: str = Field('srv_marketplaces', env='POSTGRES_DB')
    username: str = Field('srv_marketplaces', env='POSTGRES_USER')
    password: Optional[str] = Field('look_in_vault', env='POSTGRES_PASSWORD')

    has_pg_bouncer: Optional[bool] = Field(True, env='POSTGRES_BOUNCER')

    @classmethod
    def generate(cls):
        base_settings = cls()
        if base_settings.dsn is not None:
            return base_settings
        dsn = URL.create(
            drivername=base_settings.driver,
            host=base_settings.host,
            port=base_settings.port,
            database=base_settings.db_name,
            username=base_settings.username,
            password=base_settings.password,
            query={
                'statement_cache_size': str(0)
                if base_settings.has_pg_bouncer
                else str(DEFAULT_STATEMENT_CACHE_SIZE)
            },
        )
        return cls(dsn=dsn)
