# Legacy Removal Plan 32.7.0

Stand: Phase J umgesetzt. Der alte Legacy-Dateipfad ist entfernt; der bisherige Anwendungskern liegt als `app/core.py` innerhalb des App-Packages.

## Abschluss 32.7.0

- `app/main.py` startet ueber `from app import create_app`.
- `app/__init__.py` ist die zentrale App Factory.
- `app/engine/port.py` enthaelt nur noch Startup-/Dependency-Checks, Projektpfade und Versionsinformationen.
- Der bisherige Kern wurde nach `app/core.py` uebernommen.
- Blueprints delegieren intern auf `current_app.extensions["app_core"]`.
- Es gibt keinen Importlib-Dateilader fuer den alten Dateipfad mehr.
- Naechste Arbeit: `app/core.py` weiter in Templates, Utils, Services und kleinere Route-Handler aufteilen.

Phase A wurde in 32.4.9 vorbereitet: `app/routes/`, Blueprint-Platzhaltermodule, `app/extensions.py` und eine vorsichtige `app/__init__.py` existieren.

Phase B wurde in 32.5.0 begonnen: `app/routes/dashboard.py` ist als erster echter Blueprint registriert. Die Routen `/`, `/dashboard_embed`, `/shell_status`, `/live_log`, `/live_log_page`, `/live_log_data`, `/clear_log` und `/clear_monitor` werden nicht mehr direkt in `app/core.py` registriert, delegieren aber weiterhin auf die bestehenden Legacy-Handler.

Phase C wurde in 32.5.1 begonnen: `app/routes/config.py`, `app/routes/backup.py` und `app/routes/objects.py` registrieren die Config-, Backup- und Object-Routen. Die entsprechenden Routen werden nicht mehr direkt in `app/core.py` registriert, delegieren aber weiterhin auf die bestehenden Legacy-Handler.

Phase D Teil 1 wurde in 32.6.0 begonnen: `app/routes/mqtt.py` registriert MQTT Hub, MQTT Monitor, Monitor-Datenrouten, Topic Explorer, Topic Manager, Brokerverwaltung und Broker-Test. Die entsprechenden Routen werden nicht mehr direkt in `app/core.py` registriert, delegieren aber weiterhin auf die bestehenden Legacy-Handler.

Phase D Teil 2 wurde in 32.6.1 begonnen: `app/routes/udp.py` registriert MQTT->UDP, UDP->MQTT, UDP Input, UDP Presets und UDP Discovery. Die entsprechenden Routen werden nicht mehr direkt in `app/core.py` registriert, delegieren aber weiterhin auf die bestehenden Legacy-Handler.

Phase D Teil 3 wurde in 32.6.2 begonnen: `app/routes/loxone.py` registriert MQTT->Loxone, Speichern, Test und Live-Daten. Die entsprechenden Routen werden nicht mehr direkt in `app/core.py` registriert, delegieren aber weiterhin auf die bestehenden Legacy-Handler.

Phase D Teil 4 wurde in 32.6.3 begonnen: `app/routes/influx.py` registriert Influx-Test, Influx Explorer, einzelnes Loeschen und Mehrfach-Loeschen. Die entsprechenden Routen werden nicht mehr direkt in `app/core.py` registriert, delegieren aber weiterhin auf die bestehenden Legacy-Handler.

Phase E wurde in 32.6.4 begonnen: `app/routes/api.py` registriert globale Suche, Suchseite, Konfliktpruefung und Konfliktseite. Domain-nahe Data-/JSON-Routen bleiben bei ihren Blueprints oder im geplanten Domain-/Event-/System-Bereich.

Phase F wurde in 32.6.5 begonnen: `app/routes/events.py` registriert alle SSE/Eventstream-Routen. Der generische SSE-Helper liegt jetzt in `app/utils/sse.py`; Eventnamen, Payloads und Keepalive-Verhalten bleiben unveraendert.

