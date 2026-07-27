#!/usr/bin/env bash
set -Eeuo pipefail

# MP-Gateway Komplettinstaller für Proxmox VE 9 / Debian 13 LXC
# Ausführung ausschließlich auf dem Proxmox-Host als root.

REPO="stephanmrst/MP-Gatway_LXC"
RELEASE_TAG="MP-Gateway"
DEFAULT_HOSTNAME="mp-gateway"
DEFAULT_CORES=2
DEFAULT_MEMORY=1024
DEFAULT_SWAP=512
DEFAULT_DISK=8
DEFAULT_BRIDGE="vmbr0"
DEFAULT_PORT=8099
TMP_DIR="$(mktemp -d /tmp/mp-gateway-lxc.XXXXXX)"
CREATED_CT=0
CTID=""

C_RESET='\033[0m'
C_BLUE='\033[1;34m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'
C_RED='\033[1;31m'

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

on_error() {
    local exit_code=$?
    echo -e "\n${C_RED}[FEHLER]${C_RESET} Installation in Zeile ${BASH_LINENO[0]} abgebrochen."
    if [[ "$CREATED_CT" == "1" && -n "$CTID" ]]; then
        echo -e "Der teilweise angelegte Container ${C_YELLOW}${CTID}${C_RESET} bleibt zur Diagnose erhalten."
        echo "Entfernen bei Bedarf mit: pct stop $CTID 2>/dev/null; pct destroy $CTID --purge 1"
    fi
    exit "$exit_code"
}
trap on_error ERR

log()  { echo -e "\n${C_BLUE}[MP-Gateway]${C_RESET} $*"; }
ok()   { echo -e "${C_GREEN}[OK]${C_RESET} $*"; }
warn() { echo -e "${C_YELLOW}[HINWEIS]${C_RESET} $*"; }
die()  { echo -e "${C_RED}[FEHLER]${C_RESET} $*" >&2; exit 1; }

prompt_default() {
    local prompt="$1" default="$2" value
    read -r -p "$prompt [$default]: " value
    printf '%s' "${value:-$default}"
}

prompt_yes_no() {
    local prompt="$1" default="${2:-n}" answer suffix
    if [[ "$default" == "j" ]]; then suffix="J/n"; else suffix="j/N"; fi
    read -r -p "$prompt [$suffix]: " answer
    answer="${answer:-$default}"
    [[ "$answer" =~ ^[JjYy]$ ]]
}

