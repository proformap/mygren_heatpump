"""Data models for the Mygren Heat Pump integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .mygren_api import MygrenAPI


@dataclass
class MygrenRuntimeData:
    """Runtime data stored in ConfigEntry.runtime_data."""

    api: MygrenAPI
    coordinator: DataUpdateCoordinator[dict[str, Any]]


type MygrenConfigEntry = ConfigEntry[MygrenRuntimeData]