Phase G Teil 1 wurde in 32.6.6 begonnen: `app/routes/knx.py` registriert KNX Hub, KNX Settings, MQTT->KNX, UDP->KNX, KNX->MQTT und KNX->Loxone. KNX Monitor, Listener und xknx-nahe Runtime bleiben im Legacy-Core.

Phase G Teil 2 wurde in 32.6.7 begonnen: `app/routes/knx.py` registriert zusaetzlich KNX Monitor, KNX Monitor Data, KNX Monitor Influx-Config und Listener-Start. Die xknx-/AsyncIO-/Thread-Implementierung bleibt unveraendert angebunden.

Phase H wurde in 32.6.8 begonnen: `app/routes/system.py` registriert Bridge Start/Stop, Test-Routen und interne Broker-Routen. Bridge-Start/Stop-Helfer liegen in `app/engine/bridge.py`; die eigentliche Bridge-Logik bleibt unveraendert angebunden.

Phase J wurde in 32.7.0 umgesetzt: der alte Dateipfad wurde entfernt, die App Factory ist aktiv und die App startet ueber `app/__init__.py`.

Dies ist weiterhin der Migrationsplan. Dashboard-, Config-, Backup-, Object-, MQTT-, UDP-, Loxone-, Influx-, API/Such-, Event-, KNX- und System-Route-Registrierungen wurden ausgelagert; Handler-Logik, UI und Dateien wurden nicht verschoben.

## Ziel

`app/core.py` soll langfristig vollstaendig entfernt werden. Dafuer muss die Anwendung von einer App-Core-Datei mit Flask-App, Routen, HTML-Strings, Runtime-Orchestrierung und Hilfsfunktionen zu einer normalen Flask-App mit App Factory, Blueprints, Templates, Static Assets, Services, RuntimeContext und Utils migriert werden.

## Aktuelle Startstruktur

```text
app/main.py
  -> importiert create_app aus app
  -> startet app.run(...)

app/__init__.py
  -> zentrale App Factory
  -> fuehrt Startup-/Dependency-Checks aus
  -> importiert app/core.py direkt
  -> registriert Blueprints und RuntimeContext

app/engine/port.py
  -> setzt APP_VERSION, Projektpfade und optionale Dependency-Stubs

app/core.py
  -> erzeugt Flask-App direkt mit Flask(__name__)
  -> erzeugt runtime_context
  -> enthaelt 117 Routen
  -> enthaelt 276 Top-Level-Funktionen
  -> enthaelt grosse HTML-/JS-Strings und render_template_string-Aufrufe
  -> orchestriert Bridge, Listener, SSE und Runtime-Callbacks
```

## Was `app/core.py` Noch Erfuellt

| Bereich | Aktueller Inhalt | Zielort |
|---|---|---|
| Flask-App | `app = Flask(__name__)`, Config, UTF-8 Hook, Route-Dekoratoren | `app/__init__.py` mit `create_app()` |
| App-Shell | `APP_LAYOUT`, `SHELL_LAYOUT`, Sidebar, Footer, `render_layout` | `app/templates/layouts/`, `app/services/template.py`, spaeter `app/utils/html.py` |
| Dashboard | Dashboard HTML, Statuskarten, Shell-Status | `app/routes/dashboard.py` |
| Settings | Core/MQTT/Influx/KKNX/Sidebar/Plugin-Save-Routen | `app/routes/config.py`, `app/routes/system.py` |
| Bridge Runtime | Start/Stop, Bridge-Thread, Loxone/MQTT/UDP/KNX-Verkettung | spaeter `app/engine/bridge.py`, `app/routes/system.py` |
| Live Log | Live-Log UI, JSON, SSE | `app/routes/events.py`, `app/routes/system.py` |
| MQTT | MQTT Hub, Monitor, Topic Manager, Broker-Seiten | `app/routes/mqtt.py` |
| UDP | MQTT->UDP, UDP->MQTT, UDP Input, Discovery, Presets | `app/routes/udp.py` |
| Loxone | MQTT->Loxone Seiten, Test, Explorer-/Options-Anbindung | `app/routes/loxone.py` |
| KNX | KNX Hub, Mappings, Monitor, Listener-Start, KNX Settings | `app/routes/knx.py` |
| Influx | Settings-Test, Explorer, Delete-Routen, Monitor-Inline-Config | `app/routes/influx.py` |
| Objects | Objektmanager-Seiten und Aktionen | `app/routes/objects.py` |
| Backup/Templates | Backup, Restore, Template Import/Export | `app/routes/backup.py`, `app/routes/config.py` |
| API/JSON | `*_data`, Status, Monitor Settings, Discovery Status | `app/routes/api.py` oder Domain-Blueprints |
| Events/SSE | `/events/status`, `/events/live_log`, `/events/mqtt_monitor`, `/events/knx_monitor` | `app/routes/events.py` |

