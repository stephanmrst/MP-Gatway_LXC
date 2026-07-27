"""Central process restart handling for MP-Gateway."""

from __future__ import annotations

import os
import threading
import time
from typing import Callable


RESTART_EXIT_CODE = 75


def schedule_process_restart(
    *,
    delay: float = 1.5,
    log: Callable[[str], None] | None = None,
    reason: str = "Neustart angefordert",
) -> None:
    """Terminate MP-Gateway after the current HTTP response can finish.

    systemd (``Restart=on-failure``) and Docker
    (``restart: unless-stopped``) restart the process/container. Standalone
    starts terminate cleanly and must be launched again by their supervisor or
    operator.
    """

    if log is not None:
        log(f"{reason} – Prozessneustart wird ausgeführt")

    def _restart() -> None:
        time.sleep(max(0.1, float(delay)))
        os._exit(RESTART_EXIT_CODE)

    threading.Thread(
        target=_restart,
        name="mp-gateway-process-restart",
        daemon=True,
    ).start()
