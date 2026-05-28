"""HTTP client and HTML parser for webMAN MOD on a jailbroken PS3."""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote

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
    # --- Onda 1 extended fields ---
    fan_mode: str | None = None  # "Manual" | "Dynamic"
    runtime: str | None = None  # "178d 02:32:24"
    boots_on: int | None = None  # total ON boot count
    boots_off: int | None = None  # total OFF boot count
    console_type: str | None = None  # "CEX COBRA" (from ps3mapi GETFWTYPE)
    cobra: bool | None = None  # "COBRA" in console_type
    hen_version: str | None = None  # "PS3HEN 3.3.0"
    webman_version: str | None = None  # "1.47.48n"
    connection: str | None = None  # "WLAN" | "LAN"
    mac_address: str | None = None  # "28:0D:FC:73:D0:A2"
    ip_address: str | None = None  # "192.168.31.88"
    bd_drive: str | None = None  # "SONY PS-SYSTEM 310R8048"
    flash_type: str | None = None  # "NOR" | "NAND"
    game_title_id: str | None = None  # "NPUA80637"
    game_app_version: str | None = None  # "01.00" (best-effort)
    game_bg_url: str | None = None  # PIC1.PNG path; absolutised by WebManClient


# Regexes anchored to the real webMAN MOD /cpursx.ps3 markup. Examples:
#   CPU: 49°C [FAN: 34% Manual] RSX: 58°C
#   <a href="/games.ps3">MEM: 1,204 KB </a><br><a href="/dev_hdd0">HDD: 391.0 GB Livres
#   NOR Firmware: 4.91 CEX PS3HEN 3.3.0<br>
#   <a href="http://google.com/search?q=God of War®: ...">God of War®: ... 01.00</a>
#   <img src="/dev_hdd0/game//NPUA80637/ICON0.PNG" ...>
#   178d 02:32:24 • 1,838 ON • 1,602 OFF (236)
#   BD info: SONY    PS-SYSTEM   310R8048   <hr>...NOR Firmware: ...
#   MAC Addr : 28:0D:FC:73:D0:A2 - 192.168.31.88 WLAN
#   webMAN 1.47.48n MOD - ...
_RE_TEMP = re.compile(r"(\d+(?:\.\d+)?)\s*°C")
_RE_FAN = re.compile(r"FAN:\s*(\d+)\s*%", re.IGNORECASE)
_RE_FW = re.compile(r"Firmware:\s*([^<\n]+)", re.IGNORECASE)
_RE_MEM = re.compile(r"MEM:\s*([\d,]+)\s*KB", re.IGNORECASE)
_RE_HDD = re.compile(r"HDD:\s*([\d.]+)\s*GB", re.IGNORECASE)
_RE_GAME = re.compile(r'search\?q=([^"]+)"')
_RE_ICON = re.compile(r'(/dev_hdd0/[^"]*?ICON0\.PNG)', re.IGNORECASE)
# Onda 1 regexes
_RE_FAN_MODE = re.compile(r"FAN:\s*\d+%\s*([A-Za-z]+)")
_RE_RUNTIME = re.compile(r"(\d+d\s+\d{2}:\d{2}:\d{2})")
_RE_BOOTS_ON = re.compile(r"([\d,]+)\s*ON\b")
_RE_BOOTS_OFF = re.compile(r"([\d,]+)\s*OFF\b")
_RE_HEN = re.compile(r"(PS3HEN\s+[\d.]+)", re.IGNORECASE)
_RE_WEBMAN = re.compile(r"webMAN\s+([\w.]+)\s+MOD", re.IGNORECASE)
_RE_MAC = re.compile(
    r"MAC Addr\s*:\s*([0-9A-Fa-f:]{17})\s*-\s*([\d.]+)(?:\s+(WLAN|LAN|Ethernet))?",
    re.IGNORECASE,
)
# BD info line ends before the next HTML tag; flash type is on the Firmware line.
_RE_BD_DRIVE = re.compile(r"BD info:\s*(\S.*?)\s*<", re.IGNORECASE)
_RE_FLASH = re.compile(r"(NOR|NAND)\s+Firmware", re.IGNORECASE)
_RE_TITLEID = re.compile(r"/dev_hdd0/game/+([A-Z]{4}\d{5})/ICON0\.PNG", re.IGNORECASE)
_RE_APPVER = re.compile(r'search\?q=[^"]+\">[^<]*?(\d{2}\.\d{2})</a>')


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

    # Onda 1 extended fields
    if (m := _RE_FAN_MODE.search(text)) is not None:
        status.fan_mode = m.group(1)
    if (m := _RE_RUNTIME.search(text)) is not None:
        status.runtime = m.group(1)
    if (m := _RE_BOOTS_ON.search(text)) is not None:
        status.boots_on = int(m.group(1).replace(",", ""))
    if (m := _RE_BOOTS_OFF.search(text)) is not None:
        status.boots_off = int(m.group(1).replace(",", ""))
    if (m := _RE_HEN.search(text)) is not None:
        status.hen_version = m.group(1)
    if (m := _RE_WEBMAN.search(text)) is not None:
        status.webman_version = m.group(1)
    if (m := _RE_MAC.search(text)) is not None:
        status.mac_address = m.group(1)
        status.ip_address = m.group(2)
        status.connection = m.group(3)
    if (m := _RE_BD_DRIVE.search(text)) is not None:
        status.bd_drive = " ".join(m.group(1).split())
    if (m := _RE_FLASH.search(text)) is not None:
        status.flash_type = m.group(1).upper()
    if (m := _RE_TITLEID.search(text)) is not None:
        status.game_title_id = m.group(1)
    if (m := _RE_APPVER.search(text)) is not None:
        status.game_app_version = m.group(1)
    # Derive game_bg_url from game_icon_url (same dir, PIC1.PNG instead of ICON0.PNG)
    if status.game_icon_url is not None:
        status.game_bg_url = status.game_icon_url.replace("ICON0.PNG", "PIC1.PNG")

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

    async def async_get_ps3mapi(self, command: str):
        """GET /ps3mapi.ps3?<command>; return 'response' value or None on error/502."""
        import json  # noqa: PLC0415

        try:
            body = await self._get(f"/ps3mapi.ps3?{quote(command)}")
        except PS3ConnectionError:
            return None
        try:
            data = json.loads(body)
        except ValueError:
            return None
        if isinstance(data, dict) and "response" in data:
            return data["response"]
        return None

    async def async_get_status(self) -> PS3Status:
        """Fetch and parse /cpursx.ps3."""
        status = parse_cpursx(await self._get(CMD_STATUS))
        if status.game_icon_url and status.game_icon_url.startswith("/"):
            status.game_icon_url = f"{self._base}{status.game_icon_url}"
        if status.game_bg_url and status.game_bg_url.startswith("/"):
            status.game_bg_url = f"{self._base}{status.game_bg_url}"
        # Enrich console_type + cobra from ps3mapi (tolerant to failure).
        value = await self.async_get_ps3mapi("PS3 GETFWTYPE")
        if isinstance(value, str):
            status.console_type = value
            status.cobra = "COBRA" in value.upper()
        return status

    async def async_command(self, path: str) -> None:
        """Fire a webMAN web command (fire-and-forget GET)."""
        await self._get(path)
