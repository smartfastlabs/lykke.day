from uuid import UUID

from passlib.context import CryptContext

from planned.application.repositories import UserRepositoryProtocol
from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.utils.strings import normalize_email, normalize_phone_number

from .base import BaseService

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


class AuthService(BaseService):
    """AuthService for user management. NOT user-scoped."""

    def __init__(self, user_repo: UserRepositoryProtocol) -> None:
        """Initialize AuthService with UserRepository."""
        self.user_repo = user_repo

    @classmethod
    def new(cls, user_repo: UserRepositoryProtocol) -> "AuthService":
        """Create a new instance of AuthService."""
        return cls(user_repo=user_repo)

    async def create_user(
        self,
        email: str,
        password: str,
        phone_number: str | None = None,
    ) -> User:
        """Create a new user with hashed password.

        Args:
            email: User's email address (must be unique)
            password: Plain text password to hash
            phone_number: Optional phone number

        Returns:
            Created User entity

        Raises:
            BadRequestError: If email already exists
        """
        # Normalize email and phone number
        normalized_email = normalize_email(email)
        normalized_phone = (
            normalize_phone_number(phone_number)
            if phone_number and phone_number.strip()
            else None
        )

        # Check if user with this email already exists
        existing_user = await self.user_repo.get_by_email(normalized_email)
        if existing_user is not None:
            raise exceptions.BadRequestError(
                f"User with email {normalized_email} already exists"
            )

        # Hash password
        password_hash = pwd_context.hash(password)

        # Create user with default settings
        user = User(
            email=normalized_email,
            phone_number=normalized_phone,
            password_hash=password_hash,
            settings=UserSetting(),  # Default settings
        )

        # Save to database
        return await self.user_repo.put(user)

    async def get_user(self, user_uuid: UUID) -> User:
        """Get user by UUID.

        Args:
            user_uuid: User's UUID

        Returns:
            User entity

        Raises:
            NotFoundError: If user doesn't exist
        """
        return await self.user_repo.get(user_uuid)

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password.

        Args:
            email: User's email address
            password: Plain text password to verify

        Returns:
            User entity if authentication succeeds, None otherwise
        """
        # Normalize email for lookup
        normalized_email = normalize_email(email)
        user = await self.user_repo.get_by_email(normalized_email)
        if user is None:
            return None

        if pwd_context.verify(password, user.password_hash):
            return user

        return None

    async def set_password(self, user: User, new_password: str) -> None:
        """Update user's password.

        Args:
            user: User entity to update
            new_password: New plain text password to hash and set
        """
        user.password_hash = pwd_context.hash(new_password)
        await self.user_repo.put(user)
