import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = "mausam.db"
    api_key: str = ""                 # protects POST endpoints; empty = writes disabled
    stale_minutes: float = 30.0
    max_node_distance_km: float = 30.0
    deescalate_minutes: float = 30.0  # a risk level may only be lowered this long after the last alert
    rise_window_min: float = 90.0
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_user: str = ""
    mqtt_password: str = ""
    worker_interval_s: int = 60

    @classmethod
    def from_env(cls):
        e = os.environ.get
        return cls(
            db_path=e("MAUSAM_DB", "mausam.db"), api_key=e("MAUSAM_API_KEY", ""),
            stale_minutes=float(e("STALE_MINUTES", "30")),
            max_node_distance_km=float(e("MAX_NODE_DISTANCE_KM", "30")),
            deescalate_minutes=float(e("DEESCALATE_MINUTES", "30")),
            mqtt_host=e("MQTT_HOST", "localhost"), mqtt_port=int(e("MQTT_PORT", "1883")),
            mqtt_user=e("MQTT_USER", ""), mqtt_password=e("MQTT_PASSWORD", ""),
            worker_interval_s=int(e("WORKER_INTERVAL_S", "60")),
        )
