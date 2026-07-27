from collections import deque
from dataclasses import dataclass, field
from threading import RLock


@dataclass
class LiveLogState:
    entries: deque = field(default_factory=lambda: deque(maxlen=100))
    lock: RLock = field(default_factory=RLock)
    version: int = 0
