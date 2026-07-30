#!/usr/bin/env bash
set -Eeuo pipefail

GITHUB_REPO="${GITHUB_REPO:-stephanmrst/MP-Gatway_LXC}"
RELEASE_API="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
ASSET_SUFFIX="${ASSET_SUFFIX:-_LXC_Debian13_Stable.zip}"
TITLE="MP-Gateway LXC-Installer"
BACKTITLE="MP-Gateway – Debian 13 LXC"
LOG_FILE="/tmp/mp-gateway-install-$(date +%Y%m%d-%H%M%S).log"

DEFAULT_CTID="${CTID:-150}"
DEFAULT_HOSTNAME="${MPG_HOSTNAME:-MP-Gateway}"
DEFAULT_STORAGE="${STORAGE:-local-lvm}"
DEFAULT_TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
DEFAULT_MEMORY="${MEMORY:-2048}"
DEFAULT_SWAP="${SWAP:-512}"
DEFAULT_CORES="${CORES:-2}"
DEFAULT_DISK="${DISK:-8}"
DEFAULT_BRIDGE="${BRIDGE:-vmbr0}"

[[ ${EUID} -eq 0 ]] || { echo "Bitte als root ausführen." >&2; exit 1; }
command -v pct >/dev/null 2>&1 || { echo "Dieses Skript muss auf einem Proxmox-Host laufen." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 fehlt auf dem Proxmox-Host." >&2; exit 1; }

if ! command -v dialog >/dev/null 2>&1; then
  echo "dialog wird installiert ..."
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dialog
fi

wt() { dialog --backtitle "$BACKTITLE" "$@"; }
abort() { clear; echo "Installation abgebrochen."; exit 0; }
error_box() { wt --title "Fehler" --msgbox "$1" 12 76; }

run_dialog() {
  local __var="$1"; shift
  local value rc
  set +e
  value="$(wt "$@" 3>&1 1>&2 2>&3)"; rc=$?
  set -e
  case $rc in
    0) printf -v "$__var" '%s' "$value"; return 0 ;;
    1) return 1 ;;
    3|255) abort ;;
    *) abort ;;
  esac
}

input_page() {
  local __var="$1" title="$2" prompt="$3" default="$4"; shift 4
  run_dialog "$__var" --title "$title" --ok-label "Weiter" --cancel-label "Zurück" \
    --extra-button --extra-label "Abbrechen" --inputbox "$prompt" 11 72 "$default"
}

password_page() {
  local __var="$1" title="$2" prompt="$3"
  run_dialog "$__var" --title "$title" --ok-label "Weiter" --cancel-label "Zurück" \
    --extra-button --extra-label "Abbrechen" --passwordbox "$prompt" 11 72
}

menu_page() {
  local __var="$1" title="$2" prompt="$3" height="$4" width="$5" listheight="$6"; shift 6
  run_dialog "$__var" --title "$title" --ok-label "Weiter" --cancel-label "Zurück" \
    --extra-button --extra-label "Abbrechen" --menu "$prompt" "$height" "$width" "$listheight" "$@"
}

radiolist_page() {
  local __var="$1" title="$2" prompt="$3" height="$4" width="$5" listheight="$6"; shift 6
  run_dialog "$__var" --title "$title" --ok-label "Weiter" --cancel-label "Zurück" \
    --extra-button --extra-label "Abbrechen" \
    --radiolist "$prompt" "$height" "$width" "$listheight" "$@"
}

yesno_page() {
  local title="$1" text="$2" yeslabel="$3" nolabel="$4" default_choice="${5:-yes}" rc
  local default_args=()
  [[ "$default_choice" == "no" ]] && default_args+=(--defaultno)
  set +e
  wt --title "$title" --yes-label "$yeslabel" --no-label "$nolabel" \
    --extra-button --extra-label "Abbrechen" "${default_args[@]}" --yesno "$text" 11 72
  rc=$?; set -e
  case $rc in 0) return 0;; 1) return 1;; *) abort;; esac
}

