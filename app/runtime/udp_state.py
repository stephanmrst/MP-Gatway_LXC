from collections import deque
from dataclasses import dataclass, field
from threading import RLock


@dataclass
class UDPState:
    monitor_log: deque = field(default_factory=lambda: deque(maxlen=250))
    mqtt2udp_last_seen: dict = field(default_factory=dict)
    udp2mqtt_last_seen: dict = field(default_factory=dict)
    udp2knx_last_seen: dict = field(default_factory=dict)
    udp_input_last_seen: dict = field(default_factory=dict)
    discovery_state: dict = field(default_factory=dict)
    discovery_enabled: bool = False
    listener_running: bool = False
    stop_requested: bool = False
    explorer_listen_port: str = ""
    listener_thread: object = None
    listener_threads: dict = field(default_factory=dict)
    listener_stop_events: dict = field(default_factory=dict)
    packet_count: int = 0
    status: str = "stopped"
    lock: RLock = field(default_factory=RLock)
