"""The PS3 GoldenHEN integration."""
from __future__ import annotations

from urllib.parse import quote

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WebManClient
from .const import (
    CMD_BEEP,
    CMD_FAN_SPEED,
    CMD_FAN_TARGET,
    CMD_PLAY,
    CMD_POPUP,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import PS3DataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.IMAGE,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

ATTR_ENTRY_ID = "entry_id"

SERVICE_NOTIFY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("icon"): vol.All(int, vol.Range(min=0, max=50)),
        vol.Optional("sound"): vol.All(int, vol.Range(min=0, max=9)),
    }
)
SERVICE_BUZZER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Optional("pattern", default=1): vol.All(int, vol.Range(min=0, max=9)),
    }
)
SERVICE_LAUNCH_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTRY_ID): cv.string, vol.Required("path"): cv.string}
)
SERVICE_FAN_SPEED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required("speed"): vol.All(int, vol.Range(min=0, max=100)),
    }
)
SERVICE_LED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required("color"): vol.All(int, vol.Range(min=0, max=255)),
        vol.Required("mode"): vol.All(int, vol.Range(min=0, max=255)),
    }
)
SERVICE_MOUNT_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTRY_ID): cv.string, vol.Required("path"): cv.string}
)
SERVICE_FAN_TARGET_TEMP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required("temperature"): vol.All(int, vol.Range(min=40, max=80)),
    }
)
SERVICE_SEND_COMMAND_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTRY_ID): cv.string, vol.Required("command"): cv.string}
)
SERVICE_READ_MEMORY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required("pid"): cv.string,
        vol.Required("address"): cv.string,
        vol.Required("size"): int,
    }
)
SERVICE_WRITE_MEMORY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required("pid"): cv.string,
        vol.Required("address"): cv.string,
        vol.Required("data"): cv.string,
    }
)


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "notify"):
        return

    def _coordinator(call: ServiceCall):
        entry_id = call.data[ATTR_ENTRY_ID]
        if entry_id not in hass.data.get(DOMAIN, {}):
            raise ServiceValidationError(f"PS3 config entry '{entry_id}' not found")
        return hass.data[DOMAIN][entry_id]

    async def _notify(call: ServiceCall) -> None:
        coord = _coordinator(call)
        message = call.data["message"]
        icon = call.data.get("icon")
        sound = call.data.get("sound")
        if icon is not None or sound is not None:
            params = f"?{quote(message)}"
            if icon is not None:
                params += f"&icon={icon}"
            if sound is not None:
                params += f"&snd={sound}"
            await coord.client.async_command(f"{CMD_POPUP}{params}")
        else:
            await coord.client.async_command(f"{CMD_POPUP}/{quote(message)}")

    async def _buzzer(call: ServiceCall) -> None:
        coord = _coordinator(call)
        await coord.client.async_command(CMD_BEEP.format(n=call.data["pattern"]))

    async def _launch(call: ServiceCall) -> None:
        coord = _coordinator(call)
        path = quote(call.data["path"], safe="/")
        await coord.client.async_command(f"{CMD_PLAY}{path}")

    async def _set_fan(call: ServiceCall) -> None:
        coord = _coordinator(call)
        await coord.client.async_command(
            CMD_FAN_SPEED.format(speed=call.data["speed"])
        )

    async def _led(call: ServiceCall) -> None:
        coord = _coordinator(call)
        color = call.data["color"]
        mode = call.data["mode"]
        await coord.client.async_command(
            "/ps3mapi.ps3?" + quote(f"PS3 LED {color} {mode}")
        )

    async def _mount(call: ServiceCall) -> None:
        coord = _coordinator(call)
        path = call.data["path"]
        await coord.client.async_command(f"/mount.ps3{quote(path, safe='/')}")

    async def _set_fan_target_temp(call: ServiceCall) -> None:
        coord = _coordinator(call)
        await coord.client.async_command(
            CMD_FAN_TARGET.format(temp=int(call.data["temperature"]))
        )

    async def _send_command(call: ServiceCall) -> None:
        coord = _coordinator(call)
        command = call.data["command"]
        if not command.startswith("/"):
            raise ServiceValidationError(
                "command must be a relative webMAN web command starting with '/' "
                "(e.g. /popup.ps3/hi)"
            )
        await coord.client.async_command(command)

    async def _read_memory(call: ServiceCall) -> dict:
        coord = _coordinator(call)
        pid = call.data["pid"]
        address = call.data["address"]
        size = call.data["size"]
        result = await coord.client.async_get_ps3mapi(
            f"MEMORY GET {pid} {address} {size}"
        )
        if result is None:
            raise ServiceValidationError(
                "read_memory failed: the PS3 is unreachable or ps3mapi returned "
                "an error (check pid/address/size)"
            )
        return {"data": result}

    async def _write_memory(call: ServiceCall) -> None:
        coord = _coordinator(call)
        pid = call.data["pid"]
        address = call.data["address"]
        data = call.data["data"]
        await coord.client.async_command(
            "/ps3mapi.ps3?" + quote(f"MEMORY SET {pid} {address} {data}")
        )

    hass.services.async_register(DOMAIN, "notify", _notify, SERVICE_NOTIFY_SCHEMA)
    hass.services.async_register(DOMAIN, "buzzer", _buzzer, SERVICE_BUZZER_SCHEMA)
    hass.services.async_register(DOMAIN, "launch_game", _launch, SERVICE_LAUNCH_SCHEMA)
    hass.services.async_register(
        DOMAIN, "set_fan_speed", _set_fan, SERVICE_FAN_SPEED_SCHEMA
    )
    hass.services.async_register(DOMAIN, "led", _led, SERVICE_LED_SCHEMA)
    hass.services.async_register(DOMAIN, "mount", _mount, SERVICE_MOUNT_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        "set_fan_target_temp",
        _set_fan_target_temp,
        SERVICE_FAN_TARGET_TEMP_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, "send_command", _send_command, SERVICE_SEND_COMMAND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        "read_memory",
        _read_memory,
        SERVICE_READ_MEMORY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "write_memory", _write_memory, SERVICE_WRITE_MEMORY_SCHEMA
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PS3 GoldenHEN from a config entry."""
    session = async_get_clientsession(hass)
    client = WebManClient(
        session,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = PS3DataUpdateCoordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_refresh_games()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
