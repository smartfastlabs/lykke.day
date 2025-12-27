from . import auth
from .auth import AuthMiddleware

# Create a namespace for backward compatibility
class _MiddlewaresNamespace:
    AuthMiddleware = AuthMiddleware
    auth = auth


middlewares = _MiddlewaresNamespace()

__all__ = ["AuthMiddleware", "middlewares", "auth"]
