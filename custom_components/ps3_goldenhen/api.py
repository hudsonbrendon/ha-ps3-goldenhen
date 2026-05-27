"""HTTP client and HTML parser for webMAN MOD on a jailbroken PS3."""
from __future__ import annotations

import re
from dataclasses import dataclass

import aiohttp
import async_timeout

from .const import CMD_STATUS, HTTP_TIMEOUT


class PS3ConnectionError(Exception):
    """Raised when the PS3/webMAN cannot be reached."""


@dataclass
class PS3Status:
    """Snapshot of the PS3 state parsed from /cpursx.ps3."""

    online: bool = False
    cpu_temp: float | None = None
    rsx_temp: float | None = None
    fan_speed: int | None = None
    firmware: str | None = None
    free_memory: int | None = None  # MB
    game_title: str | None = None
    raw: str = ""


# Regex defensivos — alvo são tokens estáveis do webMAN MOD.
# Normalizamos &deg; -> ° antes de aplicar.
_RE_TEMP = re.compile(r"(\d+(?:\.\d+)?)\s*°C")
_RE_FAN = re.compile(r"(\d+)\s*%")
_RE_FW = re.compile(r"\b(\d\.\d{2})\b")
_RE_MEM = re.compile(r"(\d+)\s*MB", re.IGNORECASE)


def parse_cpursx(html: str) -> PS3Status:
    """Parse the HTML returned by /cpursx.ps3 into a PS3Status."""
    text = html.replace("&deg;", "°")
    status = PS3Status(online=True, raw=html)

    temps = _RE_TEMP.findall(text)
    if len(temps) >= 1:
        status.cpu_temp = float(temps[0])
    if len(temps) >= 2:
        status.rsx_temp = float(temps[1])

    if (m := _RE_FAN.search(text)) is not None:
        status.fan_speed = int(m.group(1))
    if (m := _RE_FW.search(text)) is not None:
        status.firmware = m.group(1)
    if (m := _RE_MEM.search(text)) is not None:
        status.free_memory = int(m.group(1))

    return status


class WebManClient:
    """Talks to the webMAN MOD HTTP server on the PS3."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = 80,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"

    @property
    def base_url(self) -> str:
        return self._base

    async def _get(self, path: str) -> str:
        url = f"{self._base}{path}"
        try:
            async with async_timeout.timeout(HTTP_TIMEOUT):
                resp = await self._session.get(url)
                resp.raise_for_status()
                return await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise PS3ConnectionError(str(err)) from err

    async def async_get_status(self) -> PS3Status:
        """Fetch and parse /cpursx.ps3."""
        return parse_cpursx(await self._get(CMD_STATUS))

    async def async_command(self, path: str) -> None:
        """Fire a webMAN web command (fire-and-forget GET)."""
        await self._get(path)
