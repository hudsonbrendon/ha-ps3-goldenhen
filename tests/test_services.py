"""Tests for custom services."""
from unittest.mock import AsyncMock, patch
from urllib.parse import quote

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import (
    CMD_FAN_TARGET,
    CMD_PLAY,
    CMD_POPUP,
    DOMAIN,
)


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


@pytest.mark.asyncio
async def test_notify_with_icon_and_sound(hass):
    """notify with icon+sound must use popup.ps3?<msg>&icon=<n>&snd=<n> form."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        DOMAIN,
        "notify",
        {"entry_id": entry.entry_id, "message": "test msg", "icon": 3, "sound": 5},
        blocking=True,
    )
    expected = f"{CMD_POPUP}?{quote('test msg')}&icon=3&snd=5"
    coordinator.client.async_command.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_notify_with_icon_only(hass):
    """notify with only icon omits snd param."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        DOMAIN,
        "notify",
        {"entry_id": entry.entry_id, "message": "hi", "icon": 10},
        blocking=True,
    )
    expected = f"{CMD_POPUP}?{quote('hi')}&icon=10"
    coordinator.client.async_command.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_launch_game_service_quotes_path(hass):
    """Paths with spaces/special chars must be URL-encoded (slashes preserved)."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    path = "/dev_hdd0/PS3ISO/Cool Game (USA).iso"
    await hass.services.async_call(
        DOMAIN, "launch_game",
        {"entry_id": entry.entry_id, "path": path},
        blocking=True,
    )
    expected = CMD_PLAY + quote(path, safe="/")
    coordinator.client.async_command.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_led_service(hass):
    """led service sends /ps3mapi.ps3?PS3%20LED%20<color>%20<mode>."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        DOMAIN,
        "led",
        {"entry_id": entry.entry_id, "color": 2, "mode": 1},
        blocking=True,
    )
    expected = "/ps3mapi.ps3?" + quote("PS3 LED 2 1")
    coordinator.client.async_command.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_mount_service_quotes_path(hass):
    """mount service must URL-encode the path (slashes preserved)."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    path = "/dev_hdd0/PS3ISO/Cool Game (USA).iso"
    await hass.services.async_call(
        DOMAIN,
        "mount",
        {"entry_id": entry.entry_id, "path": path},
        blocking=True,
    )
    expected = f"/mount.ps3{quote(path, safe='/')}"
    coordinator.client.async_command.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_set_fan_target_temp(hass):
    """set_fan_target_temp 60 must call /cpursx.ps3?max=60."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    await hass.services.async_call(
        DOMAIN,
        "set_fan_target_temp",
        {"entry_id": entry.entry_id, "temperature": 60},
        blocking=True,
    )
    expected = CMD_FAN_TARGET.format(temp=60)
    coordinator.client.async_command.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_send_command_passthrough(hass):
    """send_command passes the raw command string unchanged."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_command = AsyncMock()

    raw_cmd = "/popup.ps3/hello world"
    await hass.services.async_call(
        DOMAIN,
        "send_command",
        {"entry_id": entry.entry_id, "command": raw_cmd},
        blocking=True,
    )
    coordinator.client.async_command.assert_awaited_once_with(raw_cmd)


@pytest.mark.asyncio
async def test_read_memory_returns_data(hass):
    """read_memory returns {"data": <response>} from async_get_ps3mapi."""
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.client.async_get_ps3mapi = AsyncMock(return_value="ABCD")

    result = await hass.services.async_call(
        DOMAIN,
        "read_memory",
        {"entry_id": entry.entry_id, "pid": "0x1234", "address": "0xDEAD", "size": 4},
        blocking=True,
        return_response=True,
    )
    assert result == {"data": "ABCD"}
    coordinator.client.async_get_ps3mapi.assert_awaited_once_with(
        "MEMORY GET 0x1234 0xDEAD 4"
    )
