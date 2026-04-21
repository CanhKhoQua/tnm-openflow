from openflow.connectors.base import BasePlatformConnector

_registry: dict[str, BasePlatformConnector] = {}


def register(connector: BasePlatformConnector) -> None:
    _registry[connector.platform_name] = connector


def get(name: str) -> BasePlatformConnector | None:
    return _registry.get(name)


def all_connectors() -> list[BasePlatformConnector]:
    return list(_registry.values())
