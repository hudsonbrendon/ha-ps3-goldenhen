"""Number entities (fan speed and fan target temperature) for PS3 GoldenHEN."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import PS3Status
from .const import CMD_FAN_SPEED, CMD_FAN_TARGET, DOMAIN
from .entity import PS3Entity


@dataclass(frozen=True, kw_only=True)
class PS3NumberDescription(NumberEntityDescription):
    """Number entity description extended with command factory."""

    command_fn: Callable[[int], str]
    value_fn: Callable[[PS3Status], float | None]


NUMBERS: tuple[PS3NumberDescription, ...] = (
    PS3NumberDescription(
        key="fan_speed",
        translation_key="fan_speed",
        icon="mdi:fan",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: (
            float(data.fan_speed) if data.fan_speed is not None else None
        ),
        command_fn=lambda v: CMD_FAN_SPEED.format(speed=v),
    ),
    PS3NumberDescription(
        key="fan_target_temp",
        translation_key="fan_target_temp",
        icon="mdi:thermometer",
        native_min_value=40,
        native_max_value=80,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: None,  # write-only
        command_fn=lambda v: CMD_FAN_TARGET.format(temp=v),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PS3Number(coordinator, entry, description) for description in NUMBERS
    )


class PS3Number(PS3Entity, NumberEntity):
    """Numeric control for a PS3 fan parameter."""

    entity_description: PS3NumberDescription

    def __init__(self, coordinator, entry, description: PS3NumberDescription) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        command = self.entity_description.command_fn(int(value))
        await self.coordinator.client.async_command(command)
