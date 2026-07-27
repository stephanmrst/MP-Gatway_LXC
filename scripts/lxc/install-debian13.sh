#!/bin/bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then echo "Bitte als root ausführen." >&2; exit 1; fi
. /etc/os-release
if [[ ${ID:-} != debian || ${VERSION_ID:-} != 13 ]]; then
  echo "Hinweis: Referenzplattform ist Debian 13; erkannt: ${PRETTY_NAME:-unbekannt}." >&2
fi

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
APP_DIR=/opt/mp-gateway
CFG_DIR=/etc/mp-gateway
DATA_DIR=/var/lib/mp-gateway
BACKUP_DIR=/var/backups/mp-gateway
LOG_DIR=/var/log/mp-gateway

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip openssh-server sudo rsync curl ca-certificates
getent group mpgateway >/dev/null || groupadd --system mpgateway
id mpgateway >/dev/null 2>&1 || useradd --system --gid mpgateway --home-dir "$APP_DIR" --shell /usr/sbin/nologin mpgateway
install -d -o mpgateway -g mpgateway -m 0750 "$APP_DIR" "$CFG_DIR" "$DATA_DIR" "$BACKUP_DIR" "$LOG_DIR"

rsync -a --delete --exclude='.venv/' --exclude='config/' --exclude='data/' --exclude='backups/' "$ROOT_DIR/" "$APP_DIR/"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip wheel
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

cat > "$CFG_DIR/mp-gateway.env" <<EOF
MQTT2LOX_APP_ROOT=$APP_DIR
MQTT2LOX_CONFIG_DIR=$CFG_DIR
MQTT2LOX_DATA_DIR=$DATA_DIR
MQTT2LOX_BACKUP_DIR=$BACKUP_DIR
MPGATEWAY_ADMIN_HELPER=/usr/local/lib/mp-gateway/mpgateway-admin
PYTHONUNBUFFERED=1
EOF
chmod 0640 "$CFG_DIR/mp-gateway.env"
chown root:mpgateway "$CFG_DIR/mp-gateway.env"

install -D -o root -g root -m 0755 "$APP_DIR/scripts/lxc/mpgateway-admin" /usr/local/lib/mp-gateway/mpgateway-admin
install -o root -g root -m 0755 "$APP_DIR/scripts/lxc/mpgateway" /usr/local/sbin/mpgateway
cat > /etc/sudoers.d/mp-gateway-admin <<'EOF'
mpgateway ALL=(root) NOPASSWD: /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password status, /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable, /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable, /usr/local/lib/mp-gateway/mpgateway-admin service restart
EOF
chmod 0440 /etc/sudoers.d/mp-gateway-admin
visudo -cf /etc/sudoers.d/mp-gateway-admin >/dev/null

install -o root -g root -m 0644 "$APP_DIR/packaging/systemd/mp-gateway.service" /etc/systemd/system/mp-gateway.service
chown -R mpgateway:mpgateway "$APP_DIR" "$CFG_DIR" "$DATA_DIR" "$BACKUP_DIR" "$LOG_DIR"
systemctl enable --now ssh
systemctl daemon-reload
systemctl enable --now mp-gateway

echo
echo "MP-Gateway wurde installiert."
echo "Weboberfläche: http://$(hostname -I | awk '{print $1}'):8099"
echo "Root-SSH per Passwort ist standardmäßig AUS und kann in den MP-Gateway-Einstellungen aktiviert werden."
