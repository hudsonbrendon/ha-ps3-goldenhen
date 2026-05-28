"""Fan-mode switch (optimistic + coordinator sync) for PS3 GoldenHEN."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_FAN_AUTO, CMD_FAN_MANUAL, DOMAIN
from .entity import PS3Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PS3FanModeSwitch(coordinator, entry)])


class PS3FanModeSwitch(PS3Entity, SwitchEntity):
    """ON = fan automático (dinâmico); OFF = fan manual.

    Optimistic on action; syncs real state from coordinator polls.
    """

    _attr_translation_key = "fan_auto"
    _attr_icon = "mdi:fan-auto"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_fan_auto"
        self._attr_is_on = True  # webMAN inicia em modo dinâmico por padrão

    def _handle_coordinator_update(self) -> None:
        """Sync is_on from the latest poll result, then notify HA."""
        data = self.coordinator.data
        if data is not None:
            fan_mode = data.fan_mode
            if fan_mode is not None:
                # "Manual" → OFF (fan controlled manually); anything else → ON (auto)
                self._attr_is_on = fan_mode != "Manual"
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_command(CMD_FAN_AUTO)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_command(CMD_FAN_MANUAL)
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)
