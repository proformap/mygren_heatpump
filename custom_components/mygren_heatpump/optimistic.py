"""Helpers for showing a changed value before the heat pump confirms it."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
import time
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import OPTIMISTIC_TIMEOUT
from .mygren_api import MygrenAPIError


class PendingValue:
    """A value shown in the UI until telemetry confirms it or it times out.

    The timeout covers a write the pump accepts but never applies, such as a
    value it silently limits. Without it, the UI would show that value forever.
    """

    def __init__(self) -> None:
        """Start with nothing pending."""
        self._value: Any = None
        self._expires_at = 0.0

    @property
    def value(self) -> Any:
        """Return the pending value, or None if nothing is pending."""
        return self._value

    def set(self, value: Any) -> None:
        """Show this value until it is confirmed or times out."""
        self._value = value
        self._expires_at = time.monotonic() + OPTIMISTIC_TIMEOUT

    def clear(self) -> None:
        """Go back to showing telemetry."""
        self._value = None

    def settle(self, confirmed: Callable[[Any], bool]) -> None:
        """Clear the value if telemetry confirms it or the timeout has passed."""
        if self._value is None:
            return
        if confirmed(self._value) or time.monotonic() >= self._expires_at:
            self.clear()


@asynccontextmanager
async def rollback_on_error(entity: Any, pending: PendingValue) -> AsyncIterator[None]:
    """Undo a pending value and report the error if a write to the pump fails.

    A refresh is requested because a failed write may still have been applied,
    for example after a timeout or when only part of a mode change succeeded.
    """
    try:
        yield
    except MygrenAPIError as err:
        pending.clear()
        entity.async_write_ha_state()
        await entity.coordinator.async_request_refresh()
        raise HomeAssistantError(f"Mygren heat pump write failed: {err}") from err
