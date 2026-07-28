#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="35.2.4"
CTID="${CTID:-150}"
HOSTNAME="${HOSTNAME:-mp-gateway}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
MEMORY="${MEMORY:-2048}"
CORES="${CORES:-2}"
DISK="${DISK:-8}"
BRIDGE="${BRIDGE:-vmbr0}"
IP_CONFIG="${IP_CONFIG:-dhcp}"
GATEWAY="${GATEWAY:-}"
RELEASE_FILE="MP-Gateway_${VERSION}_LXC_Debian13_Stable.zip"
RELEASE_URL="${RELEASE_URL:-https://github.com/stephanmrst/MP-Gatway_LXC/releases/latest/download/${RELEASE_FILE}}"
CREATED=0

info() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nFEHLER: %s\n' "$*" >&2; exit 1; }

cleanup_error() {
    rc=$?
    printf '\nInstaller abgebrochen (Fehler %s).\n' "$rc" >&2
    if [[ $CREATED -eq 1 ]]; then
        printf 'Der angelegte Container %s bleibt zur Diagnose erhalten.\n' "$CTID" >&2
        pct status "$CTID" 2>/dev/null || true
    fi
    exit "$rc"
}
trap cleanup_error ERR

[[ ${EUID} -eq 0 ]] || fail "Bitte auf dem Proxmox-Host als root ausführen."
command -v pct >/dev/null 2>&1 || fail "Dieses Skript muss auf einem Proxmox-Host ausgeführt werden."
command -v pveam >/dev/null 2>&1 || fail "pveam wurde nicht gefunden."
[[ "$CTID" =~ ^[0-9]+$ ]] || fail "CTID muss numerisch sein."
[[ "$MEMORY" =~ ^[0-9]+$ && "$CORES" =~ ^[0-9]+$ && "$DISK" =~ ^[0-9]+$ ]] || \
    fail "MEMORY, CORES und DISK müssen numerisch sein."

printf '\n== MP-Gateway %s LXC-Installer ==\n' "$VERSION"
printf 'CTID: %s | Hostname: %s | Netzwerk: %s\n' "$CTID" "$HOSTNAME" "$IP_CONFIG"

pct status "$CTID" >/dev/null 2>&1 && \
    fail "Container-ID $CTID ist bereits vergeben. Beispiel: CTID=151 bash install.sh"

info "Debian-13-LXC-Template ermitteln"
pveam update >/dev/null
TEMPLATE_NAME="$(pveam available --section system | awk '/debian-13-standard/ {print $2; exit}')"
[[ -n "$TEMPLATE_NAME" ]] || fail "Kein Debian-13-LXC-Template gefunden."
TEMPLATE_VOLID="${TEMPLATE_STORAGE}:vztmpl/$(basename "$TEMPLATE_NAME")"
if ! pvesm path "$TEMPLATE_VOLID" >/dev/null 2>&1; then
    info "Debian-13-Template herunterladen"
    pveam download "$TEMPLATE_STORAGE" "$TEMPLATE_NAME"
fi

NET0="name=eth0,bridge=${BRIDGE},ip=${IP_CONFIG}"
if [[ "$IP_CONFIG" != dhcp && -n "$GATEWAY" ]]; then
    NET0+=",gw=${GATEWAY}"
fi

info "LXC $CTID erstellen"
pct create "$CTID" "$TEMPLATE_VOLID" \
    --hostname "$HOSTNAME" \
    --cores "$CORES" \
    --memory "$MEMORY" \
    --rootfs "${STORAGE}:${DISK}" \
    --net0 "$NET0" \
    --features nesting=1 \
    --unprivileged 1 \
    --onboot 1 \
    --start 1
CREATED=1

info "Auf Netzwerk und DNS warten"
network_ready=0
for _ in $(seq 1 60); do
    if pct exec "$CTID" -- bash -c 'ip -4 route get 1.1.1.1 >/dev/null 2>&1 && getent hosts github.com >/dev/null 2>&1'; then
        network_ready=1
        break
    fi
    sleep 2
done
[[ $network_ready -eq 1 ]] || fail "Der Container hat nach 120 Sekunden kein funktionierendes Netzwerk/DNS."

info "Release laden und im Container installieren"
pct exec "$CTID" -- env RELEASE_URL="$RELEASE_URL" bash -c '
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends curl unzip ca-certificates
rm -rf /root/mp-gateway-install /root/mpgateway.zip
mkdir -p /root/mp-gateway-install
curl --fail --location --retry 3 --retry-delay 2 "$RELEASE_URL" -o /root/mpgateway.zip
unzip -q /root/mpgateway.zip -d /root/mp-gateway-install
cd /root/mp-gateway-install
chmod +x scripts/lxc/install-debian13.sh
./scripts/lxc/install-debian13.sh
'

IP="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"
[[ -n "$IP" ]] || IP="unbekannt"
trap - ERR
printf '\n============================================================\n'
printf 'MP-Gateway %s wurde erfolgreich installiert.\n' "$VERSION"
printf 'Weboberfläche: http://%s:8099\n' "$IP"
printf 'Container-ID:  %s\n' "$CTID"
printf 'Konsole:       pct enter %s\n' "$CTID"
printf '============================================================\n'
