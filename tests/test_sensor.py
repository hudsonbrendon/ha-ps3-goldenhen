"""Tests for sensor entities."""
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import DOMAIN


async def _setup(hass, status: PS3Status) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, title="PS3", data={CONF_HOST: "1.2.3.4", CONF_PORT: 80}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ps3_goldenhen.WebManClient.async_get_status",
        return_value=status,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_cpu_temp_sensor(hass):
    await _setup(hass, PS3Status(online=True, cpu_temp=62.0, rsx_temp=58.0))
    assert hass.states.get("sensor.ps3_cpu_temperature").state == "62.0"
    assert hass.states.get("sensor.ps3_rsx_temperature").state == "58.0"


@pytest.mark.asyncio
async def test_fan_and_memory_sensors(hass):
    await _setup(hass, PS3Status(online=True, fan_speed=45, free_memory=213))
    assert hass.states.get("sensor.ps3_fan_speed").state == "45"
    assert hass.states.get("sensor.ps3_free_memory").state == "213"


@pytest.mark.asyncio
async def test_sensor_unavailable_when_offline(hass):
    await _setup(hass, PS3Status(online=False))
    assert hass.states.get("sensor.ps3_cpu_temperature").state == "unavailable"
