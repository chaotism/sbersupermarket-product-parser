"""Config for sentry"""
from pydantic import BaseSettings, Field


class SentrySettings(BaseSettings):
    """Base sentry settings"""

    dsn: str = Field('', env='SENTRY_DSN')
