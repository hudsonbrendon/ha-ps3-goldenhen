"""Tests for the fan-mode switch."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.switch import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import CMD_FAN_AUTO, CMD_FAN_MANUAL, DOMAIN


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
async def test_fan_switch_on_off(hass):
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        "switch", SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.ps3_fan_auto"}, blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_FAN_AUTO)
    assert hass.states.get("switch.ps3_fan_auto").state == "on"

    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.ps3_fan_auto"}, blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_FAN_MANUAL)
    assert hass.states.get("switch.ps3_fan_auto").state == "off"
