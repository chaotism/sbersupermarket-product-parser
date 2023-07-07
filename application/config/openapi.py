"""config for OpenAPI-schema"""
from pydantic import AnyHttpUrl, BaseSettings, Field

DEFAULT_API_NAME = 'Internal parsing service'
DEFAULT_API_VERSION = '0.0.1'
DEFAULT_API_DESCRIPTION = 'API for humans'
DEFAULT_SERVER_NAME = 'http://sbermegamarket-parser.edu'


class OpenAPISettings(BaseSettings):
    """Base openapi settings"""

    name: str = Field(default=DEFAULT_API_NAME, env='OPENAPI_NAME')
    version: str = Field(default=DEFAULT_API_VERSION, env='OPENAPI_VERSION')
    description: str = Field(default=DEFAULT_API_DESCRIPTION, env='OPENAPI_DESCRIPTION')
    server_name: AnyHttpUrl = Field(
        default=DEFAULT_SERVER_NAME, env='OPENAPI_SERVERNAME'
    )
