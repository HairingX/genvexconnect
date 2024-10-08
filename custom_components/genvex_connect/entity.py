"""GenvexConnect base entity class"""

import logging
from typing import Any, Dict, TypeVar, Generic

from genvexnabto import GenvexNabto, GenvexNabtoDatapointKey, GenvexNabtoSetpointKey, GenvexNabtoUnits # type: ignore
from homeassistant.helpers.entity import Entity
from homeassistant.const import UnitOfTime,UnitOfTemperature,PERCENTAGE,CONCENTRATION_PARTS_PER_MILLION,REVOLUTIONS_PER_MINUTE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

VALUE_KEY_TYPE = TypeVar("VALUE_KEY_TYPE", GenvexNabtoDatapointKey, GenvexNabtoSetpointKey, None)
T = TypeVar("T")

class GenvexConnectEntityBase(Generic[VALUE_KEY_TYPE], Entity):
    """Base for all GenvexConnect entities"""

    _attr_has_entity_name = True
    _unit_of_measurement:str|None
    _value_key:  VALUE_KEY_TYPE
    _genvex_nabto: GenvexNabto
    
    def __init__(
        self,
        genvex_nabto: GenvexNabto,
        name: str,
        value_key: VALUE_KEY_TYPE,
        use_default_update_handler: bool = True,
        default_enabled:bool|None = None, 
        default_visible:bool|None = None
    ) -> None:
        if default_enabled is not None: self._attr_entity_registry_enabled_default = default_enabled
        if default_visible is not None: self._attr_entity_registry_visible_default = default_visible
        self._genvex_nabto = genvex_nabto
        self._attr_translation_key = name
        self._attr_unique_id = f"{genvex_nabto.get_device_id()}_{self._attr_translation_key.split("__")[0]}"
        self._attr_should_poll = False #set to False, we push changes to HA.
        self._value_key = value_key
        self._unit_of_measurement = GenvexNabtoUnits.UNDEFINED
        self._use_default_update_handler = use_default_update_handler
        if value_key is not None:
            self._unit_of_measurement = genvex_nabto.get_unit_of_measure(value_key)
            self.set_unit_of_measurement(self._unit_of_measurement)
        
    async def async_added_to_hass(self) -> None:
        if self._use_default_update_handler and self._value_key is not None:
            self._genvex_nabto.register_update_handler(self._value_key, self._on_change)
    
    async def async_will_remove_from_hass(self) -> None:
        if self._use_default_update_handler and self._value_key is not None:
            self._genvex_nabto.deregister_update_handler(self._value_key, self._on_change)

    def set_unit_of_measurement(self, uom:str|None):
        # self._attr_unit_of_measurement = self.parseUnitOfMeasure(uom)
        return
        
    def parse_unit_of_measure(self, uom:str|None, default:T = None) -> str|T:
        match uom:
            case GenvexNabtoUnits.SECONDS:     return UnitOfTime.SECONDS
            case GenvexNabtoUnits.MINUTES:     return UnitOfTime.MINUTES
            case GenvexNabtoUnits.HOURS:     return UnitOfTime.HOURS
            case GenvexNabtoUnits.DAYS:     return UnitOfTime.DAYS
            case GenvexNabtoUnits.MONTHS:   return UnitOfTime.MONTHS
            case GenvexNabtoUnits.YEARS:    return UnitOfTime.YEARS
            case GenvexNabtoUnits.CELSIUS:  return UnitOfTemperature.CELSIUS
            case GenvexNabtoUnits.PCT:      return PERCENTAGE
            case GenvexNabtoUnits.PPM:      return CONCENTRATION_PARTS_PER_MILLION
            case GenvexNabtoUnits.RPM:      return REVOLUTIONS_PER_MINUTE
            case _:
                return default
    
    def _on_change(self, old_value:int|float|None, new_value:int|float|None):
        """Notify HA of changes"""
        if self.hass is None: return # type: ignore
        _LOGGER.debug(f"Value Update: {self._attr_translation_key}: {old_value} -> {new_value}")
        self.schedule_update_ha_state(force_refresh=True)

    @property
    def device_info(self): # type: ignore
        info: Dict[str, Any] = {
            "identifiers": {(DOMAIN, self._genvex_nabto.get_device_id())},
            "name": self._genvex_nabto.get_device_id(),
            "manufacturer": self._genvex_nabto.get_device_manufacturer(),
            "model": self._genvex_nabto.get_loaded_model_name(),
            "hw_version": f"M: {self._genvex_nabto.get_device_model()}, SD: {self._genvex_nabto.get_slave_device_number()}, SDM: {self._genvex_nabto.get_slave_device_model()}",
        }
        return info
