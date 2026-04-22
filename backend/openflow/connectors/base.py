from abc import ABC, abstractmethod
from typing import Any


class BasePlatformConnector(ABC):
    """Abstract base for all platform connectors (Teams, Slack, etc.)."""

    @abstractmethod
    async def send_message(self, conversation_id: str, text: str, **kwargs: Any) -> None:
        """Send a text message to the given conversation."""

    @abstractmethod
    async def handle_incoming(self, body: bytes, auth_header: str) -> Any:
        """Process a raw incoming webhook body and auth header."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Unique identifier for the platform (e.g. 'teams', 'slack')."""
