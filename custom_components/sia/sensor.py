from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.typing import StateType


from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from homeassistant.const import EntityCategory
from .sia_entity_base import SIABaseEntity, SIAEntityDescription
from .const import CONF_ACCOUNT, CONF_ACCOUNTS, CONF_ZONES
import logging
import re
from typing import Iterable

_LOGGER = logging.getLogger(__name__)

SIGNAL_SIA_UPDATE = "sia_update_signal"

ENTITY_DESCRIPTION_LOG = SIAEntityDescription(
    key="log",
    device_class = None,
    code_consequences={},
)

class SIATextLog(SIABaseEntity):
    """SIA Log Entity voor tekstgebaseerde logs."""

    @property
    def state(self):
        """Laat de nieuwste logregel zien."""
        return self._attr_state if self._attr_state else "Geen logs"


    def update_state(self, sia_event) -> bool:
        """Werk de status van de entiteit bij en log het evenement."""

        _LOGGER.debug(f"Ontvangen SIA evenement: {sia_event.sia_code}")
        # Controleer of de code een beschrijving heeft
        if sia_event.sia_code.code == "RP":
            return False

        # Bouw het logbericht
        add_message = ""
        if sia_event.message:

            actor = f" ({match.group(1)})" if (match := re.search(r"'([^']*)'", sia_event.message)) and match.group(1) else ""
            what = (match := re.match(r"(\w+)", sia_event.sia_code.concerns)) and sia_event.sia_code.concerns != "Unused" and match.group(1) or ""

            add_message= f" ({what}: {actor.strip()})" if actor and what else actor

        log_entry = f"{sia_event.code} - { sia_event.sia_code.description}{add_message}"
        self._attr_extra_state_attributes = {}
        self._attr_state = log_entry
        # Log het bericht en schrijf de status weg
        self.async_write_ha_state()

        # Altijd True retourneren, omdat alle logs relevant zijn
        return False

    def handle_last_state(self, last_state: State | None) -> None:
        """Handle the last state."""
        if last_state is not None:
            self._attr_state = last_state.state

async def generate_text_logs(hass, entry: ConfigEntry) -> Iterable[SIATextLog]:
    """Genereer log-entiteiten voor elk account en zone."""
    entities = []

    # Doorloop alle accounts in de configuratie
    for account_data in entry.data[CONF_ACCOUNTS]:
        account = account_data[CONF_ACCOUNT]

        # Haal zones op uit opties
        zones = entry.options[CONF_ACCOUNTS][account][CONF_ZONES]

        # Voeg een log-entiteit toe voor de hoofdzone (0)
        entities.append(
            SIATextLog(
                entry=entry,
                account=account,
                zone=0,
                entity_description=ENTITY_DESCRIPTION_LOG,
            )
        )

        # Voeg een log-entiteit toe voor elke zone
        i = 0
        while i < zones:
            entities.append(
            SIATextLog(
                entry=entry,
                account=account,
                zone=i+1,
                entity_description=ENTITY_DESCRIPTION_LOG,
            )
        )
            i += 1

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SIA log sensors from a config entry."""
    async_add_entities(await generate_text_logs(hass, entry))
