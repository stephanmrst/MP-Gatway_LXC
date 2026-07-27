from dataclasses import dataclass


@dataclass
class BridgeState:
    running: bool = False
    status: str = "gestoppt"
    stop_requested: bool = False
    thread: object = None
