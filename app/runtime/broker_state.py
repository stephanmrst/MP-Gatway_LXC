from dataclasses import dataclass, field
from threading import RLock


@dataclass
class BrokerState:
    process: object = None
    running: bool = False
    status: str = "gestoppt"
    start_requested: bool = False
    stop_requested: bool = False
    restart_requested: bool = False
    lock: RLock = field(default_factory=RLock)
