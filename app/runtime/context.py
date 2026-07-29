from dataclasses import dataclass

from .bridge_state import BridgeState
from .live_log import LiveLogState
from .mqtt_state import MQTTState
from .knx_state import KNXState
from .udp_state import UDPState
from .broker_state import BrokerState


@dataclass
class RuntimeContext:
    bridge: BridgeState
    live_log: LiveLogState
    mqtt: MQTTState
    knx: KNXState
    udp: UDPState
    broker: BrokerState


def create_runtime_context() -> RuntimeContext:
    return RuntimeContext(
        bridge=BridgeState(),
        live_log=LiveLogState(),
        mqtt=MQTTState(),
        knx=KNXState(),
        udp=UDPState(),
        broker=BrokerState(),
    )
