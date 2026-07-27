"""Restricted host administration helpers for supported Debian/LXC installs."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

HELPER = os.environ.get("MPGATEWAY_ADMIN_HELPER", "/usr/local/lib/mp-gateway/mpgateway-admin")


def _run(*args: str, timeout: int = 15) -> dict[str, Any]:
    command = ["sudo", "-n", HELPER, *args]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"ok": False, "available": False, "message": "sudo oder Administrationshelfer nicht installiert"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "available": True, "message": "Administrationsaktion hat zu lange gedauert"}
    text = (proc.stdout or proc.stderr or "").strip()
    try:
        payload = json.loads(text) if text else {}
    except json.JSONDecodeError:
        payload = {"message": text}
    payload.setdefault("ok", proc.returncode == 0)
    payload.setdefault("available", proc.returncode != 127)
    if proc.returncode and not payload.get("message"):
        payload["message"] = f"Administrationshelfer meldet Fehler {proc.returncode}"
    return payload


def ssh_root_password_status() -> dict[str, Any]:
    return _run("ssh-root-password", "status")


def set_ssh_root_password(enabled: bool) -> dict[str, Any]:
    return _run("ssh-root-password", "enable" if enabled else "disable")