## Routen In Legacy

Aktuell liegen 117 Flask-Routen in `app/core.py`.

| Ziel-Blueprint | Routen |
|---|---|
| `dashboard` | `/`, `/dashboard_embed`, `/shell_status`, `/live_log`, `/live_log_page`, `/live_log_data`, `/clear_log`, `/clear_monitor` |
| `config` | `/settings`, `/settings_embed`, `/core_settings_embed`, `/mqtt_settings_embed`, `/influx_settings_embed`, `/save`, `/save_core`, `/save_mqtt`, `/save_influx`, `/sidebar_links/save`, `/plugins`, `/plugins/save` |
| `system` | `/start`, `/stop`, `/test/loxone`, `/test/mqtt`, `/internal_broker/save`, `/internal_broker/start`, `/internal_broker/stop`, `/internal_broker/status`, spaeter `/startup_status` aus `app/engine/port.py` |
| `mqtt` | `/mqtt`, `/monitor`, `/monitor_data`, `/monitor_settings`, `/monitor_topic_config`, `/monitor/influx_topic`, `/monitor/influx_json_key`, `/monitor/influx_json_key_type`, `/monitor/favorite`, `/monitor/alias`, `/topics`, `/topics_data`, `/topics/save`, `/topics2`, `/topics2/data`, `/topics2/save`, `/mqtt_brokers`, `/mqtt_brokers/save`, `/test/mqtt_broker/<int:index>` |
| `loxone` | `/mqtt2lox`, `/mqtt2lox/save`, `/mqtt2lox/test/<int:index>`, `/mqtt2lox_data` |
| `udp` | `/mqtt2udp`, `/mqtt2udp/save`, `/mqtt2udp/test/<int:index>`, `/mqtt2udp_data`, `/mqtt2udp/copy/<int:index>`, `/udp_presets`, `/udp_presets/save`, `/udp2mqtt`, `/udp2mqtt/save`, `/udp2mqtt/test/<int:index>`, `/udp2mqtt_data`, `/udp_input`, `/udp_input/save`, `/udp_input/test`, `/udp_input_data`, `/udp_discovery_status`, `/udp_discovery_toggle` |
| `knx` | `/knx`, `/knx_settings_embed`, `/knx/save`, `/knx/test`, `/mqtt2knx`, `/mqtt2knx/save`, `/mqtt2knx/test/<int:index>`, `/mqtt2knx_data`, `/udp2knx`, `/udp2knx/save`, `/udp2knx/test/<int:index>`, `/udp2knx_data`, `/knx2mqtt`, `/knx2mqtt/save`, `/knx2mqtt_data`, `/knx2lox`, `/knx2lox/save`, `/knx2lox_data`, `/knx_monitor`, `/knx_monitor_data`, `/knx_monitor/influx`, `/knx_monitor/influx_type`, `/knx_monitor/influx_topic`, `/knx_listener_start` |
| `influx` | `/test/influx`, `/influx_explorer`, `/influx_explorer/delete`, `/influx_explorer/delete_selected` |
| `objects` | `/objects`, `/objects/edit/<object_id>`, `/objects/sync_from_mappings`, `/objects/rebuild_mappings`, `/objects/save`, `/objects/delete`, `/objects/delete_all` |
| `backup` | `/backup`, `/restore` |
| `api` | `/global_search`, `/global_search_page`, `/conflicts`, `/conflicts_page`, JSON/Data-Routen, soweit sie nicht in Domain-Blueprints bleiben |
| `events` | `/events/status`, `/events/live_log`, `/events/live_log_full`, `/events/mqtt_monitor`, `/events/knx_monitor` |
| `templates` | `/templates`, `/templates/export`, `/templates/import` |

