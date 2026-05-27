"""Image entity (current game cover) for PS3 GoldenHEN."""
from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import PS3Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PS3GameCover(hass, coordinator, entry)])


class PS3GameCover(PS3Entity, ImageEntity):
    """Cover art (ICON0.PNG) of the running game, when available."""

    _attr_translation_key = "game_cover"

    def __init__(self, hass: HomeAssistant, coordinator, entry) -> None:
        PS3Entity.__init__(self, coordinator, entry)
        ImageEntity.__init__(self, hass)
        self._attr_unique_id = f"{entry.entry_id}_game_cover"
        self._current_url: str | None = None

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        return bool(data and data.online and data.game_icon_url)

    def _handle_coordinator_update(self) -> None:
        url = self.coordinator.data.game_icon_url if self.coordinator.data else None
        if url != self._current_url:
            self._current_url = url
            self._attr_image_url = url
            self._attr_image_last_updated = dt_util.utcnow()
        super()._handle_coordinator_update()
