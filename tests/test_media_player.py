"""Tests for the PS3 media_player entity."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.media_player import MediaPlayerState
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import CMD_SHUTDOWN, DOMAIN

ENTITY_ID = "media_player.ps3"


async def _setup(hass, status: PS3Status):
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
async def test_media_player_state_playing_when_game_title(hass):
    """State is PLAYING when a game title is set."""
    game_title = "God of War: Chains of Olympus (Digital)"
    status = PS3Status(online=True, game_title=game_title)
    await _setup(hass, status)

    state = hass.states.get(ENTITY_ID)
    assert state is not None, f"{ENTITY_ID} not found"
    print(f"entity_id: {ENTITY_ID}, state: {state.state}")
    assert state.state == MediaPlayerState.PLAYING


@pytest.mark.asyncio
async def test_media_player_state_idle_when_online_no_game(hass):
    """State is IDLE when online but no game is running (XMB)."""
    status = PS3Status(online=True, game_title=None)
    await _setup(hass, status)

    state = hass.states.get(ENTITY_ID)
    assert state is not None, f"{ENTITY_ID} not found"
    assert state.state == MediaPlayerState.IDLE


@pytest.mark.asyncio
async def test_media_player_state_off_when_offline(hass):
    """State is OFF when the console is unreachable."""
    status = PS3Status(online=False)
    await _setup(hass, status)

    state = hass.states.get(ENTITY_ID)
    assert state is not None, f"{ENTITY_ID} not found"
    assert state.state == MediaPlayerState.OFF


@pytest.mark.asyncio
async def test_media_player_source_list_from_games(hass):
    """source_list reflects coordinator.games names."""
    status = PS3Status(online=True, game_title=None)
    entry = await _setup(hass, status)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.games = [
        {
            "name": "God of War: Chains of Olympus (Digital)",
            "title_id": "NPUA80637",
            "path": "/dev_hdd0/game/NPUA80637",
            "category": "HG",
        }
    ]
    # Notify listeners without hitting the real network
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert "God of War: Chains of Olympus (Digital)" in state.attributes.get(
        "source_list", []
    )


@pytest.mark.asyncio
async def test_media_player_select_source_sends_play_command(hass):
    """async_select_source sends /play.ps3<path>."""
    status = PS3Status(online=True, game_title=None)
    entry = await _setup(hass, status)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()
    coordinator.games = [
        {
            "name": "God of War: Chains of Olympus (Digital)",
            "title_id": "NPUA80637",
            "path": "/dev_hdd0/game/NPUA80637",
            "category": "HG",
        }
    ]
    # Update listeners without triggering network poll
    coordinator.async_update_listeners()
    await hass.async_block_till_done()

    await hass.services.async_call(
        "media_player",
        "select_source",
        {
            "entity_id": ENTITY_ID,
            "source": "God of War: Chains of Olympus (Digital)",
        },
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(
        "/play.ps3/dev_hdd0/game/NPUA80637"
    )


@pytest.mark.asyncio
async def test_media_player_turn_off_sends_shutdown(hass):
    """async_turn_off sends CMD_SHUTDOWN."""
    status = PS3Status(online=True, game_title=None)
    entry = await _setup(hass, status)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        "media_player",
        "turn_off",
        {"entity_id": ENTITY_ID},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_with(CMD_SHUTDOWN)