## Helper In Legacy

| Helper-Gruppe | Beispiele | Zielort |
|---|---|---|
| Layout/HTML | `render_layout`, `embedded_page`, `mapping_*_select`, `build_datalist_html`, grosse CSS/JS-Strings | `app/templates/`, `app/static/`, `app/utils/html.py` |
| Dashboard/Shell | `dashboard_content`, `build_sidebar_links_html`, `shell_status_payload` | `app/routes/dashboard.py`, `app/services/runtime.py` |
| Config-Aliase | `load_*_config`, `save_*_config` Aliase auf `services.config` | direkte Service-Nutzung in Blueprints |
| Mapping UI | `render_shared_mapping_explorer_page`, `shared_mapping_explorer_script`, `render_mapping_card` | `app/templates/mappings/`, `app/static/js/mappings.js` |
| Search/Conflicts | `collect_global_search_items`, `collect_config_conflicts` | `app/services/search.py`, `app/services/validation.py` |
| Bridge/Runtime | `bridge_async`, `bridge_runner`, `handle_mqtt_command`, Start/Stop-Routen | `app/engine/bridge.py`, `app/routes/system.py` |
| KNX Listener/Monitor | `_knx_listener_async`, `knx_listener_runner`, `ensure_knx_listener_started`, `add_knx_monitor_entry`, `knx_monitor_payload` | erst spaeter `app/routes/knx.py`; xknx-nahe Logik besonders vorsichtig |
| SSE | `sse_response`, `status_sse_response`, Event-Payloads | `app/routes/events.py`, optional `app/utils/sse.py` |
| UDP Input/Discovery | UDP-Seitenhelper, Test-/Data-Routen | `app/routes/udp.py` |
| Objects UI | `objects_page`, `objects_edit_page` | `app/routes/objects.py`, `app/templates/objects/` |
| Influx Explorer UI | `influx_explorer_page` | `app/routes/influx.py`, `app/templates/influx/` |

## App-Initialisierung In Legacy

Aktuell steckt noch in `app/core.py`:

- `runtime_context = create_runtime_context()`
- `app = Flask(__name__)`
- Flask Config: `JSON_AS_ASCII`, Upload-Limits
- `@app.after_request force_utf8_response`
- globale Laufzeitobjekte: `ws`, `main_loop`, `mqtt_client`, Config-/Mapping-Aliase, Loxone Mappings
- direkte Route-Registrierung per `@app.route`
- grosse Layout-Konstanten und Shell-Rendering

Ziel:

- `app/__init__.py` enthaelt `create_app(config_object=None)`.
- `create_app()` erzeugt Flask-App, RuntimeContext, registriert UTF-8 Hook, Blueprints und Startup-Status.
- RuntimeContext wird zentral an Blueprints/Services angebunden, nicht in Legacy erzeugt.
- `app/main.py` ruft nur noch `from app import create_app`.

## Direkte Legacy-Abhaengigkeiten

| Datei | Abhaengigkeit | Ziel |
|---|---|---|
| `app/main.py` | `from engine.port import APP_VERSION, create_app` | `from app import create_app`; Version aus neutralem Modul |
| `app/engine/port.py` | `APP_CORE_FILE`, `direkte App-Core-Initialisierung`, `create_app`, setzt `legacy.app.config` | Bootstrap nur noch Startup/Dependency Check oder entfernen |
| `app/core.py` | importiert alle Services und RuntimeContext | wird geloescht |

