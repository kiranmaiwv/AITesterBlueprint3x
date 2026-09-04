"""Data gateway: deterministic fixture/live star-schema snapshot reading."""

from .base import DataProvider
from .fixture_provider import FixtureDataProvider
from .gateway import DataGateway
from .live_provider import LiveDataProvider

__all__ = [
    "DataGateway",
    "DataProvider",
    "FixtureDataProvider",
    "LiveDataProvider",
]
