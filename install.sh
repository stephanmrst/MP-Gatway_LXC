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
name=asset['name']
version=name
prefix='MP-Gateway_'
if name.startswith(prefix) and name.endswith(suffix):
    version=name[len(prefix):-len(suffix)]
print(version)
print(name)
print(asset['browser_download_url'])
PYJSON
  )
  [[ ${#RELEASE_INFO[@]} -eq 3 ]] || return 1
  RELEASE_VERSION="${RELEASE_INFO[0]}"
  RELEASE_FILE="${RELEASE_INFO[1]}"
  RELEASE_URL="${RELEASE_INFO[2]}"
}

DEFAULT_CTID="${CTID:-150}"
DEFAULT_HOSTNAME="${MPG_HOSTNAME:-MP-Gatway}"
DEFAULT_STORAGE="${STORAGE:-local-lvm}"
DEFAULT_TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
DEFAULT_MEMORY="${MEMORY:-2048}"
DEFAULT_SWAP="${SWAP:-512}"
DEFAULT_CORES="${CORES:-2}"
DEFAULT_DISK="${DISK:-8}"
DEFAULT_BRIDGE="${BRIDGE:-vmbr0}"
DEFAULT_ONBOOT="${ONBOOT:-1}"

if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_GREEN=$'\033[1;32m'
  C_BLUE=$'\033[1;34m'
  C_CYAN=$'\033[1;36m'
  C_YELLOW=$'\033[1;33m'
  C_RED=$'\033[1;31m'
  C_BOLD=$'\033[1m'
else
  C_RESET=""; C_GREEN=""; C_BLUE=""; C_CYAN=""
  C_YELLOW=""; C_RED=""; C_BOLD=""
fi

say()     { printf '%s\n' "$*"; }
title()   { printf '\n%s%s%s\n' "$C_BOLD$C_BLUE" "$*" "$C_RESET"; }
step()    { printf '%s==>%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
success() { printf '%s[OK]%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn()    { printf '%s[! ]%s %s\n' "$C_YELLOW" "$C_RESET" "$*"; }
die()     { printf '%s[FEHLER]%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

if [[ -r /dev/tty ]]; then
  exec 3</dev/tty
else
  exec 3<&0
fi

ask() {
  local prompt="$1" default="$2" answer
  read -r -u 3 -p "$prompt [$default]: " answer
  printf '%s' "${answer:-$default}"
}

ask_yes_no() {
  local prompt="$1" default="$2" answer suffix
  [[ "$default" == "yes" ]] && suffix="J/n" || suffix="j/N"
  read -r -u 3 -p "$prompt ($suffix): " answer
  answer="${answer:-$default}"
  case "${answer,,}" in
    j|ja|y|yes) return 0 ;;
    *) return 1 ;;
  esac
}

choose_storage() {
  local content="$1" prompt="$2" default="$3"
  local -a items=()
  local answer i selected

  mapfile -t items < <(
    pvesm status -content "$content" 2>/dev/null |
      awk 'NR > 1 && $3 == "active" {print $1}'
  )

  ((${#items[@]})) || die "Kein aktives Proxmox-Storage mit Inhaltstyp '$content' gefunden."

  printf '\n%s\n' "$prompt" >&2
  for i in "${!items[@]}"; do
    if [[ "${items[$i]}" == "$default" ]]; then
      printf '  %s%2d)%s %s %s(Standard)%s\n' "$C_GREEN" "$((i+1))" "$C_RESET" \
        "${items[$i]}" "$C_GREEN" "$C_RESET" >&2
    else
      printf '  %2d) %s\n' "$((i+1))" "${items[$i]}" >&2
    fi
  done

  while true; do
    read -r -u 3 -p "Auswahl [${default}]: " answer
    answer="${answer:-$default}"

    if [[ "$answer" =~ ^[0-9]+$ ]] &&
       ((answer >= 1 && answer <= ${#items[@]})); then
      selected="${items[$((answer-1))]}"
      printf '%s' "$selected"
      return 0
    fi

    for selected in "${items[@]}"; do
      if [[ "$answer" == "$selected" ]]; then
        printf '%s' "$selected"
        return 0
      fi
    done

    warn "Bitte Nummer oder Storage-Namen eingeben." >&2
  done
}

printf '\n%s== MP-Gateway 35.3.0 Debian/LXC Installer ==%s\n' "$C_BOLD$C_BLUE" "$C_RESET"

command -v pct >/dev/null 2>&1 ||
  die "Dieses Skript muss auf einem Proxmox-Host ausgeführt werden."
[[ ${EUID} -eq 0 ]] || die "Bitte als root ausführen."
command -v python3 >/dev/null 2>&1 ||
  die "python3 wird auf dem Proxmox-Host benötigt."

step "Aktuelles Stable-Release ermitteln"
resolve_latest_stable
success "Stable-Version: $RELEASE_VERSION"
say "    Release-Asset: $RELEASE_FILE"

title "Container-Konfiguration"
CTID="$(ask 'Container-ID' "$DEFAULT_CTID")"
HOSTNAME="$(ask 'Hostname' "$DEFAULT_HOSTNAME")"

STORAGE="$(choose_storage rootdir \
  'Storage für die Container-Root-Disk:' "$DEFAULT_STORAGE")"

TEMPLATE_STORAGE="$(choose_storage vztmpl \
  'Storage für das Debian-13-Template:' "$DEFAULT_TEMPLATE_STORAGE")"

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
  read -r -s -u 3 -p 'Root-Passwort für den LXC: ' ROOT_PASSWORD; echo
  read -r -s -u 3 -p 'Root-Passwort wiederholen: ' ROOT_PASSWORD_CONFIRM; echo
  if [[ "$ROOT_PASSWORD" != "$ROOT_PASSWORD_CONFIRM" ]]; then
    warn "Die Passwörter stimmen nicht überein. Bitte erneut eingeben."
    ROOT_PASSWORD=""
  fi
done

pct status "$CTID" >/dev/null 2>&1 &&
  die "Container-ID $CTID ist bereits vergeben."
pvesm status -storage "$STORAGE" >/dev/null 2>&1 ||
  die "Storage '$STORAGE' wurde nicht gefunden."
pvesm status -storage "$TEMPLATE_STORAGE" >/dev/null 2>&1 ||
  die "Template-Storage '$TEMPLATE_STORAGE' wurde nicht gefunden."
ip link show "$BRIDGE" >/dev/null 2>&1 ||
  die "Bridge '$BRIDGE' wurde nicht gefunden."

title "Zusammenfassung"
say "  CT-ID:            $CTID"
say "  Hostname:         $HOSTNAME"
say "  CPU/RAM:          $CORES Kerne / ${MEMORY} MB"
say "  Swap/Disk:        ${SWAP} MB / ${DISK} GB"
say "  Root-Disk:        $STORAGE"
say "  Debian-Template:  $TEMPLATE_STORAGE"
say "  Netzwerk:         $NET_IP über $BRIDGE${GATEWAY:+, Gateway $GATEWAY}${VLAN_TAG:+, VLAN $VLAN_TAG}"
say "  Autostart:        $([[ $ONBOOT == 1 ]] && echo ja || echo nein)"
say "  Root-SSH:         $([[ $ENABLE_ROOT_SSH == 1 ]] && echo aktiviert || echo deaktiviert)"
say "  Download:         $RELEASE_URL"
say ""

if ! ask_yes_no 'Container jetzt erstellen und MP-Gateway installieren?' yes; then
  warn "Abgebrochen."
  exit 0
fi

step "Debian-13-Template prüfen"
pveam update >/dev/null
TEMPLATE_NAME="$(
  pveam available |
    awk '/debian-13-standard/ && !found {value=$2; found=1} END {if (found) print value}'
)"
[[ -n "$TEMPLATE_NAME" ]] ||
  die "Kein Debian-13-LXC-Template gefunden."

TEMPLATE_BASENAME="$(basename "$TEMPLATE_NAME")"
TEMPLATE_VOLUME="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE_BASENAME}"
TEMPLATE_PATH="$(pvesm path "$TEMPLATE_VOLUME" 2>/dev/null || true)"

if [[ -z "$TEMPLATE_PATH" || ! -f "$TEMPLATE_PATH" ]]; then
  step "Debian-13-Template nach '$TEMPLATE_STORAGE' laden"
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE_NAME"
  TEMPLATE_PATH="$(pvesm path "$TEMPLATE_VOLUME")"
else
  success "Debian-Template bereits vorhanden: $TEMPLATE_PATH"
fi

NET0="name=eth0,bridge=${BRIDGE},ip=${NET_IP}"
[[ -n "$GATEWAY" ]] && NET0+=",gw=${GATEWAY}"
[[ -n "$VLAN_TAG" ]] && NET0+=",tag=${VLAN_TAG}"

step "LXC $CTID erstellen"
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
    printf '%s[FEHLER]%s Installer abgebrochen (Fehler %s).\n' "$C_RED" "$C_RESET" "$code"
    warn "Der angelegte Container $CTID bleibt zur Diagnose erhalten."
    pct status "$CTID" 2>/dev/null || true
  fi
  exit "$code"
}
trap cleanup_on_error EXIT

step "Container starten"
pct start "$CTID"

step "Auf Netzwerk im Container warten"
NETWORK_READY=0
for _ in $(seq 1 60); do
  if pct exec "$CTID" -- bash -c \
    'ip -4 addr show dev eth0 | grep -q "inet "' >/dev/null 2>&1; then
    NETWORK_READY=1
    break
  fi
  sleep 2
done
[[ $NETWORK_READY -eq 1 ]] ||
  die "Der Container hat keine IPv4-Adresse erhalten."
success "Netzwerk ist verfügbar"

step "MP-Gateway im Container installieren"
ROOT_PASSWORD_B64="$(printf %s "$ROOT_PASSWORD" | base64 -w0)"
pct exec "$CTID" -- env \
  RELEASE_URL="$RELEASE_URL" \
  RELEASE_VERSION="$RELEASE_VERSION" \
  ENABLE_ROOT_SSH="$ENABLE_ROOT_SSH" \
  ROOT_PASSWORD_B64="$ROOT_PASSWORD_B64" \
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

printf "\n==> Lade MP-Gateway %s von GitHub\n" "$RELEASE_VERSION"
curl -fL --retry 3 --retry-delay 2 "$RELEASE_URL" -o /root/mpgateway.zip
unzip -q /root/mpgateway.zip

INSTALL_SCRIPT="$(find /root/mp-gateway-install -type f \
  -path "*/scripts/lxc/install-debian13.sh" -print -quit)"
if [[ -z "$INSTALL_SCRIPT" ]]; then
  echo "Fehler: scripts/lxc/install-debian13.sh wurde im Release nicht gefunden."
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "$INSTALL_SCRIPT")/../.." && pwd)"
cd "$PROJECT_ROOT"
chmod +x "$INSTALL_SCRIPT"
bash "$INSTALL_SCRIPT"

printf "\n==> Root-Passwort und SSH-Zugriff verbindlich konfigurieren\n"
ROOT_PASSWORD="$(printf %s "$ROOT_PASSWORD_B64" | base64 -d)"
printf "root:%s\n" "$ROOT_PASSWORD" | chpasswd
unset ROOT_PASSWORD ROOT_PASSWORD_B64

passwd -S root | grep -q "^root P " || {
  echo "Fehler: Root-Passwort wurde nicht gesetzt."
  exit 1
}

# Dateien aus dem Release nochmals verbindlich installieren. Dadurch werden
# auch ältere oder zwischengespeicherte Service-Dateien zuverlässig ersetzt.
install -D -o root -g root -m 0755   "$PROJECT_ROOT/scripts/lxc/mpgateway-admin"   /usr/local/lib/mp-gateway/mpgateway-admin

cat >/etc/sudoers.d/mp-gateway-admin <<'EOF'
mpgateway ALL=(root) NOPASSWD: /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password status, /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable, /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable
EOF
chmod 0440 /etc/sudoers.d/mp-gateway-admin
visudo -cf /etc/sudoers.d/mp-gateway-admin >/dev/null

install -o root -g root -m 0644   "$PROJECT_ROOT/packaging/systemd/mp-gateway.service"   /etc/systemd/system/mp-gateway.service

systemctl daemon-reload

if [[ "$ENABLE_ROOT_SSH" == "1" ]]; then
  /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable
else
  /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable
fi

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
printf '%s========================================%s\n' "$C_GREEN" "$C_RESET"
success "MP-Gateway $RELEASE_VERSION wurde installiert."
say "Weboberfläche: http://${IP}:8099"
say "Container-ID:  ${CTID}"
say "Root-SSH:      $([[ $ENABLE_ROOT_SSH == 1 ]] && echo aktiviert || echo deaktiviert)"
printf '%s========================================%s\n' "$C_GREEN" "$C_RESET"
