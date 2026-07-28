# MP-Gateway 35.2.5 auf Debian 13 LXC

## Variante A: vorhandenen Debian-13-LXC verwenden

1. Release-ZIP in den Container kopieren und vollständig entpacken.
2. Im entpackten Verzeichnis als `root` ausführen:

```bash
chmod +x scripts/lxc/install-debian13.sh
./scripts/lxc/install-debian13.sh
```

Der Installer übernimmt automatisch:

- benötigte Debian-Pakete und Python-Abhängigkeiten
- Systembenutzer `mpgateway`
- virtuelle Python-Umgebung
- systemd-Dienst und Autostart
- OpenSSH-Server
- Admin-Helfer für den Root-SSH-Schalter
- Start- und HTTP-Prüfung auf Port 8099

Danach ist die Weboberfläche unter `http://LXC-IP:8099` erreichbar.

## Variante B: LXC direkt auf dem Proxmox-Host erstellen

Das Skript `install.sh` wird auf dem Proxmox-Host als `root` gestartet. Standardwerte:

- CTID: `150`
- Hostname: `mp-gateway`
- 2 CPU-Kerne
- 2048 MB RAM
- 8 GB Disk auf `local-lvm`
- DHCP an `vmbr0`

Beispiel:

```bash
chmod +x install.sh
CTID=151 STORAGE=local-lvm bash install.sh
```

Statische IP:

```bash
CTID=151 IP_CONFIG=192.168.1.51/24 GATEWAY=192.168.1.1 bash install.sh
```

Weitere Variablen: `HOSTNAME`, `MEMORY`, `CORES`, `DISK`, `BRIDGE`, `TEMPLATE_STORAGE` und `RELEASE_URL`.

## Erneute Installation

Der Debian-Installer ist wiederholbar. Vor dem Überschreiben einer vorhandenen Installation werden Konfiguration und Laufzeitdaten nach
`/var/backups/mp-gateway/preinstall-DATUM-UHRZEIT` gesichert. Die Verzeichnisse unter `/etc/mp-gateway` und `/var/lib/mp-gateway` bleiben erhalten.

## Verzeichnisse

- Anwendung: `/opt/mp-gateway`
- Konfiguration: `/etc/mp-gateway`
- Laufzeitdaten: `/var/lib/mp-gateway`
- Sicherungen: `/var/backups/mp-gateway`
- Logs: systemd-Journal

## Verwaltung

```bash
mpgateway status
mpgateway health
mpgateway version
mpgateway restart
mpgateway logs 200
mpgateway follow 100
mpgateway backup
```

## Root-Zugriff per SSH-Passwort

OpenSSH wird installiert. Root-Login per Passwort ist standardmäßig deaktiviert und kann unter **Einstellungen → Debian / LXC-System** ein- oder ausgeschaltet werden. SSH-Schlüssel bleiben beim Ausschalten erlaubt.

Vor der ersten Passwortanmeldung muss einmal ein Root-Passwort gesetzt werden:

```bash
passwd root
```

## Erste Diagnose

```bash
systemctl status mp-gateway --no-pager
journalctl -u mp-gateway -n 200 --no-pager
mpgateway health
ss -lntp | grep 8099
```
