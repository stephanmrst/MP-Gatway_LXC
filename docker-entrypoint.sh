#!/bin/sh
set -eu

SOURCE_DIR="/opt/mpgateway-source"
APP_DIR="${MQTT2LOX_APP_ROOT:-/mpgateway}"
CONFIG_DIR="${MQTT2LOX_CONFIG_DIR:-$APP_DIR/config}"
DATA_DIR="${MQTT2LOX_DATA_DIR:-$APP_DIR/data}"
BACKUP_DIR="${MQTT2LOX_BACKUP_DIR:-$APP_DIR/backups}"

mkdir -p "$APP_DIR" "$CONFIG_DIR" "$DATA_DIR" "$BACKUP_DIR" "$APP_DIR/logs"

# Anwendungscode aus dem Image nur übernehmen, wenn keine neuere Web-Update-Version
# im persistenten Volume liegt. So bleiben Updates über die Oberfläche erhalten.
IMAGE_VERSION="$(cat "$SOURCE_DIR/VERSION" 2>/dev/null || echo 0.0.0)"
APP_VERSION="$(cat "$APP_DIR/VERSION" 2>/dev/null || echo 0.0.0)"
SYNC_IMAGE=1
if [ -f "$APP_DIR/.update-managed.json" ] && [ -f "$APP_DIR/VERSION" ]; then
    NEWEST="$(printf '%s\n%s\n' "$IMAGE_VERSION" "$APP_VERSION" | sort -V | tail -n 1)"
    if [ "$NEWEST" = "$APP_VERSION" ]; then
        SYNC_IMAGE=0
        echo "MP-Gateway: persistente Web-Update-Version $APP_VERSION bleibt aktiv (Image: $IMAGE_VERSION)."
    fi
fi

if [ "$SYNC_IMAGE" -eq 1 ]; then
    echo "MP-Gateway: aktualisiere Anwendungscode aus dem Container-Image $IMAGE_VERSION ..."
    for path in app static templates docs tests; do
        rm -rf "$APP_DIR/$path"
        if [ -e "$SOURCE_DIR/$path" ]; then
            cp -a "$SOURCE_DIR/$path" "$APP_DIR/$path"
        fi
    done

    for file in requirements.txt VERSION update_manifest.json Dockerfile docker-compose.yml DOCKER.md GITHUB_RELEASE.md CHANGELOG.md AGENTS.md ARCHITECTURE_REVIEW.md BLUEPRINT_PLAN.md CLEANUP_REPORT.md KNX_RUNTIME_MIGRATION_PLAN.md LEGACY_REMOVAL_PLAN.md MIGRATION.md ROADMAP.md RUNTIME_CONTEXT_PLAN.md TODO.md .gitignore .gitattributes; do
        if [ -e "$SOURCE_DIR/$file" ]; then
            cp -a "$SOURCE_DIR/$file" "$APP_DIR/$file"
        fi
    done
    rm -f "$APP_DIR/.update-managed.json"
fi
cp "$SOURCE_DIR/.image-requirements.sha256" "$APP_DIR/.image-requirements.sha256.image"

# Alte Mapping-Dateien werden einmalig aus dem aktiven Config-Verzeichnis entfernt
# und sicher archiviert. Die V34-Runtime liest ausschließlich objects.json.
LEGACY_ARCHIVE="$BACKUP_DIR/legacy_v33_disabled"
mkdir -p "$LEGACY_ARCHIVE"
for file in topic_config.json mqtt2lox.json mqtt2udp_config.json udp2mqtt.json mqtt2knx.json knx2mqtt.json udp2knx.json knx2lox.json; do
    if [ -f "$CONFIG_DIR/$file" ]; then
        mv "$CONFIG_DIR/$file" "$LEGACY_ARCHIVE/$file"
        echo "MP-Gateway: Legacy-Konfiguration deaktiviert und archiviert: $file"
    fi
done

# Abhängigkeiten nur bei geänderter requirements.txt nachziehen.
if [ -f "$APP_DIR/requirements.txt" ]; then
    CURRENT_HASH="$(sha256sum "$APP_DIR/requirements.txt" | awk '{print $1}')"
    INSTALLED_HASH="$(cat "$APP_DIR/.requirements.sha256" 2>/dev/null || true)"
    if [ "$CURRENT_HASH" != "$INSTALLED_HASH" ]; then
        echo "MP-Gateway: requirements.txt geändert, installiere Abhängigkeiten ..."
        python -m pip install -r "$APP_DIR/requirements.txt"
        printf '%s\n' "$CURRENT_HASH" > "$APP_DIR/.requirements.sha256"
    fi
fi

cd "$APP_DIR"
exec "$@"
