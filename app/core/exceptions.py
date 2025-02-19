class ServiceError(Exception):
    """Base class for exceptions in this module."""


class ChatError(ServiceError):
    """Raised when there is an error in chatbot service."""


class FAQError(ServiceError):
    """Raised when there is an error in FAQ service."""
