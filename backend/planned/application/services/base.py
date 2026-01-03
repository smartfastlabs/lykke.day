from planned.domain.entities import UserEntity


class BaseService:
    """Base class for all services.

    Provides a common base with user association for all service classes.
    Services should use UnitOfWork for transaction management rather than
    managing transactions directly.
    """

    user: UserEntity

    def __init__(self, user: UserEntity) -> None:
        """Initialize the service with a user.

        Args:
            user: The user associated with this service instance.
        """
        self.user = user
