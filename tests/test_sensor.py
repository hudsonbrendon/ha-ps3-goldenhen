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


@pytest.mark.asyncio
async def test_extended_sensors(hass):
    """Test the Onda 2 extended diagnostic/status sensors."""
    await _setup(
        hass,
        PS3Status(
            online=True,
            runtime="178d 02:32:24",
            boots_on=1838,
            fan_mode="Manual",
            console_type="CEX COBRA",
            hen_version="PS3HEN 3.3.0",
            webman_version="1.47.48n",
            connection="WLAN",
            mac_address="aa:bb",
            bd_drive="SONY PS-SYSTEM 310R8048",
            flash_type="NOR",
            game_title_id="NPUA80637",
        ),
    )
    # entity_ids confirmed via registration log:
    # sensor.ps3_total_runtime, sensor.ps3_boot_count, sensor.ps3_fan_mode,
    # sensor.ps3_console_type, sensor.ps3_hen_version, sensor.ps3_webman_version,
    # sensor.ps3_connection, sensor.ps3_mac_address, sensor.ps3_blu_ray_drive,
    # sensor.ps3_flash_type, sensor.ps3_title_id
    assert hass.states.get("sensor.ps3_total_runtime").state == "178d 02:32:24"
    assert hass.states.get("sensor.ps3_boot_count").state == "1838"
    assert hass.states.get("sensor.ps3_fan_mode").state == "Manual"
    assert hass.states.get("sensor.ps3_console_type").state == "CEX COBRA"
    assert hass.states.get("sensor.ps3_hen_version").state == "PS3HEN 3.3.0"
    assert hass.states.get("sensor.ps3_webman_version").state == "1.47.48n"
    assert hass.states.get("sensor.ps3_connection").state == "WLAN"
    assert hass.states.get("sensor.ps3_mac_address").state == "aa:bb"
    bd = hass.states.get("sensor.ps3_blu_ray_drive").state
    assert bd == "SONY PS-SYSTEM 310R8048"
    assert hass.states.get("sensor.ps3_flash_type").state == "NOR"
    assert hass.states.get("sensor.ps3_title_id").state == "NPUA80637"


@pytest.mark.asyncio
async def test_extended_sensors_unavailable_when_offline(hass):
    """Extended sensors are unavailable when the PS3 is offline."""
    await _setup(hass, PS3Status(online=False))
    assert hass.states.get("sensor.ps3_total_runtime").state == "unavailable"
    assert hass.states.get("sensor.ps3_boot_count").state == "unavailable"
