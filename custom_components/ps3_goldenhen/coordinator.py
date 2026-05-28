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
        self._last_title_id: str | None = None
        self.games: list[dict] = []

    async def _async_update_data(self) -> PS3Status:
        """Fetch status; a console offline não é erro fatal."""
        try:
            data = await self.client.async_get_status()
        except PS3ConnectionError as err:
            _LOGGER.debug("PS3 unreachable: %s", err)
            return PS3Status(online=False)

        if data.online and data.game_title_id != self._last_title_id:
            self.hass.bus.async_fire(
                "ps3_goldenhen_event",
                {
                    "type": "game_changed",
                    "title_id": data.game_title_id,
                    "title": data.game_title,
                },
            )
            self._last_title_id = data.game_title_id

        return data

    async def async_refresh_games(self) -> None:
        """Refresh the installed games list (best-effort; errors are swallowed)."""
        try:
            self.games = await self.client.async_get_games()
        except PS3ConnectionError:
            pass
