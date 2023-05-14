"""
Base names for root errors in application.
"""


class ApplicationError(Exception):
    """
    Base application exception.
    """

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(self.default_message)


class ClientError(ApplicationError):
    """
    Base client logic exception.
    """

    default_message = 'Client error'


class DatabaseError(ApplicationError):
    """
    Base database logic exception.
    """

    default_message = 'Database error'


class EntityError(ApplicationError):
    """
    Base entity validation exception.
    """

    default_message = 'Entity error'


class ProviderError(ApplicationError):
    """
    Base provider logic exception.
    """

    default_message = 'ProductProvider error'


class RepositoryError(ApplicationError):
    """
    Base repository logic exception.
    """

    default_message = 'Repository error'


class ServiceError(ApplicationError):
    """
    Base service logic exception.
    """

    default_message = 'Service error'


class NotFoundError(ApplicationError):
    """
    Not found object wrapper.
    """

    default_message = 'Cannot found object'
