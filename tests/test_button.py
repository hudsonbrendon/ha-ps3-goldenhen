"""Tests for button entities."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import CMD_SHUTDOWN, DOMAIN


@pytest.mark.asyncio
async def test_shutdown_button_calls_command(hass):
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

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    # shutdown has device_class="restart" -> entity_id is button.ps3_restart (no translations)
    await hass.services.async_call(
        "button",
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.ps3_restart"},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_once_with(CMD_SHUTDOWN)
