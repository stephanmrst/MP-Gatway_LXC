#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${MPGATEWAY_APP_DIR:-/opt/mp-gateway}"
CFG_DIR="${MPGATEWAY_CONFIG_DIR:-/etc/mp-gateway}"
DATA_DIR="${MPGATEWAY_DATA_DIR:-/var/lib/mp-gateway}"
BACKUP_DIR="${MPGATEWAY_BACKUP_DIR:-/var/backups/mp-gateway}"
LOG_DIR="${MPGATEWAY_LOG_DIR:-/var/log/mp-gateway}"
SERVICE_NAME="mp-gateway"
SERVICE_USER="mpgateway"
INSTALL_BACKUP=""

info() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nFEHLER: %s\n' "$*" >&2; exit 1; }

on_error() {
    rc=$?
    printf '\nInstallation abgebrochen (Fehler %s).\n' "$rc" >&2
    if command -v systemctl >/dev/null 2>&1; then
        systemctl status "$SERVICE_NAME" --no-pager 2>/dev/null || true
        journalctl -u "$SERVICE_NAME" -n 50 --no-pager 2>/dev/null || true
    fi
    exit "$rc"
}
trap on_error ERR

[[ ${EUID} -eq 0 ]] || fail "Bitte als root ausführen."
[[ -r /etc/os-release ]] || fail "/etc/os-release fehlt."
# shellcheck disable=SC1091
. /etc/os-release
[[ ${ID:-} == debian ]] || fail "Unterstützt wird Debian 13; erkannt: ${PRETTY_NAME:-unbekannt}."
if [[ ${VERSION_ID:-} != 13 ]]; then
    printf 'WARNUNG: Referenzplattform ist Debian 13; erkannt: %s.\n' "${PRETTY_NAME:-unbekannt}" >&2
fi
command -v systemctl >/dev/null 2>&1 || fail "systemd wurde nicht gefunden."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ -f "$ROOT_DIR/VERSION" && -f "$ROOT_DIR/requirements.txt" && -f "$ROOT_DIR/app/main.py" ]] || \
    fail "Das Skript muss aus einem vollständig entpackten MP-Gateway-Release gestartet werden."
VERSION="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"

info "MP-Gateway ${VERSION} auf Debian installieren"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip openssh-server sudo rsync curl ca-certificates

info "Systembenutzer und Verzeichnisse vorbereiten"
getent group "$SERVICE_USER" >/dev/null || groupadd --system "$SERVICE_USER"
id "$SERVICE_USER" >/dev/null 2>&1 || \
    useradd --system --gid "$SERVICE_USER" --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 \
    "$APP_DIR" "$CFG_DIR" "$DATA_DIR" "$BACKUP_DIR" "$LOG_DIR"

if [[ -f "$APP_DIR/VERSION" ]]; then
    INSTALL_BACKUP="$BACKUP_DIR/preinstall-$(date +%Y%m%d-%H%M%S)"
    install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$INSTALL_BACKUP"
    cp -a "$APP_DIR/VERSION" "$INSTALL_BACKUP/" 2>/dev/null || true
    cp -a "$CFG_DIR/." "$INSTALL_BACKUP/config/" 2>/dev/null || true
    cp -a "$DATA_DIR/." "$INSTALL_BACKUP/data/" 2>/dev/null || true
fi

info "Programmdateien installieren"
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
rsync -a --delete \
    --exclude='.venv/' --exclude='config/' --exclude='data/' --exclude='backups/' \
    --exclude='*.pyc' --exclude='__pycache__/' \
    "$ROOT_DIR/" "$APP_DIR/"

info "Python-Umgebung aufbauen"
if [[ ! -x "$APP_DIR/.venv/bin/python" ]]; then
    python3 -m venv "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/python" -m pip install --disable-pip-version-check --upgrade pip wheel
"$APP_DIR/.venv/bin/python" -m pip install --disable-pip-version-check -r "$APP_DIR/requirements.txt"

info "Systemintegration einrichten"
cat > "$CFG_DIR/mp-gateway.env" <<ENV
MQTT2LOX_APP_ROOT=$APP_DIR
MQTT2LOX_CONFIG_DIR=$CFG_DIR
MQTT2LOX_DATA_DIR=$DATA_DIR
MQTT2LOX_BACKUP_DIR=$BACKUP_DIR
MP_GATEWAY_APP_DIR=$APP_DIR
MPGATEWAY_ADMIN_HELPER=/usr/local/lib/mp-gateway/mpgateway-admin
PYTHONUNBUFFERED=1
ENV
chown root:"$SERVICE_USER" "$CFG_DIR/mp-gateway.env"
chmod 0640 "$CFG_DIR/mp-gateway.env"

install -D -o root -g root -m 0755 "$APP_DIR/scripts/lxc/mpgateway-admin" \
    /usr/local/lib/mp-gateway/mpgateway-admin
install -o root -g root -m 0755 "$APP_DIR/scripts/lxc/mpgateway" /usr/local/sbin/mpgateway

cat > /etc/sudoers.d/mp-gateway-admin <<'SUDOERS'
mpgateway ALL=(root) NOPASSWD: /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password status, /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable, /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable
SUDOERS
chmod 0440 /etc/sudoers.d/mp-gateway-admin
visudo -cf /etc/sudoers.d/mp-gateway-admin >/dev/null

install -o root -g root -m 0644 "$APP_DIR/packaging/systemd/mp-gateway.service" \
    /etc/systemd/system/mp-gateway.service

chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR" "$DATA_DIR" "$BACKUP_DIR" "$LOG_DIR"
chown root:"$SERVICE_USER" "$CFG_DIR"
find "$CFG_DIR" -mindepth 1 -maxdepth 1 ! -name mp-gateway.env -exec chown -R "$SERVICE_USER:$SERVICE_USER" {} + 2>/dev/null || true

info "Dienste starten und prüfen"
systemctl daemon-reload
systemctl enable --now ssh
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

for _ in {1..30}; do
    systemctl is-active --quiet "$SERVICE_NAME" && break
    sleep 1
done
systemctl is-active --quiet "$SERVICE_NAME" || fail "MP-Gateway wurde nicht aktiv."

if command -v curl >/dev/null 2>&1; then
    for _ in {1..30}; do
        curl -fsS --max-time 2 http://127.0.0.1:8099/ >/dev/null 2>&1 && break
        sleep 1
    done
    curl -fsS --max-time 3 http://127.0.0.1:8099/ >/dev/null || \
        fail "Der Dienst läuft, aber die Weboberfläche auf Port 8099 antwortet nicht."
fi

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[[ -n "$IP" ]] || IP="LXC-IP"
trap - ERR
printf '\n============================================================\n'
printf 'MP-Gateway %s wurde erfolgreich installiert.\n' "$VERSION"
printf 'Weboberfläche: http://%s:8099\n' "$IP"
printf 'Verwaltung:    mpgateway status | logs | restart | backup\n'
printf 'Root-SSH per Passwort ist standardmäßig deaktiviert.\n'
if [[ -n "$INSTALL_BACKUP" ]]; then
    printf 'Sicherung vor Neuinstallation: %s\n' "$INSTALL_BACKUP"
fi
printf '============================================================\n'
