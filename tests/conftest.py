"""Shared pytest fixtures."""
from unittest.mock import MagicMock, patch

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


@pytest.fixture(autouse=True)
def mock_clientsession():
    """Hand the integration a fake aiohttp session.

    The real ``async_get_clientsession`` builds an aiohttp session whose DNS
    resolver (pycares) spawns a daemon thread that pytest-homeassistant's
    ``verify_cleanup`` rejects, failing the run in CI. Tests mock the actual
    HTTP calls (``WebManClient.async_get_status`` / ``async_command``), so a
    fake session here is sufficient and avoids the lingering thread. Patched on
    the names bound inside our modules (they use ``from ... import``).
    """
    session = MagicMock()
    with (
        patch(
            "custom_components.ps3_goldenhen.async_get_clientsession",
            return_value=session,
        ),
        patch(
            "custom_components.ps3_goldenhen.config_flow.async_get_clientsession",
            return_value=session,
        ),
    ):
        yield session
