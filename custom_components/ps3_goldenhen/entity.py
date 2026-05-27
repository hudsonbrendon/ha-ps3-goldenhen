"""Base entity for the PS3 GoldenHEN integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PS3DataUpdateCoordinator


class PS3Entity(CoordinatorEntity[PS3DataUpdateCoordinator]):
    """Common device info and coordinator wiring."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PS3DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Sony",
            model="PlayStation 3 (GoldenHEN + webMAN MOD)",
            configuration_url=coordinator.client.base_url,
            sw_version=coordinator.data.firmware if coordinator.data else None,
        )
