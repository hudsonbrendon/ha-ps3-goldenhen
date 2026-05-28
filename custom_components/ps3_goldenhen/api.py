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
    free_memory: int | None = None  # KB (webMAN reports "MEM: N KB")
    hdd_free: float | None = None  # GB (webMAN reports "HDD: N GB Livres")
    game_title: str | None = None
    game_icon_url: str | None = None  # relative path; absolutised by WebManClient
    raw: str = ""


# Regexes anchored to the real webMAN MOD /cpursx.ps3 markup. Examples:
#   CPU: 49°C [FAN: 34% Manual] RSX: 58°C
#   <a href="/games.ps3">MEM: 1,204 KB </a><br><a href="/dev_hdd0">HDD: 391.0 GB Livres
#   NOR Firmware: 4.91 CEX PS3HEN 3.3.0<br>
#   <a href="http://google.com/search?q=God of War®: ...">God of War®: ... 01.00</a>
#   <img src="/dev_hdd0/game//NPUA80637/ICON0.PNG" ...>
_RE_TEMP = re.compile(r"(\d+(?:\.\d+)?)\s*°C")
_RE_FAN = re.compile(r"FAN:\s*(\d+)\s*%", re.IGNORECASE)
_RE_FW = re.compile(r"Firmware:\s*([^<\n]+)", re.IGNORECASE)
_RE_MEM = re.compile(r"MEM:\s*([\d,]+)\s*KB", re.IGNORECASE)
_RE_HDD = re.compile(r"HDD:\s*([\d.]+)\s*GB", re.IGNORECASE)
_RE_GAME = re.compile(r'search\?q=([^"]+)"')
_RE_ICON = re.compile(r'(/dev_hdd0/[^"]*?ICON0\.PNG)', re.IGNORECASE)


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
        status.firmware = m.group(1).strip()
    if (m := _RE_MEM.search(text)) is not None:
        status.free_memory = int(m.group(1).replace(",", ""))
    if (m := _RE_HDD.search(text)) is not None:
        status.hdd_free = float(m.group(1))
    if (m := _RE_GAME.search(text)) is not None:
        title = m.group(1).strip()
        status.game_title = None if not title or title.upper() == "XMB" else title
    if (m := _RE_ICON.search(text)) is not None:
        status.game_icon_url = m.group(1)

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
        status = parse_cpursx(await self._get(CMD_STATUS))
        if status.game_icon_url and status.game_icon_url.startswith("/"):
            status.game_icon_url = f"{self._base}{status.game_icon_url}"
        return status

    async def async_command(self, path: str) -> None:
        """Fire a webMAN web command (fire-and-forget GET)."""
        await self._get(path)
