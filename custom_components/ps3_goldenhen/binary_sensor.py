"""Binary sensor (connectivity) for PS3 GoldenHEN."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import PS3Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PS3OnlineSensor(coordinator, entry),
        PS3GameRunningSensor(coordinator, entry),
        PS3CobraModeSensor(coordinator, entry),
    ])


class PS3OnlineSensor(PS3Entity, BinarySensorEntity):
    """Reports whether webMAN MOD is reachable."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "online"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_online"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)

    @property
    def available(self) -> bool:
        return True  # sempre disponível: é justamente o sensor de conectividade


class PS3GameRunningSensor(PS3Entity, BinarySensorEntity):
    """Reports whether a game is currently running on the PS3."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_translation_key = "game_running"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_game_running"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.game_title)

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)


class PS3CobraModeSensor(PS3Entity, BinarySensorEntity):
    """Reports whether the PS3 is running in COBRA mode."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:snake"
    _attr_translation_key = "cobra_mode"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cobra_mode"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.cobra)

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)
