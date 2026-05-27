"""Tests for the webMAN MOD API client and parser."""
from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.ps3_goldenhen.api import (
    PS3ConnectionError,
    PS3Status,
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


def test_parse_cpursx_empty_is_offline_safe():
    status = parse_cpursx("")
    assert status.online is True  # respondeu HTTP, mas sem campos
    assert status.cpu_temp is None


@pytest.mark.asyncio
async def test_client_get_status_ok():
    with aioresponses() as mocked:
        mocked.get(
            "http://1.2.3.4:80/cpursx.ps3",
            body=_read("cpursx_reference.html"),
        )
        async with aiohttp.ClientSession() as session:
            client = WebManClient(session, "1.2.3.4", 80)
            status = await client.async_get_status()
    assert status.cpu_temp == 62.0


@pytest.mark.asyncio
async def test_client_connection_error_raises():
    with aioresponses() as mocked:
        mocked.get(
            "http://1.2.3.4:80/cpursx.ps3",
            exception=aiohttp.ClientError("boom"),
        )
        async with aiohttp.ClientSession() as session:
            client = WebManClient(session, "1.2.3.4", 80)
            with pytest.raises(PS3ConnectionError):
                await client.async_get_status()
