"""Button entities (power and disc) for PS3 GoldenHEN."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_BEEP,
    CMD_EJECT,
    CMD_FAN_DOWN,
    CMD_FAN_UP,
    CMD_HARD_REBOOT,
    CMD_INSERT,
    CMD_QUICK_REBOOT,
    CMD_REFRESH,
    CMD_RESTART,
    CMD_SHUTDOWN,
    CMD_SOFT_REBOOT,
    CMD_UNMOUNT,
    DOMAIN,
)
from .entity import PS3Entity


@dataclass(frozen=True, kw_only=True)
class PS3ButtonDescription(ButtonEntityDescription):
    """Button + webMAN command to fire."""

    command: str


BUTTONS: tuple[PS3ButtonDescription, ...] = (
    PS3ButtonDescription(
        key="restart", translation_key="restart",
        icon="mdi:restart", command=CMD_RESTART,
    ),
    PS3ButtonDescription(
        key="soft_reboot", translation_key="soft_reboot",
        icon="mdi:restart", command=CMD_SOFT_REBOOT,
    ),
    PS3ButtonDescription(
        key="hard_reboot", translation_key="hard_reboot",
        icon="mdi:restart-alert", command=CMD_HARD_REBOOT,
    ),
    PS3ButtonDescription(
        key="shutdown", translation_key="shutdown",
        icon="mdi:power", command=CMD_SHUTDOWN,
    ),
    PS3ButtonDescription(
        key="eject", translation_key="eject",
        icon="mdi:eject", command=CMD_EJECT,
    ),
    PS3ButtonDescription(
        key="insert", translation_key="insert",
        icon="mdi:disc", command=CMD_INSERT,
    ),
    PS3ButtonDescription(
        key="quick_reboot", translation_key="quick_reboot",
        icon="mdi:restart", command=CMD_QUICK_REBOOT,
    ),
    PS3ButtonDescription(
        key="fan_up", translation_key="fan_up",
        icon="mdi:fan-plus", command=CMD_FAN_UP,
    ),
    PS3ButtonDescription(
        key="fan_down", translation_key="fan_down",
        icon="mdi:fan-minus", command=CMD_FAN_DOWN,
    ),
    PS3ButtonDescription(
        key="refresh_games", translation_key="refresh_games",
        icon="mdi:refresh", command=CMD_REFRESH,
    ),
    PS3ButtonDescription(
        key="unmount", translation_key="unmount",
        icon="mdi:eject-outline", command=CMD_UNMOUNT,
    ),
    PS3ButtonDescription(
        key="beep1", translation_key="beep1",
        icon="mdi:bullhorn", command=CMD_BEEP.format(n=1),
    ),
    PS3ButtonDescription(
        key="beep2", translation_key="beep2",
        icon="mdi:bullhorn", command=CMD_BEEP.format(n=2),
    ),
    PS3ButtonDescription(
        key="beep3", translation_key="beep3",
        icon="mdi:bullhorn", command=CMD_BEEP.format(n=3),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PS3Button(coordinator, entry, description) for description in BUTTONS
    )


class PS3Button(PS3Entity, ButtonEntity):
    """Fires a webMAN web command on press."""

    entity_description: PS3ButtonDescription

    def __init__(self, coordinator, entry, description: PS3ButtonDescription) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    async def async_press(self) -> None:
        await self.coordinator.client.async_command(self.entity_description.command)
