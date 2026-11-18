"""Base comune: ogni casa di NuvHome e' un dispositivo di Home Assistant."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NuvHomeCoordinator


class NuvHomeEntity(CoordinatorEntity[NuvHomeCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: NuvHomeCoordinator, house_id: str, key: str) -> None:
        super().__init__(coordinator)
        self._house_id = house_id
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{house_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}_{house_id}")},
            name=(coordinator.data.get(house_id) or {}).get("name") or "Casa",
            manufacturer="NuvHome",
        )

    @property
    def house(self) -> dict[str, Any] | None:
        return self.coordinator.data.get(self._house_id)

    @property
    def available(self) -> bool:
        return super().available and self.house is not None
