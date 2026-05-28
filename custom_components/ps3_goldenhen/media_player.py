"""Media player entity for PS3 GoldenHEN."""
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_PLAY, CMD_SHUTDOWN, DOMAIN
from .entity import PS3Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PS3MediaPlayer(coordinator, entry)])


class PS3MediaPlayer(PS3Entity, MediaPlayerEntity):
    """Media player representing the PlayStation 3 console."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.SELECT_SOURCE | MediaPlayerEntityFeature.TURN_OFF
    )
    _attr_media_image_remotely_accessible = False

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_media_player"

    @property
    def state(self) -> MediaPlayerState:
        data = self.coordinator.data
        if data is None or not data.online:
            return MediaPlayerState.OFF
        if data.game_title:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        return data.game_title

    @property
    def media_content_type(self) -> MediaType:
        return MediaType.GAME

    @property
    def app_name(self) -> str:
        return "PlayStation 3"

    @property
    def media_image_url(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        return data.game_icon_url

    @property
    def source_list(self) -> list[str]:
        return [g["name"] for g in self.coordinator.games]

    @property
    def source(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        # Prefer matching the running game by its title ID (reliable), then fall
        # back to the display title. Either way the result is a name from the
        # games list (or None), never an out-of-list value.
        if data.game_title_id:
            for game in self.coordinator.games:
                if game["title_id"] == data.game_title_id:
                    return game["name"]
        if data.game_title and data.game_title in self.source_list:
            return data.game_title
        return None

    async def async_select_source(self, source: str) -> None:
        game = next(
            (g for g in self.coordinator.games if g["name"] == source), None
        )
        if game is None:
            return
        await self.coordinator.client.async_command(f"{CMD_PLAY}{game['path']}")

    async def async_turn_off(self) -> None:
        await self.coordinator.client.async_command(CMD_SHUTDOWN)
