"""Device info helper for Mygren Heat Pump integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .const import CONF_HOST, DOMAIN


def mygren_device_info(entry: ConfigEntry, sw_version: str | None = None) -> dict:
    """Return common device info dict for all Mygren entities.

    Includes configuration_url pointing to the heat pump's service desk.
    """
    host = entry.data.get(CONF_HOST, "")
    # host is stored with scheme, e.g. "https://mygren.home.arpa"
    config_url = f"{host}/servicedesk" if host else None

    info = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.title,
        "manufacturer": "Mygren (AI Trade s.r.o.)",
        "model": "Geo Heat Pump SMARTHUB S06",
    }

    if sw_version:
        info["sw_version"] = sw_version

    if config_url:
        info["configuration_url"] = config_url

    return info
