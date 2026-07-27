#!/usr/bin/env bash
set -eu

CTID="${CTID:-150}"
HOSTNAME="${HOSTNAME:-mp-gateway}"
STORAGE="${STORAGE:-local-lvm}"
MEMORY="${MEMORY:-2048}"
CORES="${CORES:-2}"
DISK="${DISK:-8}"
BRIDGE="${BRIDGE:-vmbr0}"
RELEASE_FILE="MP-Gateway_35.1.4_LXC_Debian13_Stable.zip"
RELEASE_URL="https://github.com/stephanmrst/MP-Gatway_LXC/releases/latest/download/${RELEASE_FILE}"

printf '\n== MP-Gateway Bootstrap Installer 0.1 ==\n\n'

if ! command -v pct >/dev/null 2>&1; then
  echo "Fehler: Dieses Skript muss auf einem Proxmox-Host ausgeführt werden."
  exit 1
fi

if pct status "$CTID" >/dev/null 2>&1; then
  echo "Fehler: Container-ID $CTID ist bereits vergeben."
  echo "Andere ID verwenden, z. B.: CTID=151 bash install.sh"
  exit 1
fi

pveam update >/dev/null
TEMPLATE_NAME="$(pveam available | awk '/debian-13-standard/ {print $2; exit}')"
if [ -z "$TEMPLATE_NAME" ]; then
  echo "Fehler: Kein Debian-13-LXC-Template gefunden."
  exit 1
fi

TEMPLATE_PATH="/var/lib/vz/template/cache/$(basename "$TEMPLATE_NAME")"
if [ ! -f "$TEMPLATE_PATH" ]; then
  echo "Lade Debian-13-Template ..."
  pveam download local "$TEMPLATE_NAME"
fi

 echo "Erstelle LXC $CTID ..."
pct create "$CTID" "$TEMPLATE_PATH" \
  --hostname "$HOSTNAME" \
  --cores "$CORES" \
  --memory "$MEMORY" \
  --rootfs "${STORAGE}:${DISK}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
  --features nesting=1 \
  --onboot 1

pct start "$CTID"

echo "Warte auf Netzwerk im Container ..."
for i in $(seq 1 60); do
  if pct exec "$CTID" -- bash -c 'ip -4 addr show dev eth0 | grep -q "inet "' >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

pct exec "$CTID" -- env RELEASE_URL="$RELEASE_URL" bash -c '
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl unzip python3 python3-venv ca-certificates openssh-server
rm -rf /root/mp-gateway-install /root/mpgateway.zip
mkdir -p /root/mp-gateway-install
cd /root/mp-gateway-install
curl -fL "$RELEASE_URL" -o /root/mpgateway.zip
unzip -q /root/mpgateway.zip
chmod +x scripts/lxc/install-debian13.sh
bash scripts/lxc/install-debian13.sh
systemctl daemon-reload
systemctl enable mp-gateway
systemctl restart mp-gateway
sleep 4
if ! systemctl is-active --quiet mp-gateway; then
  echo "MP-Gateway konnte nicht gestartet werden:"
  journalctl -u mp-gateway -n 80 --no-pager
  exit 1
fi
'

IP="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"

echo
echo "========================================"
echo "MP-Gateway 35.1.4 wurde installiert."
echo "Weboberfläche: http://${IP}:8099"
echo "Container-ID:  ${CTID}"
echo "========================================"