resolve_latest_stable() {
  local release_json
  release_json="$(curl -fsSL -H 'Accept: application/vnd.github+json' \
    -H 'X-GitHub-Api-Version: 2022-11-28' "$RELEASE_API")" || return 1
  mapfile -t RELEASE_INFO < <(RELEASE_JSON="$release_json" ASSET_SUFFIX="$ASSET_SUFFIX" python3 - <<'PYJSON'
import json, os, sys
release=json.loads(os.environ['RELEASE_JSON']); suffix=os.environ['ASSET_SUFFIX']
assets=[a for a in release.get('assets',[]) if a.get('name','').endswith(suffix)]
if not assets: raise SystemExit(2)
preferred=[a for a in assets if a.get('name','').startswith('MP-Gateway_')]
a=(preferred or assets)[0]; name=a['name']; prefix='MP-Gateway_'
version=name[len(prefix):-len(suffix)] if name.startswith(prefix) else release.get('tag_name','unbekannt')
print(version); print(name); print(a['browser_download_url'])
PYJSON
  )
  [[ ${#RELEASE_INFO[@]} -eq 3 ]] || return 1
  RELEASE_VERSION="${RELEASE_INFO[0]}"; RELEASE_FILE="${RELEASE_INFO[1]}"; RELEASE_URL="${RELEASE_INFO[2]}"
}

wt --title "Willkommen" --ok-label "Weiter" --msgbox \
"Willkommen zum MP-Gateway-Installer.\n\nDieser Assistent erstellt einen Debian-13-LXC auf Proxmox und installiert automatisch das aktuelle Stable-Release.\n\nAlle Angaben können vor der Installation nochmals geprüft werden." 15 72

wt --title "Stable-Release" --infobox "Aktuelles MP-Gateway Stable-Release wird ermittelt ..." 8 62
if ! resolve_latest_stable; then
  error_box "Das aktuelle Stable-Release oder das passende LXC-Asset konnte nicht ermittelt werden."
  exit 1
fi

mapfile -t ROOT_STORAGES < <(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 && $3=="active" {print $1}')
mapfile -t TEMPLATE_STORAGES < <(pvesm status -content vztmpl 2>/dev/null | awk 'NR>1 && $3=="active" {print $1}')
mapfile -t BRIDGES < <(ip -o link show | awk -F': ' '$2 ~ /^vmbr[0-9]+(@.*)?$/ {sub(/@.*/,"",$2); print $2}')
((${#ROOT_STORAGES[@]})) || { error_box "Kein aktives Storage für Container-Rootdisks gefunden."; exit 1; }
((${#TEMPLATE_STORAGES[@]})) || { error_box "Kein aktives Storage für LXC-Templates gefunden."; exit 1; }
((${#BRIDGES[@]})) || BRIDGES=(vmbr0)

CTID="$DEFAULT_CTID"; HOSTNAME="$DEFAULT_HOSTNAME"
STORAGE="${ROOT_STORAGES[0]}"
for s in "${ROOT_STORAGES[@]}"; do [[ "$s" == "$DEFAULT_STORAGE" ]] && STORAGE="$s"; done
TEMPLATE_STORAGE="${TEMPLATE_STORAGES[0]}"
for s in "${TEMPLATE_STORAGES[@]}"; do [[ "$s" == "$DEFAULT_TEMPLATE_STORAGE" ]] && TEMPLATE_STORAGE="$s"; done
CORES="$DEFAULT_CORES"; MEMORY="$DEFAULT_MEMORY"; SWAP="$DEFAULT_SWAP"; DISK="$DEFAULT_DISK"; BRIDGE="$DEFAULT_BRIDGE"
NET_MODE=dhcp; NET_IP="192.168.1.145/24"; GATEWAY="192.168.1.1"; VLAN_TAG=""; USE_VLAN=0; ONBOOT=1; ENABLE_ROOT_SSH=1
ROOT_PASSWORD=""; PAGE=1

while true; do
while (( PAGE <= 9 )); do
  case $PAGE in
    1)
      if input_page CTID "Container" "Container-ID:" "$CTID"; then
        [[ "$CTID" =~ ^[0-9]+$ ]] || { error_box "Die Container-ID muss eine Zahl sein."; continue; }
        if pct status "$CTID" >/dev/null 2>&1; then error_box "Die Container-ID $CTID ist bereits vergeben."; continue; fi
        ((PAGE++))
      else ((PAGE--)); [[ $PAGE -lt 1 ]] && PAGE=1; fi ;;
    2)
      if input_page HOSTNAME "Container" "Hostname des neuen Containers:" "$HOSTNAME"; then
        [[ "$HOSTNAME" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]] || { error_box "Der Hostname enthält ungültige Zeichen."; continue; }
        ((PAGE++))
      else ((PAGE--)); fi ;;
    3)
      args=(); for s in "${ROOT_STORAGES[@]}"; do args+=("$s" "" "$([[ $s == "$STORAGE" ]] && echo ON || echo OFF)"); done
      if radiolist_page STORAGE "Root-Disk" "Storage für die Container-Root-Disk auswählen:" 18 72 9 "${args[@]}"; then
        [[ -n "$STORAGE" ]] || { error_box "Bitte ein Storage für die Root-Disk auswählen."; continue; }
        ((PAGE++))
      else ((PAGE--)); fi ;;
    4)
      args=(); for s in "${TEMPLATE_STORAGES[@]}"; do args+=("$s" "" "$([[ $s == "$TEMPLATE_STORAGE" ]] && echo ON || echo OFF)"); done
      if radiolist_page TEMPLATE_STORAGE "Debian-Template" "Storage für das Debian-13-Template auswählen:" 18 72 9 "${args[@]}"; then
        [[ -n "$TEMPLATE_STORAGE" ]] || { error_box "Bitte ein Storage für das Debian-Template auswählen."; continue; }
        ((PAGE++))
      else ((PAGE--)); fi ;;
    5)
      FORM=""
      set +e
      FORM="$(wt --title "Ressourcen" --ok-label "Weiter" --cancel-label "Zurück" --extra-button --extra-label "Abbrechen" \
        --form "Ressourcen des LXC-Containers:" 18 72 8 \
        "CPU-Kerne:" 1 1 "$CORES" 1 24 12 0 \
        "RAM in MB:" 2 1 "$MEMORY" 2 24 12 0 \
        "Swap in MB:" 3 1 "$SWAP" 3 24 12 0 \
        "Disk in GB:" 4 1 "$DISK" 4 24 12 0 3>&1 1>&2 2>&3)"; rc=$?
      set -e
      if [[ $rc == 0 ]]; then
        mapfile -t vals <<<"$FORM"; CORES="${vals[0]:-}"; MEMORY="${vals[1]:-}"; SWAP="${vals[2]:-}"; DISK="${vals[3]:-}"
        if [[ ! "$CORES" =~ ^[1-9][0-9]*$ || ! "$MEMORY" =~ ^[1-9][0-9]*$ || ! "$SWAP" =~ ^[0-9]+$ || ! "$DISK" =~ ^[1-9][0-9]*$ ]]; then error_box "Bitte gültige ganze Zahlen eingeben."; continue; fi
        ((PAGE++))
      elif [[ $rc == 1 ]]; then ((PAGE--)); else abort; fi ;;
    6)
      args=(); for b in "${BRIDGES[@]}"; do args+=("$b" "Netzwerk-Bridge"); done
      if menu_page BRIDGE "Netzwerk" "Netzwerk-Bridge auswählen:" 16 72 7 "${args[@]}"; then ((PAGE++)); else ((PAGE--)); fi ;;
    7)
      if menu_page NET_MODE "IP-Konfiguration" "Wie soll der Container seine IPv4-Adresse erhalten?" 14 72 4 \
        dhcp "Automatisch per DHCP" static "Statische IPv4-Adresse"; then
        if [[ "$NET_MODE" == static ]]; then
          if ! input_page NET_IP "Statische IP" "IPv4-Adresse mit Präfix, z. B. 192.168.1.145/24:" "$NET_IP"; then continue; fi
          if ! input_page GATEWAY "Statische IP" "IPv4-Gateway:" "$GATEWAY"; then continue; fi
        fi
        ((PAGE++))
      else ((PAGE--)); fi ;;
    8)
      CHECKS=""
      set +e
      CHECKS="$(wt --title "Optionen" --ok-label "Weiter" --cancel-label "Zurück" --extra-button --extra-label "Abbrechen" \
        --checklist "Gewünschte Optionen auswählen:" 16 72 6 \
        onboot "Container automatisch mit Proxmox starten" "$([[ $ONBOOT == 1 ]] && echo ON || echo OFF)" \
        ssh "Root-Login per SSH-Passwort aktivieren" "$([[ $ENABLE_ROOT_SSH == 1 ]] && echo ON || echo OFF)" \
        vlan "VLAN verwenden" "$([[ $USE_VLAN == 1 ]] && echo ON || echo OFF)" 3>&1 1>&2 2>&3)"; rc=$?
      set -e
      if [[ $rc == 0 ]]; then
        [[ "$CHECKS" == *onboot* ]] && ONBOOT=1 || ONBOOT=0
        [[ "$CHECKS" == *ssh* ]] && ENABLE_ROOT_SSH=1 || ENABLE_ROOT_SSH=0
        if [[ "$CHECKS" == *vlan* ]]; then
          USE_VLAN=1
          if input_page VLAN_TAG "VLAN" "VLAN-ID:" "${VLAN_TAG:-10}"; then
            [[ "$VLAN_TAG" =~ ^[0-9]+$ ]] && ((VLAN_TAG>=1 && VLAN_TAG<=4094)) || { error_box "Die VLAN-ID muss zwischen 1 und 4094 liegen."; continue; }
          else
            continue
          fi
        else
          USE_VLAN=0; VLAN_TAG=""
        fi
        ((PAGE++))
      elif [[ $rc == 1 ]]; then ((PAGE--)); else abort; fi ;;
    9)
      if password_page ROOT_PASSWORD "Root-Passwort" "Root-Passwort für den neuen LXC:"; then
        [[ -n "$ROOT_PASSWORD" ]] || { error_box "Das Passwort darf nicht leer sein."; continue; }
        CONFIRM=""; if ! password_page CONFIRM "Root-Passwort" "Root-Passwort wiederholen:"; then continue; fi
        [[ "$ROOT_PASSWORD" == "$CONFIRM" ]] || { error_box "Die Passwörter stimmen nicht überein."; continue; }
        ((PAGE++))
      else ((PAGE--)); fi ;;
  esac
done

NETWORK_DESC="$NET_MODE über $BRIDGE"
[[ "$NET_MODE" == static ]] && NETWORK_DESC="$NET_IP über $BRIDGE, Gateway $GATEWAY"
[[ -n "$VLAN_TAG" ]] && NETWORK_DESC+=", VLAN $VLAN_TAG"
SUMMARY="MP-Gateway:      $RELEASE_VERSION\nContainer-ID:    $CTID\nHostname:        $HOSTNAME\nCPU / RAM:       $CORES Kerne / $MEMORY MB\nSwap / Disk:     $SWAP MB / $DISK GB\nRoot-Disk:       $STORAGE\nTemplate:        $TEMPLATE_STORAGE\nNetzwerk:        $NETWORK_DESC\nAutostart:       $([[ $ONBOOT == 1 ]] && echo Ja || echo Nein)\nRoot-SSH:        $([[ $ENABLE_ROOT_SSH == 1 ]] && echo aktiviert || echo deaktiviert)"

set +e
wt --title "Zusammenfassung" --yes-label "Installieren" --no-label "Zurück" --extra-button --extra-label "Abbrechen" \
  --yesno "$SUMMARY\n\nContainer jetzt erstellen und MP-Gateway installieren?" 22 78
rc=$?; set -e
if [[ $rc == 1 ]]; then PAGE=8; continue; elif [[ $rc != 0 ]]; then abort; fi
break
done

export CTID HOSTNAME STORAGE TEMPLATE_STORAGE CORES MEMORY SWAP DISK BRIDGE NET_MODE NET_IP GATEWAY VLAN_TAG ONBOOT ENABLE_ROOT_SSH ROOT_PASSWORD RELEASE_VERSION RELEASE_URL

perform_install() {
  # Dateideskriptor 3 bleibt mit dem Dialog-Fortschrittsbalken verbunden.
  # stdout/stderr der eigentlichen Installation gehen ausschließlich ins Log.
  exec 3>&1
  exec >>"$LOG_FILE" 2>&1
  progress() {
    printf '%s\nXXX\n%s\nXXX\n' "$1" "$2" >&3
  }
  progress 3 "Debian-13-Template wird geprüft ..."
  pveam update
  TEMPLATE_NAME="$(pveam available | awk '/debian-13-standard/ && !found {value=$2; found=1} END {if(found) print value}')"
  [[ -n "$TEMPLATE_NAME" ]]
  TEMPLATE_BASENAME="$(basename "$TEMPLATE_NAME")"; TEMPLATE_VOLUME="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE_BASENAME}"
  TEMPLATE_PATH="$(pvesm path "$TEMPLATE_VOLUME" 2>/dev/null || true)"
  if [[ -z "$TEMPLATE_PATH" || ! -f "$TEMPLATE_PATH" ]]; then
    progress 10 "Debian-13-Template wird geladen ..."
    pveam download "$TEMPLATE_STORAGE" "$TEMPLATE_NAME"; TEMPLATE_PATH="$(pvesm path "$TEMPLATE_VOLUME")"
  fi
  progress 20 "LXC $CTID wird erstellt ..."
  NET0="name=eth0,bridge=${BRIDGE},ip=$([[ $NET_MODE == dhcp ]] && echo dhcp || echo "$NET_IP")"
  [[ "$NET_MODE" == static ]] && NET0+=",gw=${GATEWAY}"; [[ -n "$VLAN_TAG" ]] && NET0+=",tag=${VLAN_TAG}"
  pct create "$CTID" "$TEMPLATE_PATH" --hostname "$HOSTNAME" --cores "$CORES" --memory "$MEMORY" --swap "$SWAP" \
    --rootfs "${STORAGE}:${DISK}" --net0 "$NET0" --features nesting=1 --onboot "$ONBOOT" --unprivileged 1 --password "$ROOT_PASSWORD"
  progress 32 "Container wird gestartet ..."; pct start "$CTID"
  progress 38 "Auf Netzwerk wird gewartet ..."
  ready=0; for _ in $(seq 1 60); do pct exec "$CTID" -- bash -c 'ip -4 addr show dev eth0 | grep -q "inet "' && { ready=1; break; }; sleep 2; done
  [[ $ready == 1 ]]
  progress 45 "Grundpakete und MP-Gateway werden installiert ..."
  ROOT_PASSWORD_B64="$(printf %s "$ROOT_PASSWORD" | base64 -w0)"
  progress 55 "MP-Gateway wird im Container eingerichtet ..."
  pct exec "$CTID" -- env RELEASE_URL="$RELEASE_URL" RELEASE_VERSION="$RELEASE_VERSION" ENABLE_ROOT_SSH="$ENABLE_ROOT_SSH" ROOT_PASSWORD_B64="$ROOT_PASSWORD_B64" bash -c '
set -Eeuo pipefail; export DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8
apt-get update; apt-get install -y curl unzip python3 python3-venv ca-certificates openssh-server
rm -rf /root/mp-gateway-install /root/mpgateway.zip; mkdir -p /root/mp-gateway-install; cd /root/mp-gateway-install
curl -fL --retry 3 --retry-delay 2 "$RELEASE_URL" -o /root/mpgateway.zip; unzip -q /root/mpgateway.zip
INSTALL_SCRIPT="$(find /root/mp-gateway-install -type f -path "*/scripts/lxc/install-debian13.sh" -print -quit)"; [[ -n "$INSTALL_SCRIPT" ]]
PROJECT_ROOT="$(cd "$(dirname "$INSTALL_SCRIPT")/../.." && pwd)"; chmod +x "$INSTALL_SCRIPT"; bash "$INSTALL_SCRIPT"
ROOT_PASSWORD="$(printf %s "$ROOT_PASSWORD_B64" | base64 -d)"; printf "root:%s\n" "$ROOT_PASSWORD" | chpasswd; unset ROOT_PASSWORD ROOT_PASSWORD_B64
install -D -o root -g root -m 0755 "$PROJECT_ROOT/scripts/lxc/mpgateway-admin" /usr/local/lib/mp-gateway/mpgateway-admin
install -o root -g root -m 0644 "$PROJECT_ROOT/packaging/systemd/mp-gateway.service" /etc/systemd/system/mp-gateway.service
systemctl daemon-reload; systemctl restart mp-gateway
if [[ "$ENABLE_ROOT_SSH" == 1 ]]; then /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable; else /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable; fi
systemctl restart mp-gateway; sleep 4; systemctl is-active --quiet mp-gateway
'
  progress 95 "Installation wird geprüft ..."
  IP="$(pct exec "$CTID" -- hostname -I | awk '{print $1}')"; echo "$IP" >"${LOG_FILE}.ip"
  progress 100 "Installation abgeschlossen."
}

set +e
perform_install | wt --title "Installation" --gauge "MP-Gateway wird installiert ..." 10 76 0
rc=${PIPESTATUS[0]}; set -e
unset ROOT_PASSWORD
if [[ $rc != 0 ]]; then
  tailtext="$(tail -n 18 "$LOG_FILE" 2>/dev/null || true)"
  wt --title "Installation fehlgeschlagen" --msgbox "Die Installation wurde mit Fehler $rc beendet.\n\nLetzte Meldungen:\n$tailtext\n\nVollständiges Protokoll:\n$LOG_FILE" 28 88
  exit "$rc"
fi
IP="$(cat "${LOG_FILE}.ip")"
RESULT_FILE="/root/mp-gateway-${RELEASE_VERSION}-installation.txt"
ROOT_SSH_TEXT="$([[ $ENABLE_ROOT_SSH == 1 ]] && echo aktiviert || echo deaktiviert)"
cat >"$RESULT_FILE" <<EOF
MP-Gateway $RELEASE_VERSION wurde erfolgreich installiert.

Container-ID: $CTID
IP-Adresse:   $IP
Weboberfläche: http://${IP}:8099
Root-SSH:     $ROOT_SSH_TEXT
Installationsprotokoll: $LOG_FILE
EOF

wt --title "Installation abgeschlossen" --msgbox \
"MP-Gateway $RELEASE_VERSION wurde erfolgreich installiert.\n\nContainer-ID: $CTID\nIP-Adresse:   $IP\nWeboberfläche:\nhttp://${IP}:8099\n\nRoot-SSH: $ROOT_SSH_TEXT\n\nNach OK werden diese Angaben noch einmal als kopierbarer Shelltext angezeigt.\nZusätzlich gespeichert unter:\n$RESULT_FILE" 22 82

clear
cat "$RESULT_FILE"
printf '\nDie Angaben oben können jetzt im Proxmox-Terminal markiert und kopiert werden.\n'
