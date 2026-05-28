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


@pytest.mark.asyncio
async def test_game_changed_event_fired_on_title_id_change(hass):
    """Two successive polls with different game_title_id must fire the event."""
    fired_events = []

    hass.bus.async_listen(
        "ps3_goldenhen_event", lambda event: fired_events.append(event.data)
    )

    client = AsyncMock()
    coordinator = PS3DataUpdateCoordinator(hass, client, scan_interval=30)

    # First poll: game NPUA80637 running
    client.async_get_status.return_value = PS3Status(
        online=True,
        game_title_id="NPUA80637",
        game_title="God of War",
    )
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert len(fired_events) == 1
    assert fired_events[0]["type"] == "game_changed"
    assert fired_events[0]["title_id"] == "NPUA80637"
    assert fired_events[0]["title"] == "God of War"

    # Second poll: different game
    client.async_get_status.return_value = PS3Status(
        online=True,
        game_title_id="BLUS31104",
        game_title="The Last of Us",
    )
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert len(fired_events) == 2
    assert fired_events[1]["title_id"] == "BLUS31104"
    assert fired_events[1]["title"] == "The Last of Us"


@pytest.mark.asyncio
async def test_game_changed_event_not_fired_on_same_title_id(hass):
    """Repeated polls with the same game_title_id must NOT fire the event again."""
    fired_events = []

    hass.bus.async_listen(
        "ps3_goldenhen_event", lambda event: fired_events.append(event.data)
    )

    client = AsyncMock()
    client.async_get_status.return_value = PS3Status(
        online=True,
        game_title_id="NPUA80637",
        game_title="God of War",
    )
    coordinator = PS3DataUpdateCoordinator(hass, client, scan_interval=30)

    await coordinator._async_update_data()
    await hass.async_block_till_done()
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    # Event fires only once (first detection)
    assert len(fired_events) == 1


@pytest.mark.asyncio
async def test_game_changed_event_fired_when_game_closes(hass):
    """When a game exits (title_id becomes None), the event must fire."""
    fired_events = []

    hass.bus.async_listen(
        "ps3_goldenhen_event", lambda event: fired_events.append(event.data)
    )

    client = AsyncMock()
    coordinator = PS3DataUpdateCoordinator(hass, client, scan_interval=30)

    # Game running
    client.async_get_status.return_value = PS3Status(
        online=True,
        game_title_id="NPUA80637",
        game_title="God of War",
    )
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    # Game closed
    client.async_get_status.return_value = PS3Status(
        online=True,
        game_title_id=None,
        game_title=None,
    )
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert len(fired_events) == 2
    assert fired_events[1]["title_id"] is None
    assert fired_events[1]["title"] is None
