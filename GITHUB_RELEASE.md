# MP-Gateway 35.2.5 – Debian 13 LXC Installer

## Schwerpunkt

Diese Version ist für den ersten stabilen Live-Test als Debian-13-LXC vorbereitet.

## Änderungen

- vollständiger Installer für vorhandene Debian-13-LXC
- Proxmox-Bootstrap zur automatischen Container-Erstellung
- idempotente Neuinstallation mit Sicherung bestehender Konfiguration und Daten
- automatische Prüfung von systemd-Dienst und Weboberfläche
- reparierter Root-SSH-Admin-Helfer
- Verwaltungsbefehle für Status, Healthcheck, Logs, Neustart, Version und Backup
- MP-Gateway startet bei Update oder Restore zentral über systemd neu

## Installation

Im entpackten Release als `root`:

```bash
./scripts/lxc/install-debian13.sh
```

Details stehen in `LXC_DEBIAN13.md`.
