"""Sensor platform for Teploty.info."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeplotyInfoCoordinator

PARALLEL_UPDATES = 0

DEVICE_CLASSES: dict[str, SensorDeviceClass] = {
    "10": SensorDeviceClass.HUMIDITY,
    "11": SensorDeviceClass.CO2,
    "12": SensorDeviceClass.PRESSURE,
    "13": SensorDeviceClass.ILLUMINANCE,
    "14": SensorDeviceClass.MOISTURE,
    "16": SensorDeviceClass.PRESSURE,
    "18": SensorDeviceClass.DISTANCE,
    "19": SensorDeviceClass.OZONE,
    "20": SensorDeviceClass.PH,
    "21": SensorDeviceClass.POWER,
    "22": SensorDeviceClass.WIND_SPEED,
    "23": SensorDeviceClass.WIND_DIRECTION,
    "24": SensorDeviceClass.VOLUME_FLOW_RATE,
    "25": SensorDeviceClass.VOLTAGE,
    "fa": SensorDeviceClass.VOLTAGE,
    "fb": SensorDeviceClass.SIGNAL_STRENGTH,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors and add newly discovered sensors on later polls."""
    coordinator: TeplotyInfoCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_ids: set[str] = set()

    @callback
    def add_new_entities() -> None:
        entities: list[TeplotyInfoSensor] = []
        for probe in coordinator.data.get("probes", []):
            for sensor in probe.get("sensors", []):
                unique_id = f"{probe['id']}:{sensor['id']}"
                if unique_id in known_ids:
                    continue
                known_ids.add(unique_id)
                entities.append(TeplotyInfoSensor(coordinator, probe, sensor))
        if entities:
            async_add_entities(entities)

    add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_new_entities))


class TeplotyInfoSensor(CoordinatorEntity[TeplotyInfoCoordinator], SensorEntity):
    """A sensor reading belonging to a Teploty.info probe."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TeplotyInfoCoordinator,
        probe: dict[str, Any],
        sensor: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._probe = probe
        self._sensor = sensor
        self._sensor_id = str(sensor["id"])
        self._probe_id = str(probe["id"])
        self._attr_unique_id = f"{self._probe_id}:{self._sensor_id}"
        self._attr_name = sensor["name"]
        self._attr_device_class = self._device_class_for_sensor(self._sensor_id)
        self._attr_native_unit_of_measurement = self._normalize_unit(
            sensor.get("unit"), self._attr_device_class
        )
        if self._attr_device_class == SensorDeviceClass.WIND_DIRECTION:
            self._attr_state_class = SensorStateClass.MEASUREMENT_ANGLE
        elif self._attr_device_class is None:
            self._attr_state_class = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._probe_id)},
            name=probe["name"],
            manufacturer="Teploty.info",
            model="Temperature probe",
            serial_number=str(probe.get("node") or probe["id"]),
        )

    @property
    def native_value(self) -> float | None:
        """Return the latest raw Teploty.info value."""
        sensor = self._current_sensor()
        value = sensor.get("value") if sensor else None
        return float(value) if value is not None else None

    @property
    def available(self) -> bool:
        """Mark missing or stale readings unavailable."""
        sensor = self._current_sensor()
        return super().available and bool(sensor and sensor.get("available"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose source ID and most recent server timestamp."""
        sensor = self._current_sensor()
        return {
            "probe": self._probe.get("name"),
            "probe_id": self._probe_id,
            "sensor_id": self._sensor_id,
            "last_updated": sensor.get("last_updated") if sensor else None,
        }

    def _current_sensor(self) -> dict[str, Any] | None:
        for probe in self.coordinator.data.get("probes", []):
            if str(probe.get("id")) != self._probe_id:
                continue
            for sensor in probe.get("sensors", []):
                if str(sensor.get("id")) == self._sensor_id:
                    return sensor
        return None

    @staticmethod
    def _normalize_unit(
        unit: str | None, device_class: SensorDeviceClass | None
    ) -> str | None:
        """Normalize units to Home Assistant's expected spelling."""
        if device_class == SensorDeviceClass.PH:
            return None
        if unit in {"℃", "°C"}:
            return UnitOfTemperature.CELSIUS
        if device_class == SensorDeviceClass.VOLUME_FLOW_RATE and unit == "l/m":
            return UnitOfVolumeFlowRate.LITERS_PER_MINUTE
        return unit or None

    @staticmethod
    def _device_class_for_sensor(sensor_id: str) -> SensorDeviceClass | None:
        """Map known Teploty.info sensor families to HA device classes."""
        family = sensor_id[:2].lower()
        if family == "28":
            return SensorDeviceClass.TEMPERATURE
        return DEVICE_CLASSES.get(family)
