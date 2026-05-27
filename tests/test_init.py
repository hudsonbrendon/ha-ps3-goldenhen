"""Tests for setup and unload of the config entry."""
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ps3_goldenhen.api import PS3Status
from custom_components.ps3_goldenhen.const import DOMAIN


@pytest.mark.asyncio
async def test_setup_and_unload(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="PlayStation 3",
        data={CONF_HOST: "1.2.3.4", CONF_PORT: 80},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ps3_goldenhen.WebManClient.async_get_status",
        return_value=PS3Status(online=True, cpu_temp=60.0, firmware="4.91"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.entry_id in hass.data[DOMAIN]

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.entry_id not in hass.data[DOMAIN]
