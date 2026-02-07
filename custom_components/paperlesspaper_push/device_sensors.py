from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


def _parse_iso(s: str | None) -> Optional[datetime]:
    if not s:
        return None
    # API returns e. g. "2026-02-07T16:22:39.682Z"
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _ms_to_dt(ms: int | None) -> Optional[datetime]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _battery_percent_from_mv(mv: int | None) -> Optional[int]:
    if mv is None:
        return None

    v = mv / 1000.0
    # 4xAAA batteries
    V_MIN = 4.8
    V_MAX = 6.4

    if v <= V_MIN:
        return 0
    if v >= V_MAX:
        return 100

    return round((v - V_MIN) / (V_MAX - V_MIN) * 100)


def _battery_voltage_v(mv: int | None) -> Optional[float]:
    if mv is None:
        return None
    return round(mv / 1000.0, 3)


def _get_bat_mv(data: dict) -> Optional[int]:
    # deviceStatus.batLevel is string in mV "6476"
    try:
        s = data.get("deviceStatus", {}).get("batLevel")
        if s is None:
            return None
        return int(s)
    except Exception:
        return None


def _device_name(data: dict) -> str:
    return data.get("meta", {}).get("name") or data.get("deviceId") or "paperlesspaper"


@dataclass(frozen=True)
class _SensorDef:
    key: str
    name: str
    device_class: SensorDeviceClass | None = None
    unit: str | None = None
    value_fn: Callable[[dict], Any] = lambda d: None


SENSORS: tuple[_SensorDef, ...] = (
    _SensorDef(
        key="battery_voltage",
        name="Battery Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: _battery_voltage_v(_get_bat_mv(d)),
    ),
    _SensorDef(
        key="battery_percent",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        unit=PERCENTAGE,
        value_fn=lambda d: _battery_percent_from_mv(_get_bat_mv(d)),
    ),
    _SensorDef(
        key="last_reachable",
        name="Last Reachable",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _ms_to_dt(d.get("deviceStatus", {}).get("lastReachableAgo")),
    ),
    _SensorDef(
        key="next_device_sync",
        name="Next Device Sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _ms_to_dt(d.get("deviceStatus", {}).get("nextDeviceSync")),
    ),
    _SensorDef(
        key="updated_at",
        name="Updated At",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _parse_iso(d.get("updatedAt")),
    ),
    _SensorDef(
        key="loaded_at",
        name="Loaded At",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _parse_iso(d.get("loadedAt")),
    ),
)


class PaperlesspaperDeviceSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_def: _SensorDef, unique_prefix: str):
        super().__init__(coordinator)
        self._def = sensor_def
        self._attr_unique_id = f"{unique_prefix}_{sensor_def.key}"
        self._attr_name = sensor_def.name
        self._attr_device_class = sensor_def.device_class
        self._attr_native_unit_of_measurement = sensor_def.unit
        self._attr_suggested_object_id = f"{DOMAIN}_{sensor_def.key}"

    @property
    def suggested_object_id(self) -> str:
        return f"{DOMAIN}_{self._def.key}"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return self._def.value_fn(data)

    @property
    def device_info(self):
        data = self.coordinator.data or {}
        device_id = data.get("deviceId") or "paperlesspaper"
        name = _device_name(data)
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": name,
            "manufacturer": "paperlesspaper",
            "model": data.get("kind"),
            "sw_version": data.get("iotDevice", {}).get("fwVersion"),
        }

    @property
    def extra_state_attributes(self):
        # hilfreiche Zusatzinfos in den Sensoren
        data = self.coordinator.data or {}
        ds = data.get("deviceStatus", {}) or {}
        return {
            "deviceId": data.get("deviceId"),
            "paper": data.get("paper"),
            "pictureSynced": ds.get("pictureSynced"),
            "fileVersion": ds.get("fileVersion"),
            "fwVersion": ds.get("fwVersion"),
            "sleepTime": ds.get("sleepTime"),
        }
