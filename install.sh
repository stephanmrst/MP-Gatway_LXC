#!/usr/bin/env bash
set -euo pipefail

GITHUB_REPO="${GITHUB_REPO:-stephanmrst/MP-Gatway_LXC}"
RELEASE_API="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
ASSET_SUFFIX="${ASSET_SUFFIX:-_LXC_Debian13_Stable.zip}"

resolve_latest_stable() {
  local release_json
  release_json="$(curl -fsSL \
    -H 'Accept: application/vnd.github+json' \
    -H 'X-GitHub-Api-Version: 2022-11-28' \
    "$RELEASE_API")" || {
      printf 'Fehler: Aktuelles Stable-Release konnte nicht ermittelt werden.\n' >&2
      return 1
    }

  mapfile -t RELEASE_INFO < <(RELEASE_JSON="$release_json" ASSET_SUFFIX="$ASSET_SUFFIX" python3 - <<'PYJSON'
import json, os, sys
release=json.loads(os.environ['RELEASE_JSON'])
suffix=os.environ['ASSET_SUFFIX']
assets=[a for a in release.get('assets', []) if a.get('name','').endswith(suffix)]
if not assets:
    names=', '.join(a.get('name','') for a in release.get('assets', [])) or 'keine'
    print(f"Kein Stable-Asset '*{suffix}' gefunden. Vorhanden: {names}", file=sys.stderr)
    raise SystemExit(2)
preferred=[a for a in assets if a.get('name','').startswith('MP-Gateway_')]
asset=(preferred or assets)[0]
print(release.get('tag_name') or release.get('name') or 'unbekannt')
print(asset['name'])
print(asset['browser_download_url'])
PYJSON
  )
  [[ ${#RELEASE_INFO[@]} -eq 3 ]] || return 1
  RELEASE_VERSION="${RELEASE_INFO[0]}"
  RELEASE_FILE="${RELEASE_INFO[1]}"
  RELEASE_URL="${RELEASE_INFO[2]}"
}

DEFAULT_CTID="${CTID:-150}"
DEFAULT_HOSTNAME="${HOSTNAME:-MP-Gatway}"
DEFAULT_STORAGE="${STORAGE:-local-lvm}"
DEFAULT_MEMORY="${MEMORY:-2048}"
DEFAULT_SWAP="${SWAP:-512}"
DEFAULT_CORES="${CORES:-2}"
DEFAULT_DISK="${DISK:-8}"
DEFAULT_BRIDGE="${BRIDGE:-vmbr0}"
DEFAULT_ONBOOT="${ONBOOT:-1}"

say() { printf '%s\n' "$*"; }
ask() {
  local prompt="$1" default="$2" answer
  read -r -p "$prompt [$default]: " answer
  printf '%s' "${answer:-$default}"
}
ask_yes_no() {
  local prompt="$1" default="$2" answer suffix
  [[ "$default" == "yes" ]] && suffix="J/n" || suffix="j/N"
  read -r -p "$prompt ($suffix): " answer
  answer="${answer:-$default}"
  case "${answer,,}" in
    j|ja|y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

printf '\n== MP-Gateway Proxmox-LXC-Installer 0.4 ==\n'

if ! command -v pct >/dev/null 2>&1; then
  say "Fehler: Dieses Skript muss als root auf einem Proxmox-Host ausgeführt werden."
  exit 1
fi
if [[ ${EUID} -ne 0 ]]; then
  say "Fehler: Bitte als root ausführen."
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  say "Fehler: python3 wird auf dem Proxmox-Host benötigt."
  exit 1
fi

resolve_latest_stable
printf '   Aktuelle Stable-Version: %s\n' "$RELEASE_VERSION"
printf '   Release-Asset: %s\n\n' "$RELEASE_FILE"

say "Verfügbare Container-Storage-Ziele:"
pvesm status -content rootdir 2>/dev/null | awk 'NR==1 || $3=="active" {print "  "$0}' || true
say ""

CTID="$(ask 'Container-ID' "$DEFAULT_CTID")"
HOSTNAME="$(ask 'Hostname' "$DEFAULT_HOSTNAME")"
STORAGE="$(ask 'Storage für Root-Disk' "$DEFAULT_STORAGE")"
CORES="$(ask 'CPU-Kerne' "$DEFAULT_CORES")"
MEMORY="$(ask 'Arbeitsspeicher in MB' "$DEFAULT_MEMORY")"
SWAP="$(ask 'Swap in MB' "$DEFAULT_SWAP")"
DISK="$(ask 'Festplattengröße in GB' "$DEFAULT_DISK")"
BRIDGE="$(ask 'Netzwerk-Bridge' "$DEFAULT_BRIDGE")"

if ask_yes_no 'Netzwerk per DHCP konfigurieren?' yes; then
  NET_IP="dhcp"
  GATEWAY=""
else
  NET_IP="$(ask 'Statische IPv4-Adresse mit Präfix, z. B. 192.168.1.145/24' '192.168.1.145/24')"
  GATEWAY="$(ask 'IPv4-Gateway' '192.168.1.1')"
fi

VLAN_TAG=""
if ask_yes_no 'VLAN verwenden?' no; then
  VLAN_TAG="$(ask 'VLAN-ID' '10')"
fi

if ask_yes_no 'Container beim Proxmox-Start automatisch starten?' yes; then ONBOOT=1; else ONBOOT=0; fi
if ask_yes_no 'Root-SSH per Passwort direkt aktivieren?' yes; then ENABLE_ROOT_SSH=1; else ENABLE_ROOT_SSH=0; fi

ROOT_PASSWORD=""
ROOT_PASSWORD_CONFIRM=""
while [[ -z "$ROOT_PASSWORD" ]]; do
  read -r -s -p 'Root-Passwort für den LXC: ' ROOT_PASSWORD; echo
  read -r -s -p 'Root-Passwort wiederholen: ' ROOT_PASSWORD_CONFIRM; echo
  if [[ "$ROOT_PASSWORD" != "$ROOT_PASSWORD_CONFIRM" ]]; then
    say "Die Passwörter stimmen nicht überein. Bitte erneut eingeben."
    ROOT_PASSWORD=""
  fi
done

if pct status "$CTID" >/dev/null 2>&1; then
  say "Fehler: Container-ID $CTID ist bereits vergeben."
  exit 1
fi
if ! pvesm status -storage "$STORAGE" >/dev/null 2>&1; then
  say "Fehler: Storage '$STORAGE' wurde nicht gefunden."
  exit 1
fi
if ! ip link show "$BRIDGE" >/dev/null 2>&1; then
  say "Fehler: Bridge '$BRIDGE' wurde nicht gefunden."
  exit 1
fi

say ""
say "Zusammenfassung:"
say "  CT-ID:       $CTID"
say "  Hostname:    $HOSTNAME"
say "  CPU/RAM:     $CORES Kerne / ${MEMORY} MB"
say "  Swap/Disk:   ${SWAP} MB / ${DISK} GB"
say "  Storage:     $STORAGE"
say "  Netzwerk:    $NET_IP über $BRIDGE${GATEWAY:+, Gateway $GATEWAY}${VLAN_TAG:+, VLAN $VLAN_TAG}"
say "  Autostart:   $([[ $ONBOOT == 1 ]] && echo ja || echo nein)"
say "  Root-SSH:    $([[ $ENABLE_ROOT_SSH == 1 ]] && echo aktiviert || echo deaktiviert)"
say "  Download:    $RELEASE_URL"
say ""
if ! ask_yes_no 'Container jetzt erstellen und MP-Gateway installieren?' yes; then
  say "Abgebrochen."
  exit 0
fi

pveam update >/dev/null
TEMPLATE_NAME="$(pveam available | awk '/debian-13-standard/ {print $2; exit}')"
if [[ -z "$TEMPLATE_NAME" ]]; then
  say "Fehler: Kein Debian-13-LXC-Template gefunden."
  exit 1
fi
TEMPLATE_PATH="/var/lib/vz/template/cache/$(basename "$TEMPLATE_NAME")"
if [[ ! -f "$TEMPLATE_PATH" ]]; then
  say "Lade Debian-13-Template ..."
  pveam download local "$TEMPLATE_NAME"
fi

NET0="name=eth0,bridge=${BRIDGE},ip=${NET_IP}"
[[ -n "$GATEWAY" ]] && NET0+=",gw=${GATEWAY}"
[[ -n "$VLAN_TAG" ]] && NET0+=",tag=${VLAN_TAG}"

say "Erstelle LXC $CTID ..."
pct create "$CTID" "$TEMPLATE_PATH" \
  --hostname "$HOSTNAME" \
  --cores "$CORES" \
  --memory "$MEMORY" \
  --swap "$SWAP" \
  --rootfs "${STORAGE}:${DISK}" \
  --net0 "$NET0" \
  --features nesting=1 \
  --onboot "$ONBOOT" \
  --unprivileged 1 \
  --password "$ROOT_PASSWORD"

cleanup_on_error() {
  local code=$?
  if (( code != 0 )); then
    say ""
    say "Installer abgebrochen (Fehler $code)."
    say "Der angelegte Container $CTID bleibt zur Diagnose erhalten."
    pct status "$CTID" 2>/dev/null || true
  fi
  exit "$code"
}
trap cleanup_on_error EXIT

pct start "$CTID"
say "Warte auf Netzwerk im Container ..."
NETWORK_READY=0
for _ in $(seq 1 60); do
  if pct exec "$CTID" -- bash -c 'ip -4 addr show dev eth0 | grep -q "inet "' >/dev/null 2>&1; then
    NETWORK_READY=1
    break
  fi
  sleep 2
done
if [[ $NETWORK_READY -ne 1 ]]; then
  say "Fehler: Der Container hat keine IPv4-Adresse erhalten."
  exit 1
fi

pct exec "$CTID" -- env \
  RELEASE_URL="$RELEASE_URL" \
  RELEASE_VERSION="$RELEASE_VERSION" \
  ENABLE_ROOT_SSH="$ENABLE_ROOT_SSH" \
  bash -c '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
apt-get update
apt-get install -y curl unzip python3 python3-venv ca-certificates openssh-server
rm -rf /root/mp-gateway-install /root/mpgateway.zip
mkdir -p /root/mp-gateway-install
cd /root/mp-gateway-install
printf "Lade MP-Gateway %s von GitHub ...\n" "$RELEASE_VERSION"
curl -fL --retry 3 --retry-delay 2 "$RELEASE_URL" -o /root/mpgateway.zip
unzip -q /root/mpgateway.zip
INSTALL_SCRIPT="$(find /root/mp-gateway-install -type f -path '*/scripts/lxc/install-debian13.sh' -print -quit)"
if [[ -z "$INSTALL_SCRIPT" ]]; then
  echo "Fehler: scripts/lxc/install-debian13.sh wurde im Release nicht gefunden."
  find /root/mp-gateway-install -maxdepth 3 -type f | sort | head -n 100
  exit 1
fi
PROJECT_ROOT="$(cd "$(dirname "$INSTALL_SCRIPT")/../.." && pwd)"
cd "$PROJECT_ROOT"
chmod +x "$INSTALL_SCRIPT"
bash "$INSTALL_SCRIPT"

if [[ "$ENABLE_ROOT_SSH" == "1" ]]; then
  /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable
else
  /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable
fi

systemctl daemon-reload
systemctl enable mp-gateway >/dev/null
systemctl restart mp-gateway
sleep 5
if ! systemctl is-active --quiet mp-gateway; then
  echo "MP-Gateway konnte nicht gestartet werden:"
  journalctl -u mp-gateway -n 100 --no-pager
  exit 1
fi
'

IP="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"
trap - EXIT
say ""
say "========================================"
say "MP-Gateway $RELEASE_VERSION wurde installiert."
say "Weboberfläche: http://${IP}:8099"
say "Container-ID:  ${CTID}"
say "Root-SSH:      $([[ $ENABLE_ROOT_SSH == 1 ]] && echo aktiviert || echo deaktiviert)"
say "========================================"
