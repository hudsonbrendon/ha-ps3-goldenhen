"""Tests for the config flow."""
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ps3_goldenhen.api import PS3ConnectionError, PS3Status
from custom_components.ps3_goldenhen.const import DOMAIN


@pytest.mark.asyncio
async def test_user_flow_success(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.ps3_goldenhen.config_flow.WebManClient.async_get_status",
        return_value=PS3Status(online=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_NAME: "PS3 Sala", CONF_HOST: "1.2.3.4", CONF_PORT: 80},
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "PS3 Sala"
    assert result["data"][CONF_HOST] == "1.2.3.4"


@pytest.mark.asyncio
async def test_user_flow_cannot_connect(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    with patch(
        "custom_components.ps3_goldenhen.config_flow.WebManClient.async_get_status",
        side_effect=PS3ConnectionError("down"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_NAME: "PS3 Sala", CONF_HOST: "1.2.3.4", CONF_PORT: 80},
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
