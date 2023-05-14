"""Config for DBS"""
from typing import Optional

from pydantic import BaseSettings, Field
from sqlalchemy.engine.url import URL


class DbSettings(BaseSettings):
    dsn: Optional[URL] = Field(None, env='DB_DSN')

    driver: Optional[str] = Field('asyncpg', env='DB_DRIVER')
    host: Optional[str] = Field('127.0.0.1', env='DB_HOST')
    port: Optional[int] = Field(5432, env='DB_PORT')

    db_name: str = Field(None, env='DB_DATABASE')
    username: str = Field(None, env='DB_USER')
    password: Optional[str] = Field(None, env='DB_PASSWORD')

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
        )
        return cls(dsn=dsn)