choose_from_list() {
    local title="$1" default="$2"
    shift 2
    local options=("$@") choice i
    ((${#options[@]} > 0)) || die "Keine Auswahlmöglichkeiten für $title gefunden."

    echo "$title:" >&2
    for i in "${!options[@]}"; do
        if [[ "${options[$i]}" == "$default" ]]; then
            printf '  %d) %s (Standard)\n' "$((i+1))" "${options[$i]}" >&2
        else
            printf '  %d) %s\n' "$((i+1))" "${options[$i]}" >&2
        fi
    done
    read -r -p "Auswahl: " choice
    if [[ -z "$choice" ]]; then
        printf '%s' "$default"
    elif [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#options[@]} )); then
        printf '%s' "${options[$((choice-1))]}"
    else
        die "Ungültige Auswahl."
    fi
}

wait_for_container() {
    local tries=60
    while ((tries-- > 0)); do
        if pct exec "$CTID" -- true >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    return 1
}

get_container_ipv4() {
    pct exec "$CTID" -- bash -lc "ip -4 -o addr show dev eth0 2>/dev/null | awk '{print \\$4}' | cut -d/ -f1 | head -n1" 2>/dev/null || true
}

[[ $EUID -eq 0 ]] || die "Bitte direkt auf dem Proxmox-Host als root ausführen."
command -v pveversion >/dev/null || die "Das ist offenbar kein Proxmox-VE-Host (pveversion fehlt)."
command -v pct >/dev/null || die "pct wurde nicht gefunden."
command -v pveam >/dev/null || die "pveam wurde nicht gefunden."

PVE_VERSION="$(pveversion | head -n1)"
echo -e "${C_BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       MP-Gateway – Debian-13-LXC-Installer          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${C_RESET}"
echo "Erkannt: $PVE_VERSION"
echo "Dieser Installer legt einen neuen unprivilegierten LXC an und installiert"
echo "das Release '$RELEASE_TAG' aus github.com/$REPO."

if ! [[ "$PVE_VERSION" =~ pve-manager/9\. ]]; then
    warn "Referenzplattform ist Proxmox VE 9. Fortsetzen erfolgt auf eigene Verantwortung."
    prompt_yes_no "Trotzdem fortfahren?" "n" || exit 0
fi

for cmd in curl python3 awk sed grep sort head; do
    command -v "$cmd" >/dev/null || die "Benötigtes Programm fehlt auf dem Host: $cmd"
done

NEXT_ID="$(pvesh get /cluster/nextid 2>/dev/null || true)"
NEXT_ID="${NEXT_ID:-200}"
CTID="$(prompt_default "CT-ID" "$NEXT_ID")"
[[ "$CTID" =~ ^[0-9]+$ ]] || die "CT-ID muss numerisch sein."
if pct status "$CTID" >/dev/null 2>&1; then
    die "CT-ID $CTID ist bereits vergeben."
fi

HOSTNAME="$(prompt_default "Hostname" "$DEFAULT_HOSTNAME")"
[[ "$HOSTNAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]] || die "Ungültiger Hostname."
CORES="$(prompt_default "CPU-Kerne" "$DEFAULT_CORES")"
MEMORY="$(prompt_default "Arbeitsspeicher in MB" "$DEFAULT_MEMORY")"
SWAP="$(prompt_default "Swap in MB" "$DEFAULT_SWAP")"
DISK="$(prompt_default "Festplattengröße in GB" "$DEFAULT_DISK")"
for numeric in "$CORES" "$MEMORY" "$SWAP" "$DISK"; do
    [[ "$numeric" =~ ^[0-9]+$ ]] || die "Ressourcenwerte müssen numerisch sein."
done

mapfile -t ROOTFS_STORAGES < <(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 && $3=="active" {print $1}' | sort -u)
((${#ROOTFS_STORAGES[@]} > 0)) || die "Kein aktiver Proxmox-Speicher mit Inhaltstyp 'Container' gefunden."
DEFAULT_ROOTFS="local-lvm"
printf '%s\n' "${ROOTFS_STORAGES[@]}" | grep -qx "$DEFAULT_ROOTFS" || DEFAULT_ROOTFS="${ROOTFS_STORAGES[0]}"
ROOTFS_STORAGE="$(choose_from_list "Speicher für die LXC-Festplatte" "$DEFAULT_ROOTFS" "${ROOTFS_STORAGES[@]}")"

mapfile -t TEMPLATE_STORAGES < <(pvesm status -content vztmpl 2>/dev/null | awk 'NR>1 && $3=="active" {print $1}' | sort -u)
((${#TEMPLATE_STORAGES[@]} > 0)) || die "Kein aktiver Speicher mit Inhaltstyp 'Container template' gefunden."
DEFAULT_TEMPLATE_STORAGE="local"
printf '%s\n' "${TEMPLATE_STORAGES[@]}" | grep -qx "$DEFAULT_TEMPLATE_STORAGE" || DEFAULT_TEMPLATE_STORAGE="${TEMPLATE_STORAGES[0]}"
TEMPLATE_STORAGE="$(choose_from_list "Speicher für das Debian-Template" "$DEFAULT_TEMPLATE_STORAGE" "${TEMPLATE_STORAGES[@]}")"

BRIDGE="$(prompt_default "Netzwerk-Bridge" "$DEFAULT_BRIDGE")"
echo
echo "Netzwerkkonfiguration:"
echo "  1) DHCP (empfohlen für den ersten Start; im Router fest zuweisen)"
echo "  2) Statische IPv4-Adresse"
read -r -p "Auswahl [1]: " NET_CHOICE
NET_CHOICE="${NET_CHOICE:-1}"

if [[ "$NET_CHOICE" == "2" ]]; then
    read -r -p "IPv4-Adresse mit Präfix, z. B. 192.168.1.50/24: " STATIC_IP
    read -r -p "Gateway, z. B. 192.168.1.1: " GATEWAY
    [[ "$STATIC_IP" == */* ]] || die "Die statische Adresse benötigt ein CIDR-Präfix, z. B. /24."
    [[ -n "$GATEWAY" ]] || die "Gateway darf nicht leer sein."
    NET_CONFIG="name=eth0,bridge=$BRIDGE,ip=$STATIC_IP,gw=$GATEWAY,type=veth,firewall=1"
else
    NET_CONFIG="name=eth0,bridge=$BRIDGE,ip=dhcp,type=veth,firewall=1"
fi

SSH_KEY_FILE=""
if [[ -s /root/.ssh/authorized_keys ]] && prompt_yes_no "Vorhandene SSH-Schlüssel des Proxmox-root in den LXC übernehmen?" "j"; then
    SSH_KEY_FILE="/root/.ssh/authorized_keys"
fi

ENABLE_ROOT_PASSWORD=0
if prompt_yes_no "Root-Login per SSH-Passwort nach der Installation aktivieren?" "j"; then
    ENABLE_ROOT_PASSWORD=1
    while true; do
        read -r -s -p "Neues root-Passwort für den LXC: " ROOT_PASSWORD; echo
        read -r -s -p "Passwort wiederholen: " ROOT_PASSWORD_2; echo
        [[ -n "$ROOT_PASSWORD" ]] || { warn "Passwort darf nicht leer sein."; continue; }
        [[ "$ROOT_PASSWORD" == "$ROOT_PASSWORD_2" ]] || { warn "Passwörter stimmen nicht überein."; continue; }
        break
    done
else
    ROOT_PASSWORD=""
fi

PROTECTION=0
prompt_yes_no "Löschschutz für den fertigen LXC aktivieren?" "j" && PROTECTION=1

cat <<SUMMARY

──────────────────── Zusammenfassung ────────────────────
CT-ID:             $CTID
Hostname:          $HOSTNAME
CPU / RAM / Swap:  $CORES Kerne / $MEMORY MB / $SWAP MB
Festplatte:        $DISK GB auf $ROOTFS_STORAGE
Template-Speicher: $TEMPLATE_STORAGE
Netzwerk:          $NET_CONFIG
Autostart:         ja
Unprivilegiert:    ja
Root-SSH-Passwort: $([[ "$ENABLE_ROOT_PASSWORD" == 1 ]] && echo aktiviert || echo deaktiviert)
Löschschutz:       $([[ "$PROTECTION" == 1 ]] && echo aktiviert || echo deaktiviert)
─────────────────────────────────────────────────────────
SUMMARY
prompt_yes_no "Installation jetzt starten?" "j" || exit 0

log "Aktualisiere Liste der verfügbaren LXC-Templates"
pveam update >/dev/null
AVAILABLE_TEMPLATE="$(pveam available --section system | awk '{print $2}' | grep -E '^debian-13.*standard.*_amd64\.tar\.(zst|gz|xz)$' | sort -V | tail -n1 || true)"
[[ -n "$AVAILABLE_TEMPLATE" ]] || die "Kein Debian-13-Standardtemplate in pveam gefunden."

DOWNLOADED_TEMPLATE="$(pveam list "$TEMPLATE_STORAGE" 2>/dev/null | awk -v t="$AVAILABLE_TEMPLATE" '$1 ~ t {print $1; exit}')"
if [[ -z "$DOWNLOADED_TEMPLATE" ]]; then
    log "Lade Debian-13-Template $AVAILABLE_TEMPLATE herunter"
    pveam download "$TEMPLATE_STORAGE" "$AVAILABLE_TEMPLATE"
    TEMPLATE_REF="$TEMPLATE_STORAGE:vztmpl/$AVAILABLE_TEMPLATE"
else
    TEMPLATE_REF="$DOWNLOADED_TEMPLATE"
    ok "Debian-13-Template ist bereits vorhanden: $TEMPLATE_REF"
fi

log "Lade MP-Gateway-Releaseinformationen"
RELEASE_JSON="$TMP_DIR/release.json"
curl -fsSL --retry 3 --connect-timeout 15 \
    -H 'Accept: application/vnd.github+json' \
    -H 'X-GitHub-Api-Version: 2022-11-28' \
    "https://api.github.com/repos/$REPO/releases/tags/$RELEASE_TAG" \
    -o "$RELEASE_JSON"

readarray -t ASSET_INFO < <(python3 - "$RELEASE_JSON" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    release = json.load(fh)
assets = [a for a in release.get("assets", []) if a.get("name", "").lower().endswith(".zip")]
if not assets:
    raise SystemExit("Im GitHub-Release wurde keine ZIP-Datei gefunden.")
assets.sort(key=lambda a: (
    "debian13" not in a["name"].lower(),
    "lxc" not in a["name"].lower(),
    "stable" not in a["name"].lower(),
    a["name"].lower(),
))
a = assets[0]
print(a["name"])
print(a["browser_download_url"])
print(release.get("name") or release.get("tag_name") or "MP-Gateway")
PY
)
ASSET_NAME="${ASSET_INFO[0]}"
ASSET_URL="${ASSET_INFO[1]}"
RELEASE_NAME="${ASSET_INFO[2]}"
ZIP_FILE="$TMP_DIR/$ASSET_NAME"
log "Lade $RELEASE_NAME – $ASSET_NAME"
curl -fL --retry 3 --connect-timeout 15 "$ASSET_URL" -o "$ZIP_FILE"
unzip -tq "$ZIP_FILE" >/dev/null || die "Das heruntergeladene Release-ZIP ist beschädigt."

log "Lege unprivilegierten Debian-13-LXC $CTID an"
CREATE_ARGS=(
    "$CTID" "$TEMPLATE_REF"
    --hostname "$HOSTNAME"
    --ostype debian
    --arch amd64
    --unprivileged 1
    --cores "$CORES"
    --memory "$MEMORY"
    --swap "$SWAP"
    --rootfs "$ROOTFS_STORAGE:$DISK"
    --net0 "$NET_CONFIG"
    --onboot 1
    --startup "order=30,up=15,down=60"
    --timezone host
    --features "nesting=0,keyctl=0"
    --tags "mp-gateway;debian13"
    --description "MP-Gateway Stable auf Debian 13 – automatisch installiert"
    --protection 0
)
if [[ -n "$SSH_KEY_FILE" ]]; then
    CREATE_ARGS+=(--ssh-public-keys "$SSH_KEY_FILE")
fi
pct create "${CREATE_ARGS[@]}"
CREATED_CT=1

log "Starte LXC"
pct start "$CTID"
wait_for_container || die "Der LXC wurde nicht rechtzeitig betriebsbereit."
ok "Container läuft"

log "Warte auf Netzwerk und DNS im Container"
for _ in {1..60}; do
    if pct exec "$CTID" -- bash -lc 'getent hosts deb.debian.org >/dev/null 2>&1'; then
        break
    fi
    sleep 2
done
pct exec "$CTID" -- bash -lc 'getent hosts deb.debian.org >/dev/null 2>&1' || die "Der Container erreicht deb.debian.org nicht. Bitte Bridge, DHCP, Gateway und DNS prüfen."

if [[ "$ENABLE_ROOT_PASSWORD" == 1 ]]; then
    log "Setze root-Passwort im LXC"
    printf 'root:%s\n' "$ROOT_PASSWORD" | pct exec "$CTID" -- chpasswd
    unset ROOT_PASSWORD ROOT_PASSWORD_2
fi

log "Übertrage MP-Gateway-Release in den LXC"
pct exec "$CTID" -- mkdir -p /root/mp-gateway-install
pct push "$CTID" "$ZIP_FILE" "/root/mp-gateway-install/$ASSET_NAME"

log "Entpacke und installiere MP-Gateway im LXC"
pct exec "$CTID" -- bash -lc "
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends unzip ca-certificates
cd /root/mp-gateway-install
rm -rf package
mkdir package
unzip -q '$ASSET_NAME' -d package
INSTALLER=\"\$(find package -type f -path '*/scripts/lxc/install-debian13.sh' -print -quit)\"
if [[ -z \"\$INSTALLER\" ]]; then
    echo 'scripts/lxc/install-debian13.sh wurde im Release nicht gefunden.' >&2
    exit 1
fi
chmod +x \"\$INSTALLER\"
\"\$INSTALLER\"
"

if [[ "$ENABLE_ROOT_PASSWORD" == 1 ]]; then
    log "Aktiviere Root-Login per SSH-Passwort"
    pct exec "$CTID" -- /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password enable
else
    log "Root-Login per SSH-Passwort bleibt deaktiviert"
    pct exec "$CTID" -- /usr/local/lib/mp-gateway/mpgateway-admin ssh-root-password disable
fi

log "Prüfe MP-Gateway-Dienst"
pct exec "$CTID" -- systemctl is-active --quiet mp-gateway
pct exec "$CTID" -- systemctl is-enabled --quiet mp-gateway

if [[ "$PROTECTION" == 1 ]]; then
    pct set "$CTID" --protection 1 >/dev/null
fi

CONTAINER_IP=""
for _ in {1..30}; do
    CONTAINER_IP="$(get_container_ipv4)"
    [[ -n "$CONTAINER_IP" ]] && break
    sleep 2
done

CREATED_CT=0
ok "MP-Gateway wurde vollständig installiert."
echo
echo -e "${C_GREEN}╔══════════════════════════════════════════════════════╗${C_RESET}"
echo -e "${C_GREEN}║                  INSTALLATION FERTIG                ║${C_RESET}"
echo -e "${C_GREEN}╚══════════════════════════════════════════════════════╝${C_RESET}"
echo "LXC:            $CTID ($HOSTNAME)"
echo "IP-Adresse:     ${CONTAINER_IP:-noch nicht ermittelt}"
echo "Weboberfläche:  http://${CONTAINER_IP:-LXC-IP}:$DEFAULT_PORT"
echo "Konsole:        pct enter $CTID"
echo "Dienststatus:   pct exec $CTID -- mpgateway status"
echo "Live-Logs:      pct exec $CTID -- mpgateway logs"
echo "Backup:         pct exec $CTID -- mpgateway backup"
if [[ "$ENABLE_ROOT_PASSWORD" == 1 ]]; then
    echo "SSH:            ssh root@${CONTAINER_IP:-LXC-IP}"
else
    echo "SSH-Passwort:   deaktiviert; in MP-Gateway-Einstellungen einschaltbar"
fi
echo
echo "Bitte danach die MP-Gateway-Konfiguration einspielen und die Adapter schrittweise aktivieren."
