"""Tests for the PS3 data update coordinator."""
from unittest.mock import AsyncMock

import pytest

from custom_components.ps3_goldenhen.api import PS3ConnectionError, PS3Status
from custom_components.ps3_goldenhen.coordinator import PS3DataUpdateCoordinator


@pytest.mark.asyncio
async def test_update_returns_status(hass):
    client = AsyncMock()
    client.async_get_status.return_value = PS3Status(online=True, cpu_temp=60.0)
    coordinator = PS3DataUpdateCoordinator(hass, client, scan_interval=30)
    data = await coordinator._async_update_data()
    assert data.online is True
    assert data.cpu_temp == 60.0


@pytest.mark.asyncio
async def test_update_offline_on_connection_error(hass):
    client = AsyncMock()
    client.async_get_status.side_effect = PS3ConnectionError("down")
    coordinator = PS3DataUpdateCoordinator(hass, client, scan_interval=30)
    data = await coordinator._async_update_data()
    assert data.online is False
