"""DataUpdateCoordinator for the PS3 GoldenHEN integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import PS3ConnectionError, PS3Status, WebManClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PS3DataUpdateCoordinator(DataUpdateCoordinator[PS3Status]):
    """Polls webMAN MOD and exposes a PS3Status to entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WebManClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> PS3Status:
        """Fetch status; a console offline não é erro fatal."""
        try:
            return await self.client.async_get_status()
        except PS3ConnectionError as err:
            _LOGGER.debug("PS3 unreachable: %s", err)
            return PS3Status(online=False)
