"""Platform for sensor integration."""

import logging
from homeassistant.helpers.entity import Entity
from homeassistant.components.select import SelectEntity
from genvexnabto import GenvexNabto, GenvexNabtoDatapointKey, GenvexNabtoSetpointKey
from .entity import GenvexConnectEntityBase

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    genvexNabto: GenvexNabto = hass.data[DOMAIN][config_entry.entry_id]

    new_entities = []

    if genvexNabto.provides_value(GenvexNabtoSetpointKey.FAN_LEVEL):
        new_entities.append(GenvexConnectSelect(genvexNabto, GenvexNabtoSetpointKey.FAN_LEVEL, "mdi:fan"))
        
    if genvexNabto.provides_value(GenvexNabtoSetpointKey.COMPRESSOR_PRIORITY):
        new_entities.append(GenvexConnectSelect(genvexNabto, GenvexNabtoSetpointKey.COMPRESSOR_PRIORITY, "mdi:priority-high"))
    if genvexNabto.provides_value(GenvexNabtoSetpointKey.TEMP_COOLING_START_OFFSET):
        new_entities.append(GenvexConnectSelect(genvexNabto, GenvexNabtoSetpointKey.TEMP_COOLING_START_OFFSET, "mdi:snowflake-thermometer"))
    if genvexNabto.provides_value(GenvexNabtoSetpointKey.ANTILEGIONELLA_DAY):
        new_entities.append(GenvexConnectSelect(genvexNabto, GenvexNabtoSetpointKey.ANTILEGIONELLA_DAY, "mdi:bacteria"))

    async_add_entities(new_entities)


class GenvexConnectSelect(GenvexConnectEntityBase, SelectEntity):
    def __init__(self, genvexNabto: GenvexNabto, valueKey: GenvexNabtoSetpointKey, icon: str):
        super().__init__(genvexNabto, valueKey.value, valueKey)
        self._min = int(genvexNabto.get_setpoint_min_value(valueKey))
        self._max = int(genvexNabto.get_setpoint_max_value(valueKey))
        self._attr_icon = icon
        if self._min > self._max:
            self._attr_options = []
        else:
            self._attr_options = list(map(str, range(self._min, self._max + 1)))

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        if self._value_key is None: return None
        val = self.genvex_nabto.get_value(self._value_key)
        if val is None: return None
        currentFanLevel = str(int(val))
        if currentFanLevel not in self._attr_options: return None
        return currentFanLevel

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # if option not in self._attr_options:
        #     _LOGGER.info(f"Wanted to set {self._valueKey} to {option}, but failed as it is invalid")
        #     return
        if self._value_key is GenvexNabtoSetpointKey:
            value = int(option)
            self.genvex_nabto.set_setpoint(self._value_key, value)