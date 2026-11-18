"""Sensori per casa: ultima bolletta di luce, gas e acqua, spesa e scadenze."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NuvHomeCoordinator
from .entity import NuvHomeEntity

UTILITIES = {
    "electricity": ("Luce", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, "€/kWh"),
    "gas": ("Gas", UnitOfVolume.CUBIC_METERS, SensorDeviceClass.GAS, "€/m³"),
    "water": ("Acqua", UnitOfVolume.CUBIC_METERS, SensorDeviceClass.WATER, "€/m³"),
}


@dataclass(frozen=True, kw_only=True)
class NuvHomeSensorDescription(SensorEntityDescription):
    value: Callable[[dict[str, Any]], Any]
    attributes: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _bill(house: dict[str, Any], utility: str) -> dict[str, Any]:
    return ((house.get("utilities") or {}).get(utility) or {}).get("lastBill") or {}


def _utility_descriptions(utility: str) -> list[NuvHomeSensorDescription]:
    label, unit, device_class, price_unit = UTILITIES[utility]
    return [
        NuvHomeSensorDescription(
            key=f"{utility}_last_bill",
            name=f"{label}: ultima bolletta",
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement=CURRENCY_EURO,
            suggested_display_precision=2,
            value=lambda house, u=utility: _bill(house, u).get("totalEuro"),
            attributes=lambda house, u=utility: {
                key: value
                for key, value in {
                    "periodo": _bill(house, u).get("period"),
                    "fornitore": _bill(house, u).get("supplier"),
                    "scadenza": _bill(house, u).get("dueDate"),
                }.items()
                if value is not None
            },
        ),
        NuvHomeSensorDescription(
            key=f"{utility}_last_consumption",
            name=f"{label}: consumo dell'ultima bolletta",
            device_class=device_class,
            native_unit_of_measurement=unit,
            suggested_display_precision=1,
            value=lambda house, u=utility: _bill(house, u).get("consumption"),
        ),
        NuvHomeSensorDescription(
            key=f"{utility}_unit_price",
            name=f"{label}: prezzo medio per unità",
            native_unit_of_measurement=price_unit,
            suggested_display_precision=3,
            value=lambda house, u=utility: _bill(house, u).get("unitPriceEuro"),
        ),
        NuvHomeSensorDescription(
            key=f"{utility}_last_12_months",
            name=f"{label}: spesa degli ultimi 12 mesi",
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement=CURRENCY_EURO,
            suggested_display_precision=2,
            value=lambda house, u=utility: ((house.get("utilities") or {}).get(u) or {}).get("last12MonthsEuro"),
        ),
    ]


def _next_deadline_date(house: dict[str, Any]) -> date | None:
    value = (house.get("nextDeadline") or {}).get("date")
    return date.fromisoformat(value) if value else None


DESCRIPTIONS: list[NuvHomeSensorDescription] = [
    description for utility in UTILITIES for description in _utility_descriptions(utility)
] + [
    NuvHomeSensorDescription(
        key="next_deadline",
        name="Prossima scadenza",
        device_class=SensorDeviceClass.DATE,
        value=_next_deadline_date,
        attributes=lambda house: {
            key: value
            for key, value in {"titolo": (house.get("nextDeadline") or {}).get("title"), "dettaglio": (house.get("nextDeadline") or {}).get("detail")}.items()
            if value
        },
    ),
    NuvHomeSensorDescription(key="deadlines_30_days", name="Scadenze nei prossimi 30 giorni", value=lambda house: house.get("deadlinesNext30Days")),
    NuvHomeSensorDescription(key="overdue", name="Scadenze superate", value=lambda house: house.get("overdueCount")),
    NuvHomeSensorDescription(key="bills_due_count", name="Bollette in scadenza", value=lambda house: (house.get("billsDue") or {}).get("count")),
    NuvHomeSensorDescription(
        key="bills_due_total",
        name="Importo bollette in scadenza",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY_EURO,
        suggested_display_precision=2,
        value=lambda house: (house.get("billsDue") or {}).get("totalEuro"),
    ),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: NuvHomeCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    def add_new_houses() -> None:
        new_ids = [house_id for house_id in coordinator.data if house_id not in known]
        known.update(new_ids)
        async_add_entities(NuvHomeSensor(coordinator, house_id, description) for house_id in new_ids for description in DESCRIPTIONS)

    add_new_houses()
    # Una casa aggiunta in NuvHome compare da sola al prossimo aggiornamento.
    entry.async_on_unload(coordinator.async_add_listener(add_new_houses))


class NuvHomeSensor(NuvHomeEntity, SensorEntity):
    entity_description: NuvHomeSensorDescription

    def __init__(self, coordinator: NuvHomeCoordinator, house_id: str, description: NuvHomeSensorDescription) -> None:
        super().__init__(coordinator, house_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        house = self.house
        return self.entity_description.value(house) if house else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        house = self.house
        if not house or not self.entity_description.attributes:
            return None
        return self.entity_description.attributes(house)
