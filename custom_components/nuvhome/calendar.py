"""Un calendario per casa con tutte le scadenze di NuvHome (tasse, bollette, condominio, mutuo...)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import NuvHomeCoordinator
from .entity import NuvHomeEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: NuvHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    def add_new_houses() -> None:
        new_ids = [house_id for house_id in coordinator.data if house_id not in known]
        known.update(new_ids)
        async_add_entities(NuvHomeCalendar(coordinator, house_id) for house_id in new_ids)

    add_new_houses()
    entry.async_on_unload(coordinator.async_add_listener(add_new_houses))


def _to_event(deadline: dict[str, Any]) -> CalendarEvent | None:
    try:
        day = date.fromisoformat(deadline["date"])
    except (KeyError, TypeError, ValueError):
        return None
    return CalendarEvent(
        start=day,
        end=day + timedelta(days=1),
        summary=deadline.get("title") or "Scadenza",
        description=deadline.get("detail"),
        uid=deadline.get("id"),
    )


class NuvHomeCalendar(NuvHomeEntity, CalendarEntity):
    _attr_name = "Scadenze"

    def __init__(self, coordinator: NuvHomeCoordinator, house_id: str) -> None:
        super().__init__(coordinator, house_id, "deadlines_calendar")

    def _events(self) -> list[CalendarEvent]:
        house = self.house or {}
        events = [_to_event(deadline) for deadline in house.get("deadlines", [])]
        return sorted((event for event in events if event), key=lambda event: event.start)

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        return next((event for event in self._events() if event.start >= today), None)

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        return [event for event in self._events() if start_date.date() <= event.start < end_date.date()]
