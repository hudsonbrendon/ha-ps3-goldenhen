"""Tests for the diagnostics module."""
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import DOMAIN
from custom_components.ps3_goldenhen.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def _setup(hass, status: PS3Status) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="PS3",
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 80},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.ps3_goldenhen.WebManClient.async_get_status",
        return_value=status,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


@pytest.mark.asyncio
async def test_diagnostics_redacts_sensitive_fields(hass):
    """mac_address and ip_address are redacted; firmware is present."""
    status = PS3Status(
        online=True,
        firmware="4.91 CEX PS3HEN 3.3.0",
        mac_address="28:0D:FC:73:D0:A2",
        ip_address="192.168.31.88",
        console_type="CEX COBRA",
    )
    entry = await _setup(hass, status)
    result = await async_get_config_entry_diagnostics(hass, entry)

    # Sensitive fields must be redacted in the status section
    assert result["status"]["mac_address"] == "**REDACTED**"
    assert result["status"]["ip_address"] == "**REDACTED**"

    # Non-sensitive field must be present and intact
    assert result["status"]["firmware"] == "4.91 CEX PS3HEN 3.3.0"

    # entry_data host must also be redacted
    assert result["entry_data"][CONF_HOST] == "**REDACTED**"


@pytest.mark.asyncio
async def test_diagnostics_offline_ps3(hass):
    """Diagnostics works when the PS3 is offline (coordinator.data still set)."""
    status = PS3Status(online=False)
    entry = await _setup(hass, status)
    result = await async_get_config_entry_diagnostics(hass, entry)

    assert "status" in result
    assert result["status"]["online"] is False
