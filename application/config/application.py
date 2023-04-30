"""Config for app"""
from pydantic import BaseSettings, Field


class ApplicationSettings(BaseSettings):
    """Base application settings"""

    is_debug: bool = Field(True, env='API_DEBUG')

    host: str = Field('0.0.0.0', env='API_HOST')
    port: int = Field(8000, env='API_PORT')
