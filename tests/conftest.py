"""Shared pytest fixtures."""
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture(autouse=True)
def mock_async_refresh_games():
    """Patch PS3DataUpdateCoordinator.async_refresh_games to be a no-op by default.

    async_refresh_games is called during entry setup; without this patch the
    real HTTP path is executed with a MagicMock session, which fails.  Tests
    that need real game data set coordinator.games directly after setup.
    """
    with patch(
        "custom_components.ps3_goldenhen.coordinator.PS3DataUpdateCoordinator.async_refresh_games",
        new=AsyncMock(return_value=None),
    ):
        yield
