"""Module for SIA Alarm Control Panels."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from pysiaalarm import SIAEvent

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityDescription,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import CONF_ACCOUNT, CONF_ACCOUNTS, CONF_ZONES, KEY_ALARM, PREVIOUS_STATE
from .sia_entity_base import SIABaseEntity, SIAEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SIAAlarmControlPanelEntityDescription(
    AlarmControlPanelEntityDescription,
    SIAEntityDescription,
):
    """Describes SIA alarm control panel entity."""


ENTITY_DESCRIPTION_ALARM = SIAAlarmControlPanelEntityDescription(
    key=KEY_ALARM,
    code_consequences={
        "PA": AlarmControlPanelState.TRIGGERED,
        "JA": AlarmControlPanelState.TRIGGERED,
        "TA": AlarmControlPanelState.TRIGGERED,
        "BA": AlarmControlPanelState.TRIGGERED,
        "CA": AlarmControlPanelState.ARMED_AWAY,
        "CB": AlarmControlPanelState.ARMED_AWAY,
        "CG": AlarmControlPanelState.ARMED_HOME,
        "CL": AlarmControlPanelState.ARMED_AWAY,
        "CP": AlarmControlPanelState.ARMED_AWAY,
        "CQ": AlarmControlPanelState.ARMED_AWAY,
        "CS": AlarmControlPanelState.ARMED_AWAY,
        "CF": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
        "NP": AlarmControlPanelState.DISARMED,
        "NO": AlarmControlPanelState.DISARMED,
        "OA": AlarmControlPanelState.DISARMED,
        "OB": AlarmControlPanelState.DISARMED,
        "OG": AlarmControlPanelState.DISARMED,
        "OP": AlarmControlPanelState.DISARMED,
        "OQ": AlarmControlPanelState.DISARMED,
        "OR": AlarmControlPanelState.DISARMED,
        "OS": AlarmControlPanelState.DISARMED,
        "NL": AlarmControlPanelState.ARMED_NIGHT,
        "NE": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
        "NF": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
        "BR": PREVIOUS_STATE,
    },
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SIA alarm_control_panel(s) from a config entry."""
    async_add_entities(
        SIAAlarmControlPanel(
            entry, account_data[CONF_ACCOUNT], zone, ENTITY_DESCRIPTION_ALARM
        )
        for account_data in entry.data[CONF_ACCOUNTS]
        for zone in range(
            1,
            entry.options[CONF_ACCOUNTS][account_data[CONF_ACCOUNT]][CONF_ZONES] + 1,
        )
    )

class SIAAlarmControlPanel(SIABaseEntity, AlarmControlPanelEntity):
    """Class for SIA Alarm Control Panels."""

    entity_description: SIAAlarmControlPanelEntityDescription

    def __init__(
        self,
        entry: ConfigEntry,
        account: str,
        zone: int,
        entity_description: SIAAlarmControlPanelEntityDescription,
    ) -> None:
        """Create SIAAlarmControlPanel object."""
        super().__init__(
            entry,
            account,
            zone,
            entity_description,
        )

        self.alarm_state: AlarmControlPanelState | None = None
        self._old_state: AlarmControlPanelState | None = None

    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the alarm."""
        return self.alarm_state

    def handle_last_state(self, last_state: State | None) -> None:
        """Handle the last state."""
        if last_state is not None:
            self.alarm_state = last_state.state
        if self.state == STATE_UNAVAILABLE:
            self._attr_available = False

    def update_state(self, sia_event: SIAEvent) -> bool:
        """Update the state of the alarm control panel.

        Return True if the event was relevant for this entity.
        """
        new_state = None
        if sia_event.code:
            new_state = self.entity_description.code_consequences.get(sia_event.code)
        if new_state is None:
            return False
        _LOGGER.debug("New state will be %s (previous state: %s, current state: %s)", new_state, self._old_state, self.state)
        if new_state == PREVIOUS_STATE:
            if self._old_state != 'triggered':
                new_state = self._old_state
            else:
                new_state = self.state
        self.alarm_state, self._old_state = new_state, self.alarm_state
        return True
