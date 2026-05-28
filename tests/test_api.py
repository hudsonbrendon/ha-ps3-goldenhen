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

# Minimal XMB-like page (no running game): has metrics but no game link/cover.
XMB_HTML = (
    "<html>CPU: 50°C [FAN: 30% Dynamic] RSX: 52°C<br>"
    '<a href="/games.ps3">MEM: 2,000 KB </a><br>HDD: 391.0 GB Livres<br>'
    "NOR Firmware: 4.91 CEX PS3HEN 3.3.0<br></html>"
)


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def test_parse_cpursx_real_ingame_fixture():
    """Real /cpursx.ps3 capture with a game running (God of War, NPUA80637)."""
    status = parse_cpursx(_read("cpursx_ingame.html"))
    assert status.online is True
    assert status.cpu_temp == 49.0
    assert status.rsx_temp == 58.0
    assert status.fan_speed == 34
    assert status.firmware == "4.91 CEX PS3HEN 3.3.0"
    assert status.free_memory == 1204  # "MEM: 1,204 KB"
    assert status.hdd_free == 391.0  # "HDD: 391.0 GB"
    assert status.game_title is not None
    assert status.game_title.startswith("God of War")
    assert "Chains of Olympus" in status.game_title
    assert status.game_icon_url == "/dev_hdd0/game//NPUA80637/ICON0.PNG"


def test_parse_cpursx_xmb_has_no_game():
    """In the XMB there is no running game nor cover."""
    status = parse_cpursx(XMB_HTML)
    assert status.game_title is None
    assert status.game_icon_url is None
    # Metrics still parse.
    assert status.cpu_temp == 50.0
    assert status.fan_speed == 30
    assert status.free_memory == 2000
    assert status.hdd_free == 391.0
    assert status.firmware == "4.91 CEX PS3HEN 3.3.0"


def test_parse_cpursx_empty_is_offline_safe():
    status = parse_cpursx("")
    assert status.online is True  # respondeu HTTP, mas sem campos
    assert status.cpu_temp is None
    assert status.game_title is None


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
    session = _mock_session(text=_read("cpursx_ingame.html"))
    client = WebManClient(session, "1.2.3.4", 80)
    status = await client.async_get_status()
    assert status.cpu_temp == 49.0
    # The client absolutises the cover path against the console base URL.
    assert status.game_icon_url == "http://1.2.3.4:80/dev_hdd0/game//NPUA80637/ICON0.PNG"
    session.get.assert_awaited_once_with("http://1.2.3.4:80/cpursx.ps3")


@pytest.mark.asyncio
async def test_client_connection_error_raises():
    session = _mock_session(exc=aiohttp.ClientError("boom"))
    client = WebManClient(session, "1.2.3.4", 80)
    with pytest.raises(PS3ConnectionError):
        await client.async_get_status()
