from dataclasses import dataclass, field
from threading import RLock


@dataclass
class MQTTState:
    mqtt_monitor_values: dict = field(default_factory=dict)
    mqtt_clients: dict = field(default_factory=dict)
    mqtt_client: object = None
    monitor_version: int = 0
    lock: RLock = field(default_factory=RLock)
