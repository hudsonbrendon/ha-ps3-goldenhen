"""Sensor entities for PS3 GoldenHEN."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import PS3Status
from .const import DOMAIN
from .entity import PS3Entity


@dataclass(frozen=True, kw_only=True)
class PS3SensorDescription(SensorEntityDescription):
    """Describes a PS3 sensor and how to read it from PS3Status."""

    value_fn: Callable[[PS3Status], float | int | str | None]


SENSORS: tuple[PS3SensorDescription, ...] = (
    PS3SensorDescription(
        key="cpu_temp",
        translation_key="cpu_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.cpu_temp,
    ),
    PS3SensorDescription(
        key="rsx_temp",
        translation_key="rsx_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.rsx_temp,
    ),
    PS3SensorDescription(
        key="fan_speed",
        translation_key="fan_speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fan",
        value_fn=lambda s: s.fan_speed,
    ),
    PS3SensorDescription(
        key="free_memory",
        translation_key="free_memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.free_memory,
    ),
    PS3SensorDescription(
        key="hdd_free",
        translation_key="hdd_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:harddisk",
        value_fn=lambda s: s.hdd_free,
    ),
    PS3SensorDescription(
        key="firmware",
        translation_key="firmware",
        icon="mdi:chip",
        value_fn=lambda s: s.firmware,
    ),
    PS3SensorDescription(
        key="game_title",
        translation_key="game_title",
        icon="mdi:gamepad-variant",
        value_fn=lambda s: s.game_title,
    ),
    # --- Onda 2 extended sensors ---
    PS3SensorDescription(
        key="runtime",
        translation_key="runtime",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.runtime,
    ),
    PS3SensorDescription(
        key="boots_on",
        translation_key="boots_on",
        icon="mdi:power",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.boots_on,
    ),
    PS3SensorDescription(
        key="fan_mode",
        translation_key="fan_mode",
        icon="mdi:fan",
        value_fn=lambda s: s.fan_mode,
    ),
    PS3SensorDescription(
        key="console_type",
        translation_key="console_type",
        icon="mdi:console",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.console_type,
    ),
    PS3SensorDescription(
        key="hen_version",
        translation_key="hen_version",
        icon="mdi:flash",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.hen_version,
    ),
    PS3SensorDescription(
        key="webman_version",
        translation_key="webman_version",
        icon="mdi:web",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.webman_version,
    ),
    PS3SensorDescription(
        key="connection",
        translation_key="connection",
        icon="mdi:lan",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.connection,
    ),
    PS3SensorDescription(
        key="mac_address",
        translation_key="mac_address",
        icon="mdi:network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.mac_address,
    ),
    PS3SensorDescription(
        key="bd_drive",
        translation_key="bd_drive",
        icon="mdi:disc-player",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.bd_drive,
    ),
    PS3SensorDescription(
        key="flash_type",
        translation_key="flash_type",
        icon="mdi:memory",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.flash_type,
    ),
    PS3SensorDescription(
        key="game_title_id",
        translation_key="game_title_id",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.game_title_id,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PS3Sensor(coordinator, entry, description) for description in SENSORS
    )


class PS3Sensor(PS3Entity, SensorEntity):
    """A single PS3 metric."""

    entity_description: PS3SensorDescription

    def __init__(self, coordinator, entry, description: PS3SensorDescription) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)
