"""Diagnostics support for PS3 GoldenHEN."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {"mac_address", "ip_address", "host", "raw"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = asdict(coordinator.data) if coordinator.data else {}
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "status": async_redact_data(data, TO_REDACT),
    }
