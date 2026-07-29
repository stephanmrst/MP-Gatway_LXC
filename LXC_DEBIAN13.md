# MP-Gateway auf Debian 13 LXC

## Installation

1. Einen Debian-13-LXC mit fester IP anlegen.
2. Das Release-ZIP entpacken.
3. Im entpackten Verzeichnis als root ausführen:

```bash
./scripts/lxc/install-debian13.sh
```

Danach läuft MP-Gateway unter `http://LXC-IP:8099` als systemd-Dienst.

## Verzeichnisse

- Anwendung: `/opt/mp-gateway`
- Konfiguration: `/etc/mp-gateway`
- Laufzeitdaten: `/var/lib/mp-gateway`
- Sicherungen: `/var/backups/mp-gateway`
- Logs: systemd-Journal

## Verwaltung

```bash
mpgateway status
mpgateway restart
mpgateway logs
mpgateway backup
```

## SSH-Rootzugriff

OpenSSH wird installiert. Root-Login per Passwort ist standardmäßig deaktiviert. Er kann in **Einstellungen → Debian / LXC-System** ein- oder ausgeschaltet werden. SSH-Schlüssel bleiben beim Ausschalten erlaubt. Vor der ersten Passwortanmeldung muss im LXC einmal ein Root-Passwort gesetzt werden:

```bash
passwd root
```
