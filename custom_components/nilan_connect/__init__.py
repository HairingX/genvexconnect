"""The Nilan Connect integration."""

from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed

from nilan_proxy import NilanProxy, NilanProxyConnectionErrorType # type: ignore

from custom_components.nilan_connect.data import NilanConnectHassData, get_hass_data, remove_hass_data, set_hass_data # type: ignore
from .const import DOMAIN, CONF_DEVICE_ID, CONF_AUTHORIZED_EMAIL, CONF_DEVICE_IP, CONF_DEVICE_PORT

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nilan Connect from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    authorized_email = str(entry.data.get(CONF_AUTHORIZED_EMAIL))
    proxy = NilanProxy(authorized_email)
    device_id = str(entry.data.get(CONF_DEVICE_ID))
    # Only stored when the device was set up manually. Pass them through untouched so
    # the proxy falls back to discovery when they are absent, which is what keeps a
    # changed dhcp lease from breaking the setup. Do not cast, str(None) would become
    # the literal "None" and end up being resolved as a hostname.
    device_ip = entry.data.get(CONF_DEVICE_IP)
    device_port = entry.data.get(CONF_DEVICE_PORT)
    proxy.set_device(device_id, device_ip, device_port)

    discoveryResult = await proxy.wait_for_discovery()
    if discoveryResult is False:  # Waits for NilanProxy to discover the current device IP
        raise ConfigEntryNotReady(f"Timed out while trying to discover {device_id}")
    proxy.connect_to_device()
    await proxy.wait_for_connection()
    _LOGGER.info(f"Controller model: {proxy.get_device_model()}")
    if proxy.get_connection_error() is not None:
        if proxy.get_connection_error() is NilanProxyConnectionErrorType.AUTHENTICATION_ERROR:
            raise ConfigEntryAuthFailed(f"Credentials expired for {device_id}")
        if proxy.get_connection_error() is NilanProxyConnectionErrorType.TIMEOUT:
            raise ConfigEntryNotReady(f"Timed out while trying to connect to {device_id}")
        if proxy.get_connection_error() is NilanProxyConnectionErrorType.UNSUPPORTED_MODEL:
            raise ConfigEntryNotReady(
                f"Timed out while trying to get data from {device_id} did not correctly load a model for Model no: {proxy.get_device_model()}, device number: {proxy.get_device_number()} and slavedevice number: {proxy.get_slave_device_number()}"
            )

    dataResult = await proxy.wait_for_data()
    if dataResult is False:  # Waits for NilanProxy to get fresh data
        if proxy.get_loaded_model_name() is None:
            raise ConfigEntryNotReady(
                f"Timed out while trying to get data from {device_id} did not correctly load a model for Model no: {proxy.get_device_model()}, device number: {proxy.get_device_number()} and slavedevice number: {proxy.get_slave_device_number()}"
            )
        _LOGGER.error(f"Could not get data from {device_id} has loaded model for {proxy.get_loaded_model_name()}")
        raise ConfigEntryNotReady(
            f"Timed out while trying to get data from {device_id} has loaded model for {proxy.get_loaded_model_name()}"
        )

    data = NilanConnectHassData(proxy=proxy)
    set_hass_data(hass, entry, data)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    proxy.notify_all_update_handlers()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = get_hass_data(hass, entry)
    data["proxy"].stop_listening()
    remove_hass_data(hass, entry)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)