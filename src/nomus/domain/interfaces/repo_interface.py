from abc import ABC, abstractmethod
from typing import Any


class IUserRepository(ABC):
    """
    Abstract base class for user repository operations.
    Defines the contract that any user data storage system must implement.
    
    This interface follows the Dependency Inversion Principle from SOLID:
    - High-level modules (Application layer) depend on this abstraction
    - Low-level modules (Infrastructure layer) implement this abstraction
    """

    @abstractmethod
    async def save_or_update_user(self, telegram_id: int, data: dict[str, Any]) -> None:
        """
        Creates a new user or updates existing user data.

        Args:
            telegram_id: Unique Telegram user identifier
            data: Dictionary containing user data (phone_number, language_code, etc.)
        """

    @abstractmethod
    async def get_user_by_phone(self, phone: str) -> dict[str, Any] | None:
        """
        Finds a user by their phone number.

        Args:
            phone: Phone number in any format

        Returns:
            User data dictionary if found, None otherwise

        Note:
            This operation may be less efficient than get_user_by_telegram_id
            as it requires scanning through all users.
        """

    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Finds a user by their Telegram ID (primary key).

        Args:
            telegram_id: Unique Telegram user identifier

        Returns:
            User data dictionary if found, None otherwise
        """

    @abstractmethod
    async def get_user_language(self, telegram_id: int) -> str | None:
        """
        Gets the language code for a specific user.

        Args:
            telegram_id: Unique Telegram user identifier

        Returns:
            Language code (e.g., 'uz', 'ru', 'en') if user exists, None otherwise

        Raises:
            ValueError: If language_code exists but is invalid
        """

    @abstractmethod
    async def update_user_language(self, telegram_id: int, language_code: str) -> bool:
        """
        Updates the language for a user.

        Args:
            telegram_id: Unique Telegram user identifier
            language_code: New language code

        Returns:
            True if update was successful
        """

    @abstractmethod
    async def delete_user(self, telegram_id: int) -> bool:
        """
        Deletes a user from the repository.

        Args:
            telegram_id: Unique Telegram user identifier

        Returns:
            True if user was deleted, False if user was not found
        """


class IOrderRepository(ABC):
    """
    Abstract base class for order repository operations.
    Defines the contract that any order data storage system must implement.
    """

    @abstractmethod
    async def save_or_update_order(self, order_id: str, data: dict[str, Any]) -> None:
        """
        Creates a new order or updates an existing order.

        Args:
            order_id: Unique order identifier
            data: Dictionary containing order data (user_id, tariff, amount, status, etc.)
        """

    @abstractmethod
    async def get_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        """
        Retrieves an order by its ID.

        Args:
            order_id: Unique order identifier

        Returns:
            Order data dictionary if found, None otherwise
        """

    @abstractmethod
    async def get_order_status(self, order_id: str) -> str | None:
        """
        Gets the status of a specific order.

        Args:
            order_id: Unique order identifier

        Returns:
            Order status (e.g., 'pending', 'processing', 'completed') if found, None otherwise
        """

    @abstractmethod
    async def get_orders_by_user(self, telegram_id: int) -> list[dict[str, Any]]:
        """
        Retrieves all orders for a specific user.

        Args:
            telegram_id: Unique Telegram user identifier

        Returns:
            List of order dictionaries. Empty list if no orders found.
        """

    @abstractmethod
    async def update_order_status(self, order_id: str, status: str) -> None:
        """
        Updates the status of an order.

        Args:
            order_id: Unique order identifier
            status: New status value (e.g., 'processing', 'completed', 'cancelled')

        Raises:
            KeyError: If order with given ID does not exist
        """

class ICommittable(ABC):
    """
    Abstract base class for committing accumulated data.
    Defines the contract for sending buffered data to a remote storage.
    """

    @abstractmethod
    async def commit(self) -> None:
        """
        Commits accumulated changes to the underlying storage.
        """

class IStorageRepository(IUserRepository, IOrderRepository, ABC):
    """
    Combined storage repository interface.

    Aggregates both user and order repository operations into a single
    storage abstraction. Implementations must provide both user and order
    management capabilities.

    This interface is used by ServiceFactory to ensure consistent
    storage implementations across different environments (memory, PostgreSQL, etc.).
    """

    async def flush(self) -> None:
        """
        Flushes any pending changes to the underlying storage.

        For implementations that buffer changes (like RemoteStorage), this method
        synchronizes all pending data with the remote storage.
        For direct storage implementations (like MemoryStorage, PostgreSQL), this is a no-op.

        This method should be called after completing a transaction or critical operation
        (e.g., after user registration, after order completion).
        """
        pass  # Default implementation does nothing
    