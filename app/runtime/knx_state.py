from collections import deque
from dataclasses import dataclass, field
from threading import RLock


@dataclass
class KNXState:
    monitor_log: deque = field(default_factory=lambda: deque(maxlen=250))
    monitor_values: dict = field(default_factory=dict)
    mqtt2knx_last_seen: dict = field(default_factory=dict)
    knx2mqtt_last_seen: dict = field(default_factory=dict)
    knx2lox_last_seen: dict = field(default_factory=dict)
    listener_thread: object = None
    listener_running: bool = False
    start_requested: bool = False
    stop_requested: bool = False
    monitor_version: int = 0
    xknx: object = None
    loop: object = None
    connection_status: str = "stopped"
    connection_mode: str = ""
    gateway_ip: str = ""
    gateway_port: int = 3671
    local_ip: str = ""
    physical_address: str = ""
    last_error: str = ""
    last_test: dict = field(default_factory=dict)
    lock: RLock = field(default_factory=RLock)
