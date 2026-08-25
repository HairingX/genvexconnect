"""NilanConnect base entity class"""

import logging
from typing import Any, Dict, TypeVar, Generic

from nilan_proxy import NilanProxy, NilanProxyDatapointKey, NilanProxySetpointKey, NilanProxyUnits # type: ignore
from homeassistant.helpers.entity import Entity
from homeassistant.const import UnitOfTime,UnitOfTemperature,PERCENTAGE,CONCENTRATION_PARTS_PER_MILLION,REVOLUTIONS_PER_MINUTE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

VALUE_KEY_TYPE = TypeVar("VALUE_KEY_TYPE", NilanProxyDatapointKey, NilanProxySetpointKey, None)
T = TypeVar("T")

class NilanConnectEntityBase(Generic[VALUE_KEY_TYPE], Entity):
    """Base for all NilanConnect entities"""

    _attr_has_entity_name = True
    _unit_of_measurement:str|None
    _value_key:  VALUE_KEY_TYPE
    proxy: NilanProxy
    
    def __init__(
        self,
        proxy: NilanProxy,
        name: str,
        value_key: VALUE_KEY_TYPE,
        use_default_update_handler: bool = True,
        default_enabled:bool|None = None, 
        default_visible:bool|None = None
    ) -> None:
        if default_enabled is not None: self._attr_entity_registry_enabled_default = default_enabled
        if default_visible is not None: self._attr_entity_registry_visible_default = default_visible
        self.proxy = proxy
        self._attr_translation_key = name
        self._attr_unique_id = f"{proxy.get_device_id()}_{self._attr_translation_key.split("__")[0]}"
        self._attr_should_poll = False #set to False, we push changes to HA.
        self._value_key = value_key
        self._unit_of_measurement = NilanProxyUnits.UNDEFINED
        self._use_default_update_handler = use_default_update_handler
        if value_key is not None:
            self._unit_of_measurement = proxy.get_unit_of_measure(value_key)
            self.set_unit_of_measurement(self._unit_of_measurement)
        
    async def async_added_to_hass(self) -> None:
        # Registered for every entity, also the ones that do not track a value, so a
        # button on a device that stopped answering is not presented as usable.
        self.proxy.register_connection_state_handler(self._on_connection_state_change)
        if self._use_default_update_handler and self._value_key is not None:
            self.proxy.register_update_handler(self._value_key, self._on_change)
    
    async def async_will_remove_from_hass(self) -> None:
        self.proxy.deregister_connection_state_handler(self._on_connection_state_change)
        if self._use_default_update_handler and self._value_key is not None:
            self.proxy.deregister_update_handler(self._value_key, self._on_change)

    @property
    def available(self) -> bool:
        """Report unavailable once the device stops answering.

        Without this the last known reading stays on screen looking current, which is
        worse than showing nothing. A point the device does answer for but has no value
        for still reports None, which Home Assistant shows as unknown.
        """
        return self.proxy.is_available()

    def set_unit_of_measurement(self, uom:str|None):
        # self._attr_unit_of_measurement = self.parseUnitOfMeasure(uom)
        return
        
    def parse_unit_of_measure(self, uom:str|None, default:T = None) -> str|T:
        match uom:
            case NilanProxyUnits.SECONDS:     return UnitOfTime.SECONDS
            case NilanProxyUnits.MINUTES:     return UnitOfTime.MINUTES
            case NilanProxyUnits.HOURS:     return UnitOfTime.HOURS
            case NilanProxyUnits.DAYS:     return UnitOfTime.DAYS
            case NilanProxyUnits.MONTHS:   return UnitOfTime.MONTHS
            case NilanProxyUnits.YEARS:    return UnitOfTime.YEARS
            case NilanProxyUnits.CELSIUS:  return UnitOfTemperature.CELSIUS
            case NilanProxyUnits.PCT:      return PERCENTAGE
            case NilanProxyUnits.PPM:      return CONCENTRATION_PARTS_PER_MILLION
            case NilanProxyUnits.RPM:      return REVOLUTIONS_PER_MINUTE
            case _:
                return default
    
    def _on_change(self, old_value:int|float|None, new_value:int|float|None):
        """Notify HA of changes"""
        if self.hass is None: return # type: ignore
        _LOGGER.debug(f"Value Update: {self._attr_translation_key}: {old_value} -> {new_value}")
        self.schedule_update_ha_state(force_refresh=True)

    def _on_connection_state_change(self, available:bool):
        """Push the availability change so HA rereads it.

        HA only reads the available property when state is written, and a device that
        went away sends nothing, so without this push the entity would keep its last
        state forever. Called from the proxy receive thread, which is fine here:
        schedule_update_ha_state hands the write back to the event loop.
        """
        if self.hass is None: return # type: ignore
        _LOGGER.debug(f"Availability Update: {self._attr_translation_key}: {available}")
        self.schedule_update_ha_state()

    @property
    def device_info(self): # type: ignore
        info: Dict[str, Any] = {
            "identifiers": {(DOMAIN, self.proxy.get_device_id())},
            "name": self.proxy.get_device_id(),
            "manufacturer": self.proxy.get_device_manufacturer(),
            "model": self.proxy.get_loaded_model_name(),
            "hw_version": f"M: {self.proxy.get_device_model()}, SD: {self.proxy.get_slave_device_number()}, SDM: {self.proxy.get_slave_device_model()}",
        }
        return info
