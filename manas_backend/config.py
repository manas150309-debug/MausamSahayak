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
    demo_mode: bool = False          # enables public presentation-only simulation controls
    accuweather_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-6-luna"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    session_secret: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    sms_provider: str = "dryrun"
    twilio_sid: str = ""
    twilio_token: str = ""
    twilio_from: str = ""

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
            demo_mode=e("MAUSAM_DEMO_MODE", "false").strip().lower() in ("1", "true", "yes", "on"),
            accuweather_api_key=e("ACCUWEATHER_API_KEY", ""),
            openai_api_key=e("OPENAI_API_KEY", ""), openai_model=e("OPENAI_MODEL", "gpt-6-luna"),
            gemini_api_key=e("GEMINI_API_KEY", ""), gemini_model=e("GEMINI_MODEL", "gemini-3.8-flash"),
            session_secret=e("SESSION_SECRET", ""),
            smtp_host=e("SMTP_HOST", ""), smtp_port=int(e("SMTP_PORT", "587")),
            smtp_user=e("SMTP_USER", ""), smtp_password=e("SMTP_PASSWORD", ""),
            smtp_from=e("SMTP_FROM", ""), sms_provider=e("SMS_PROVIDER", "dryrun"),
            twilio_sid=e("TWILIO_SID", ""), twilio_token=e("TWILIO_TOKEN", ""),
            twilio_from=e("TWILIO_FROM", ""),
        )
