"""Tests for the webMAN MOD API client and parser."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.ps3_goldenhen.api import (
    PS3ConnectionError,
    WebManClient,
    parse_cpursx,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def test_parse_cpursx_extracts_fields():
    status = parse_cpursx(_read("cpursx_reference.html"))
    assert status.online is True
    assert status.cpu_temp == 62.0
    assert status.rsx_temp == 58.0
    assert status.fan_speed == 45
    assert status.firmware == "4.91"
    assert status.free_memory == 213


def test_parse_cpursx_game_title_xmb_is_none():
    """When PS3 is in XMB (menu), game_title should be None."""
    status = parse_cpursx(_read("cpursx_reference.html"))
    assert status.game_title is None


def test_parse_cpursx_game_title_parsed():
    """When a game is running, game_title should reflect the game name."""
    html = "<html>Game: Demon's Souls<br></html>"
    status = parse_cpursx(html)
    assert status.game_title == "Demon's Souls"


def test_parse_cpursx_empty_is_offline_safe():
    status = parse_cpursx("")
    assert status.online is True  # respondeu HTTP, mas sem campos
    assert status.cpu_temp is None


def _mock_session(*, text: str = "", exc: Exception | None = None) -> MagicMock:
    """Build a fake aiohttp session (no real connector → no DNS resolver thread)."""
    session = MagicMock()
    if exc is not None:
        session.get = AsyncMock(side_effect=exc)
    else:
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.text = AsyncMock(return_value=text)
        session.get = AsyncMock(return_value=resp)
    return session


@pytest.mark.asyncio
async def test_client_get_status_ok():
    session = _mock_session(text=_read("cpursx_reference.html"))
    client = WebManClient(session, "1.2.3.4", 80)
    status = await client.async_get_status()
    assert status.cpu_temp == 62.0
    session.get.assert_awaited_once_with("http://1.2.3.4:80/cpursx.ps3")


@pytest.mark.asyncio
async def test_client_connection_error_raises():
    session = _mock_session(exc=aiohttp.ClientError("boom"))
    client = WebManClient(session, "1.2.3.4", 80)
    with pytest.raises(PS3ConnectionError):
        await client.async_get_status()
