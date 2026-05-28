"""Tests for number entities (fan speed and fan target temp)."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.number import ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import CMD_FAN_SPEED, CMD_FAN_TARGET, DOMAIN

ENTITY_FAN_SPEED = "number.ps3_fan_speed"
ENTITY_FAN_TARGET = "number.ps3_fan_target_temperature"


async def _setup(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="PS3", data={CONF_HOST: "1.2.3.4", CONF_PORT: 80}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ps3_goldenhen.WebManClient.async_get_status",
        return_value=PS3Status(online=True, fan_speed=35),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


@pytest.mark.asyncio
async def test_fan_speed_set_value(hass):
    """Setting fan speed sends the correct command."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    # Confirm entity exists
    state = hass.states.get(ENTITY_FAN_SPEED)
    assert state is not None, f"{ENTITY_FAN_SPEED} not found"
    print(f"entity_id: {ENTITY_FAN_SPEED}, state: {state.state}")

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: ENTITY_FAN_SPEED, ATTR_VALUE: 50},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_FAN_SPEED.format(speed=50))


@pytest.mark.asyncio
async def test_fan_target_temp_set_value(hass):
    """Setting fan target temp sends the correct command."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    # Confirm entity exists
    state = hass.states.get(ENTITY_FAN_TARGET)
    assert state is not None, f"{ENTITY_FAN_TARGET} not found"
    print(f"entity_id: {ENTITY_FAN_TARGET}, state: {state.state}")

    await hass.services.async_call(
        "number",
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: ENTITY_FAN_TARGET, ATTR_VALUE: 60},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_FAN_TARGET.format(temp=60))