## Zielstruktur

```text
app/
  __init__.py
  main.py
  engine/
    bridge.py
    port.py              # spaeter nur noch optionaler Startup-Check oder entfernt
  routes/
    dashboard.py
    config.py
    backup.py
    objects.py
    mqtt.py
    udp.py
    loxone.py
    influx.py
    knx.py
    api.py
    events.py
    system.py
  services/
  runtime/
  utils/
    encoding.py
    html.py
    json_response.py
    sse.py
  templates/
    layouts/
    dashboard/
    mqtt/
    udp/
    knx/
    influx/
    objects/
    config/
  static/
    css/
    js/
```

## Was Nach `app/__init__.py` Muss

- `create_app()`
- Flask-App-Erzeugung
- Pfad-/Config-Initialisierung
- RuntimeContext-Erzeugung und Ablage, z. B. `app.extensions["runtime_context"]`
- UTF-8 `after_request`
- Blueprint-Registrierung
- Startup-Status-Route
- zentrale Errorhandler, falls spaeter noetig

## Was Nach `app/routes/` Muss

- Alle 117 Routen, gruppiert nach Blueprint.
- Jede Route soll nur Request/Response, Form-Parsing, Redirects und Template-Rendering enthalten.
- Fachlogik bleibt in `app/services/*`.
- Runtime-State wird aus RuntimeContext gelesen/geschrieben.

## Was Nach `app/utils/` Muss

- `encoding.py`: UTF-8 Response Hook.
- `sse.py`: SSE Response Generator.
- `html.py`: Escape-/Option-/Datalist-Helfer, sofern nicht direkt Jinja.
- `json_io.py` oder bestehend `services.config`: nur wenn Config-Service spaeter entlastet wird.
- `network.py`: kleine IP/Port/URL-Helfer, falls benoetigt.

## Was Nach `templates/` Und `static/` Muss

- `APP_LAYOUT` und `SHELL_LAYOUT` nach `templates/layouts/`.
- Grosse Seitenfunktionen wie `monitor`, `mqtt2lox`, `topics2_content`, `mqtt2udp`, `knx_monitor` in Templates zerlegen.
- Lange Inline-JS-Bloecke nach `static/js/`.
- Lange Inline-CSS-Bloecke nach `static/css/`.
- Mapping-Karten und Tabellen als Jinja-Partials.

## Migrationsphasen

### A) `app/routes` Grundstruktur

- Ordner `app/routes/` mit `__init__.py` und leeren Blueprint-Modulen anlegen.
- Gemeinsame Hilfen fuer `get_runtime_context()`, Redirects und JSON-Antworten definieren.
- Noch keine Routen verschieben.
- Smoke-Test: App startet unveraendert.
- Status 32.4.9: Grundstruktur und RuntimeContext-Zugriffshilfe angelegt; Startverhalten bleibt Legacy-basiert.

### B) Dashboard Blueprint

- Verschieben: `/`, `/dashboard_embed`, `/shell_status`, LiveLog-Seiten ohne SSE.
- Templates fuer Shell/Dashboard vorbereiten.
- Risiko: niedrig-mittel.
- Exit: Dashboard, Status oben links, LiveLog-Seite unveraendert.

### C) Config/Backup/Objects Blueprints

- Verschieben: Settings, Save-Routen, Backup/Restore, Objects.
- Services `config`, `backup`, `object` direkt nutzen.
- Risiko: mittel wegen POST/Dateioperationen.
- Exit: Settings speichern, Backup/Restore, Objektmanager Smoke-Test.

### D) Domain-Blueprints MQTT/UDP/Loxone/Influx

