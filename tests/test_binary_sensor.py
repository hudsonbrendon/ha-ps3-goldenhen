"""Tests for the connectivity binary sensor."""
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import DOMAIN


async def _setup(hass, status: PS3Status) -> MockConfigEntry:
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
    return entry


@pytest.mark.asyncio
async def test_online_true(hass):
    await _setup(hass, PS3Status(online=True))
    state = hass.states.get("binary_sensor.ps3_online")
    assert state is not None
    assert state.state == "on"


@pytest.mark.asyncio
async def test_online_false(hass):
    await _setup(hass, PS3Status(online=False))
    state = hass.states.get("binary_sensor.ps3_online")
    assert state.state == "off"


@pytest.mark.asyncio
async def test_game_running_on_when_game_title_set(hass):
    """game_running is on when a game_title is present."""
    # entity_id confirmed: binary_sensor.ps3_game_running
    await _setup(
        hass,
        PS3Status(online=True, game_title="God of War®: Chains of Olympus (Digital)"),
    )
    state = hass.states.get("binary_sensor.ps3_game_running")
    assert state is not None
    assert state.state == "on"


@pytest.mark.asyncio
async def test_game_running_off_when_no_game(hass):
    """game_running is off when no game is running."""
    await _setup(hass, PS3Status(online=True, game_title=None))
    state = hass.states.get("binary_sensor.ps3_game_running")
    assert state is not None
    assert state.state == "off"


@pytest.mark.asyncio
async def test_game_running_unavailable_when_offline(hass):
    """game_running is unavailable when the PS3 is offline."""
    await _setup(hass, PS3Status(online=False))
    state = hass.states.get("binary_sensor.ps3_game_running")
    assert state.state == "unavailable"


@pytest.mark.asyncio
async def test_cobra_mode_on(hass):
    """cobra_mode is on when cobra=True."""
    # entity_id confirmed: binary_sensor.ps3_cobra_mode
    await _setup(hass, PS3Status(online=True, cobra=True))
    state = hass.states.get("binary_sensor.ps3_cobra_mode")
    assert state is not None
    assert state.state == "on"


@pytest.mark.asyncio
async def test_cobra_mode_off(hass):
    """cobra_mode is off when cobra is False or None."""
    await _setup(hass, PS3Status(online=True, cobra=False))
    state = hass.states.get("binary_sensor.ps3_cobra_mode")
    assert state is not None
    assert state.state == "off"


@pytest.mark.asyncio
async def test_cobra_mode_unavailable_when_offline(hass):
    """cobra_mode is unavailable when the PS3 is offline."""
    await _setup(hass, PS3Status(online=False))
    state = hass.states.get("binary_sensor.ps3_cobra_mode")
    assert state.state == "unavailable"
