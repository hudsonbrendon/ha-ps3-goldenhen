"""Select entity (fan mode) for PS3 GoldenHEN."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_FAN_AUTO, CMD_FAN_MANUAL, DOMAIN
from .entity import PS3Entity

_FAN_MODE_OPTIONS = ["Dynamic", "Manual"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PS3FanModeSelect(coordinator, entry)])


class PS3FanModeSelect(PS3Entity, SelectEntity):
    """Select the PS3 fan control mode (Dynamic / Manual)."""

    _attr_translation_key = "fan_mode_select"
    _attr_icon = "mdi:fan"
    _attr_options = _FAN_MODE_OPTIONS

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_fan_mode_select"

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        fan_mode = data.fan_mode
        if fan_mode == "Manual":
            return "Manual"
        if fan_mode:
            return "Dynamic"
        return None

    async def async_select_option(self, option: str) -> None:
        if option == "Manual":
            await self.coordinator.client.async_command(CMD_FAN_MANUAL)
        else:
            await self.coordinator.client.async_command(CMD_FAN_AUTO)
