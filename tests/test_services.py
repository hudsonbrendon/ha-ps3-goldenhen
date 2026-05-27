"""Tests for custom services."""
from unittest.mock import AsyncMock, patch
from urllib.parse import quote

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import CMD_POPUP, DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="PS3", data={CONF_HOST: "1.2.3.4", CONF_PORT: 80}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ps3_goldenhen.WebManClient.async_get_status",
        return_value=PS3Status(online=True),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


@pytest.mark.asyncio
async def test_notify_service(hass):
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        DOMAIN, "notify",
        {"entry_id": entry.entry_id, "message": "ola mundo"},
        blocking=True,
    )
    expected = f"{CMD_POPUP}/{quote('ola mundo')}"
    coordinator.client.async_command.assert_awaited_once_with(expected)
