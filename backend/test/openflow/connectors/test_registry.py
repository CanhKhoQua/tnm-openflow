"""
Unit tests for openflow.connectors.registry

Tested functions:
- register(connector) -> None
- get(name) -> BasePlatformConnector | None
- all_connectors() -> list[BasePlatformConnector]

Each test uses pytest's monkeypatch fixture to reset the module-level
_registry dict so tests are fully isolated from one another.
"""
from typing import Any

import pytest

from openflow.connectors.base import BasePlatformConnector
import openflow.connectors.registry as registry_module
from openflow.connectors.registry import all_connectors, get, register


# ---------------------------------------------------------------------------
# Minimal concrete connector for testing
# ---------------------------------------------------------------------------


class _FakeConnector(BasePlatformConnector):
    """Minimal BasePlatformConnector subclass used only in tests."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def platform_name(self) -> str:
        return self._name

    async def send_message(self, conversation_id: str, text: str, **kwargs: Any) -> None:
        pass  # not exercised in these tests

    async def handle_incoming(self, body: bytes, auth_header: str) -> Any:
        return None  # not exercised in these tests


# ---------------------------------------------------------------------------
# Fixture: isolate the shared _registry dict between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the module-level _registry with a fresh empty dict for every test."""
    monkeypatch.setattr(registry_module, "_registry", {})


# ---------------------------------------------------------------------------
# register + get
# ---------------------------------------------------------------------------


def test_register_and_get_by_name():
    # Arrange
    connector = _FakeConnector("teams")

    # Act
    register(connector)
    result = get("teams")

    # Assert
    assert result is connector


def test_get_returns_the_exact_instance_registered():
    # Arrange
    connector = _FakeConnector("slack")
    register(connector)

    # Act
    result = get("slack")

    # Assert
    assert result is connector


def test_registering_twice_overwrites_with_latest():
    # Arrange
    first = _FakeConnector("teams")
    second = _FakeConnector("teams")

    # Act
    register(first)
    register(second)

    # Assert
    assert get("teams") is second


# ---------------------------------------------------------------------------
# get unknown name
# ---------------------------------------------------------------------------


def test_get_unknown_name_returns_none():
    # Act
    result = get("nonexistent")

    # Assert
    assert result is None


def test_get_on_empty_registry_returns_none():
    # Act (registry is empty due to fixture)
    result = get("teams")

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# all_connectors
# ---------------------------------------------------------------------------


def test_all_connectors_returns_list():
    # Act
    result = all_connectors()

    # Assert
    assert isinstance(result, list)


def test_all_connectors_empty_when_nothing_registered():
    # Act
    result = all_connectors()

    # Assert
    assert result == []


def test_all_connectors_contains_registered_connector():
    # Arrange
    connector = _FakeConnector("teams")
    register(connector)

    # Act
    result = all_connectors()

    # Assert
    assert connector in result


def test_all_connectors_contains_all_registered_connectors():
    # Arrange
    teams = _FakeConnector("teams")
    slack = _FakeConnector("slack")
    register(teams)
    register(slack)

    # Act
    result = all_connectors()

    # Assert
    assert len(result) == 2
    assert teams in result
    assert slack in result


def test_all_connectors_returns_new_list_not_internal_dict_values():
    """Mutating the returned list must not affect the registry."""
    # Arrange
    connector = _FakeConnector("teams")
    register(connector)

    # Act
    result = all_connectors()
    result.clear()

    # Assert — registry still intact
    assert get("teams") is connector
