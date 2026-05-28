"""Tests for the webMAN MOD API client and parser."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.ps3_goldenhen.api import (
    PS3ConnectionError,
    WebManClient,
    parse_cpursx,
    parse_game_folders,
    parse_sfo,
)

FIXTURES = Path(__file__).parent / "fixtures"

# Minimal XMB-like page (no running game): has metrics but no game link/cover.
XMB_HTML = (
    "<html>CPU: 50°C [FAN: 30% Dynamic] RSX: 52°C<br>"
    '<a href="/games.ps3">MEM: 2,000 KB </a><br>HDD: 391.0 GB Livres<br>'
    "NOR Firmware: 4.91 CEX PS3HEN 3.3.0<br></html>"
)


def _make_resp(text: str) -> MagicMock:
    """Build a single fake aiohttp response."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.text = AsyncMock(return_value=text)
    return resp


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def _read_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


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
    # --- Onda 1 new fields ---
    assert status.fan_mode == "Manual"
    assert status.runtime == "178d 02:32:24"
    assert status.boots_on == 1838
    assert status.boots_off == 1602
    assert status.hen_version == "PS3HEN 3.3.0"
    assert status.webman_version == "1.47.48n"
    assert status.mac_address == "28:0D:FC:73:D0:A2"
    assert status.ip_address == "192.168.31.88"
    assert status.connection == "WLAN"
    assert status.bd_drive == "SONY PS-SYSTEM 310R8048"
    assert status.flash_type == "NOR"
    assert status.game_title_id == "NPUA80637"
    assert status.game_bg_url == "/dev_hdd0/game//NPUA80637/PIC1.PNG"


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
    # Game-specific new fields are None in XMB.
    assert status.game_title_id is None
    assert status.game_bg_url is None


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
    # session.get returns cpursx HTML for the first call; ps3mapi returns None (error)
    # for the second call — connection error is swallowed and console_type stays None.
    cpursx_resp = _make_resp(_read("cpursx_ingame.html"))
    session = MagicMock()
    session.get = AsyncMock(
        side_effect=[cpursx_resp, aiohttp.ClientError("no ps3mapi")]
    )
    client = WebManClient(session, "1.2.3.4", 80)
    status = await client.async_get_status()
    assert status.cpu_temp == 49.0
    # The client absolutises the cover path against the console base URL.
    assert status.game_icon_url == "http://1.2.3.4:80/dev_hdd0/game//NPUA80637/ICON0.PNG"
    # First call must be the cpursx endpoint.
    assert session.get.await_args_list[0].args[0] == "http://1.2.3.4:80/cpursx.ps3"


@pytest.mark.asyncio
async def test_client_connection_error_raises():
    session = _mock_session(exc=aiohttp.ClientError("boom"))
    client = WebManClient(session, "1.2.3.4", 80)
    with pytest.raises(PS3ConnectionError):
        await client.async_get_status()


@pytest.mark.asyncio
async def test_client_console_type_and_bg_url_absolutised():
    """Two-call test: cpursx HTML first, then ps3mapi GETFWTYPE JSON second."""
    cpursx_html = _read("cpursx_ingame.html")
    cpursx_resp = _make_resp(cpursx_html)
    ps3mapi_resp = _make_resp('{"response": "CEX COBRA"}')

    session = MagicMock()
    session.get = AsyncMock(side_effect=[cpursx_resp, ps3mapi_resp])

    client = WebManClient(session, "1.2.3.4", 80)
    status = await client.async_get_status()

    assert status.console_type == "CEX COBRA"
    assert status.cobra is True
    assert status.game_icon_url == "http://1.2.3.4:80/dev_hdd0/game//NPUA80637/ICON0.PNG"
    assert status.game_bg_url == "http://1.2.3.4:80/dev_hdd0/game//NPUA80637/PIC1.PNG"


# ---------------------------------------------------------------------------
# v0.3.0: PARAM.SFO parser
# ---------------------------------------------------------------------------


def test_parse_sfo_real_fixture():
    """Parse the real NPUA80637 PARAM.SFO fixture."""
    sfo = parse_sfo(_read_bytes("param_npua80637.sfo"))
    assert sfo["TITLE"].startswith("God of War")
    assert "Chains of Olympus" in sfo["TITLE"]
    assert sfo["TITLE_ID"] == "NPUA80637"
    assert sfo["CATEGORY"] == "HG"


def test_parse_sfo_invalid_magic_returns_empty():
    assert parse_sfo(b"INVALID_MAGIC") == {}


def test_parse_sfo_empty_bytes_returns_empty():
    assert parse_sfo(b"") == {}


# ---------------------------------------------------------------------------
# v0.3.0: parse_game_folders
# ---------------------------------------------------------------------------


def test_parse_game_folders_from_fixture():
    """All folders are found in the real listing fixture."""
    html = _read("devhdd0_game_listing.html")
    folders = parse_game_folders(html)
    assert "NPUA80637" in folders
    assert "FILEMANAG" in folders
    # No duplicates
    assert len(folders) == len(set(folders))


# ---------------------------------------------------------------------------
# v0.3.0: async_get_games integration test
# ---------------------------------------------------------------------------


def _make_bytes_resp(data: bytes) -> MagicMock:
    """Build a fake aiohttp response that returns bytes via resp.read()."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.read = AsyncMock(return_value=data)
    return resp


@pytest.mark.asyncio
async def test_async_get_games_returns_game_list():
    """async_get_games fetches the listing then each PARAM.SFO."""
    listing_html = _read("devhdd0_game_listing.html")
    sfo_bytes = _read_bytes("param_npua80637.sfo")

    # First call → listing (text), subsequent calls → PARAM.SFO (bytes)
    listing_resp = _make_resp(listing_html)

    # We need to build bytes responses for every folder found in the listing.
    # For simplicity, every folder returns the same NPUA80637 SFO so all
    # results will have TITLE and CATEGORY=="HG" (not "GD") and will survive.
    folders = parse_game_folders(listing_html)
    sfo_resps = [_make_bytes_resp(sfo_bytes) for _ in folders]

    session = MagicMock()
    session.get = AsyncMock(side_effect=[listing_resp] + sfo_resps)

    client = WebManClient(session, "1.2.3.4", 80)
    games = await client.async_get_games()

    assert len(games) > 0
    names = [g["name"] for g in games]
    # All games carry the real SFO title (same fixture repeated)
    assert any("God of War" in n for n in names)
    paths = [g["path"] for g in games]
    assert "/dev_hdd0/game/NPUA80637" in paths
