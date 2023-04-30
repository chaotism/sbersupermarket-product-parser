"""Config of application"""
from .application import ApplicationSettings
from .auth import AuthSettings
from .client import SberSuperMarketParserSettings
from .db import DbSettings
from .openapi import OpenAPISettings
from .sentry import SentrySettings


application_config = ApplicationSettings()
auth_config = AuthSettings.generate()
db_config = DbSettings.generate()
openapi_config = OpenAPISettings()
sentry_config = SentrySettings()
parser_config = SberSuperMarketParserSettings()
