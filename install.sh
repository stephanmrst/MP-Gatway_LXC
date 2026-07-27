#!/usr/bin/env bash
set -euo pipefail

CTID="${CTID:-150}"
HOSTNAME="${HOSTNAME:-mp-gateway}"
STORAGE="${STORAGE:-local-lvm}"
MEMORY="${MEMORY:-2048}"
CORES="${CORES:-2}"
DISK="${DISK:-8}"
TEMPLATE="debian-13-standard_13"

echo "== MP-Gateway Bootstrap Installer =="

if ! command -v pct >/dev/null; then
  echo "Dieses Skript muss auf einem Proxmox-Host ausgeführt werden."
  exit 1
fi

if ! pveam available | grep -q "$TEMPLATE"; then
  pveam update
fi

TMP=$(pveam available | awk '/debian-13-standard/ {print $2; exit}')
pveam download local "$TMP" || true
TPL=$(find /var/lib/vz/template/cache -name "debian-13-standard*.tar.zst" | sort | tail -1)

pct create "$CTID" "$TPL" \
  --hostname "$HOSTNAME" \
  --cores "$CORES" \
  --memory "$MEMORY" \
  --rootfs "${STORAGE}:${DISK}" \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp

pct start "$CTID"
sleep 15

pct exec "$CTID" -- bash -c '
apt-get update
apt-get install -y curl unzip python3 git ca-certificates openssh-server
cd /root
curl -L -o mpgateway.zip https://github.com/stephanmrst/MP-Gatway_LXC/releases/latest/download/MP-Gateway_35.1.0_LXC_Debian13_Stable.zip
unzip -o mpgateway.zip
chmod +x scripts/lxc/install-debian13.sh
bash scripts/lxc/install-debian13.sh
systemctl enable mp-gateway || true
systemctl restart mp-gateway || true
'

IP=$(pct exec "$CTID" -- hostname -I | awk "{print \$1}")
echo
echo "Fertig!"
echo "Webinterface: http://$IP:5000"