- Verschieben: MQTT Hub/Monitor/Topics/Broker, UDP-Mappings/Input/Discovery, MQTT->Loxone, Influx Explorer.
- Grosse HTML-Seiten schrittweise in Templates/Static ueberfuehren.
- Risiko: hoch wegen grosser UI-Funktionen.
- Exit: MQTT Monitor, Topic Explorer, UDP Input/Discovery, Influx Explorer.

### E) API Blueprint

- Gruppieren: JSON/Data-Routen, Global Search, Conflicts, Monitor Settings, kleine AJAX-POSTs.
- Alternativ Domain-nahe Data-Routen bei Domain-Blueprints lassen.
- Risiko: mittel.
- Exit: Alle `*_data` und AJAX-Routen liefern identische JSON-Strukturen.

### F) Events Blueprint

- Verschieben: `/events/status`, `/events/live_log`, `/events/live_log_full`, `/events/mqtt_monitor`, `/events/knx_monitor`.
- `sse_response` nach `app/utils/sse.py`.
- Risiko: hoch wegen dauerhaft offener Streams.
- Exit: alle SSE Streams verbinden, initial payload, Keepalive, Updates.

### G) KNX Blueprint

- Verschieben: KNX Hub, Settings, MQTT->KNX, UDP->KNX, KNX->MQTT, KNX->Loxone, KNX Monitor, Listener Start.
- xknx-nahe Funktionen erst zuletzt und nur mit Hardware-Smoke-Test.
- Risiko: sehr hoch.
- Exit: KNX Monitor, Telegramm, `[KNX MONITOR ADD]`, `[KNX SSE]`, Mapping-Richtungen.

### H) System Blueprint

- Verschieben: Bridge Start/Stop, Broker Start/Stop/Status, Test-Routen.
- Bridge-Orchestrierung spaeter aus Route heraus in `app/engine/bridge.py`.
- Risiko: hoch.
- Exit: Bridge Start/Stop, interner Broker, Status-SSE, LiveLog.

### I) App Factory

- Status: in 32.7.0 umgesetzt.
- `app/__init__.py` ist aktiv.
- `app/main.py` verwendet `from app import create_app`.
- `app/engine/port.py` ist auf Startup/Dependency Check reduziert.

### J) Legacy Delete

- Status: in 32.7.0 fuer den alten Dateipfad umgesetzt.
- Der bisherige Kern liegt nun als `app/core.py` im App-Package.
- Die weitere Entfernung betrifft nicht mehr den alten Dateipfad, sondern die schrittweise Zerlegung von `app/core.py`.
- Dokumentation und Tests wurden auf den neuen Startpfad aktualisiert.

## Exit-Kriterien Fuer Legacy-Loeschung

- Keine Route mehr in `app/core.py`.
- Keine Runtime-State-Variable mehr in `app/core.py`.
- Keine grossen `render_template_string`-/HTML-/JS-Monster mehr in `app/core.py`.
- `app/main.py` startet ohne Import von `app.core` oder `create_app`.
- `app/engine/port.py` laedt keine App-Core-Datei per `importlib`.
- `python -m compileall app legacy` sauber.
- Smoke-Test sauber:
  - Dashboard
  - Status/Shell
  - LiveLog
  - MQTT Hub/Monitor
  - UDP Seiten
  - Loxone Mapping
  - Influx Explorer
  - Objects
  - Backup/Restore
  - KNX Monitor und Listener
  - alle SSE-Endpunkte
- Nach Loeschung: `python -m compileall app` sauber.

## Wann Kann `app/core.py` Geloescht Werden?

Erst nach Phase I, wenn:

1. alle 117 Routen in Blueprints registriert sind,
2. App Factory und RuntimeContext ohne Legacy funktionieren,
3. keine Route, kein Helper, kein Layout und kein Runtime-State mehr aus Legacy importiert wird,
4. alle Smoke-Tests erfolgreich sind,
5. `app/engine/port.py` keine App-Core-Datei mehr laedt,
6. Dokumentation und Startanleitung auf die neue App Factory zeigen.

Bis dahin bleibt `app/core.py` als Sicherheitsnetz erhalten.
