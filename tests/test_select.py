"""Tests for select entities (fan mode select, game launcher)."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION, CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import CMD_FAN_AUTO, CMD_FAN_MANUAL, DOMAIN

ENTITY_ID = "select.ps3_fan_mode"
LAUNCHER_ENTITY_ID = "select.ps3_game_launcher"


async def _setup(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, title="PS3", data={CONF_HOST: "1.2.3.4", CONF_PORT: 80}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ps3_goldenhen.WebManClient.async_get_status",
        return_value=PS3Status(online=True, fan_mode="Dynamic"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


@pytest.mark.asyncio
async def test_select_manual_sends_cmd_fan_manual(hass):
    """Selecting 'Manual' sends CMD_FAN_MANUAL."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    # Confirm entity exists
    state = hass.states.get(ENTITY_ID)
    assert state is not None, f"{ENTITY_ID} not found"
    print(f"entity_id: {ENTITY_ID}, state: {state.state}")

    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_OPTION: "Manual"},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_FAN_MANUAL)


@pytest.mark.asyncio
async def test_select_dynamic_sends_cmd_fan_auto(hass):
    """Selecting 'Dynamic' sends CMD_FAN_AUTO."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_OPTION: "Dynamic"},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_FAN_AUTO)


@pytest.mark.asyncio
async def test_game_launcher_select_option_sends_play_command(hass):
    """Selecting a game name sends /play.ps3<path> command."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    # Populate game list manually
    game = {
        "name": "God of War: Chains of Olympus (Digital)",
        "title_id": "NPUA80637",
        "path": "/dev_hdd0/game/NPUA80637",
        "category": "HG",
    }
    coordinator.games = [game]
    # Notify listeners without hitting the real network
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get(LAUNCHER_ENTITY_ID)
    assert state is not None, f"{LAUNCHER_ENTITY_ID} not found"
    print(f"entity_id: {LAUNCHER_ENTITY_ID}, state: {state.state}")

    await hass.services.async_call(
        "select",
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: LAUNCHER_ENTITY_ID, ATTR_OPTION: game["name"]},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(
        "/play.ps3/dev_hdd0/game/NPUA80637"
    )
