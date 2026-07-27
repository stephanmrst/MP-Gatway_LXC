# Architektur-Review 32.3.1

Stand: MQTT2LoxV32 nach der ersten Modularisierung bis 32.3.0.

Dies ist eine reine Analyse. Es wurden keine Dateien verschoben, keine Funktionen verschoben und keine Logik oder UI geaendert.

## Aktuelle Struktur

```text
app/
  main.py
  core.py
  __init__.py
  engine/
    port.py
  services/
    backup.py
    config.py
    influx.py
    knx.py
    loxone.py
    mqtt.py
    object.py
    runtime.py
    template.py
    udp.py
  runtime/
    __init__.py
    context.py
    bridge_state.py
    live_log.py
    mqtt_state.py
    knx_state.py
    udp_state.py
    broker_state.py
  routes/
  models/
  utils/
config/
data/
backups/
logs/
```

`app/main.py` startet die Flask-App seit 32.7.0 ueber `from app import create_app`; `app/__init__.py` ist die zentrale Factory. Die Services enthalten inzwischen viele fachliche Hilfsfunktionen, aber `app/core.py` ist weiter der zentrale Container fuer grosse HTML-Bloecke, Runtime-State, Live-Monitore und Bridge-Orchestrierung. `app/runtime/` enthaelt seit 32.3.4 ein Dataclass-Grundgeruest fuer den RuntimeContext; LiveLog, Bridge-State, MQTT-Monitor-State, UDP-Laufzeitdaten, Broker-State und KNX-Runtime-State sind angebunden. Seit 32.4.7 sind die alten KNX-Global-State-Reste entfernt. Seit 32.7.1 sind die letzten alten Ordnerreste entfernt. xknx bleibt bewusst im App-Core.

## Kennzahlen

| Bereich | Befund |
|---|---:|
| Python-Dateien ohne `__pycache__` | 13 |
| `app/core.py` | ca. 10.786 Zeilen |
| Funktionen in `app/core.py` | 279 |
| Flask-Routen in `app/core.py` | 117 |
| Globale Zuweisungen in `app/core.py` | 113 |
| Service-Module | 10 |
| Groesste Funktion | `monitor`, ca. 1.301 Zeilen |

## Datei-Bewertung

| Datei | Status | Empfehlung | Prioritaet | Aufwand |
|---|---|---|---|---|
| `app/main.py` | gut | Schlank lassen; nur App-Fabrik, UTF-8-Hook und Startlogik behalten. Import `APP_VERSION` pruefen, da aktuell nicht direkt genutzt. | niedrig | niedrig |
| `app/engine/port.py` | mittel | Weiter als Bootstrap-/Kompatibilitaetsmodul verwenden. Langfristig Pfad-/Versionskonstanten in `app/config/runtime.py` oder `app/context.py` ziehen, damit Services nicht von `engine` abhaengen. | mittel | mittel |
| `app/core.py` | kritisch | In mehreren Schritten in Blueprints und Context/Runtime-State zerlegen. Zuerst Routen gruppieren, dann globale States kontrolliert kapseln. | hoch | hoch |
| `app/services/config.py` | mittel | Zentrale Config-Zustaendigkeit ist sinnvoll. Abhaengigkeit zu `engine.port` spaeter entfernen; Pfade ueber Context oder Settings uebergeben. | hoch | mittel |
| `app/services/mqtt.py` | mittel | MQTT-State (`mqtt_clients`, `mqtt_client`, Monitorwerte) spaeter in RuntimeContext verschieben. Publish-/Monitor-Hilfen aus App-Core vereinheitlichen. | mittel | mittel |
| `app/services/udp.py` | gut-mittel | Fachlich klar, aber importiert `services.config`. Spaeter Ports/Presets ueber Parameter oder Context uebergeben. | mittel | mittel |
| `app/services/knx.py` | gut-mittel | Reine KNX-Hilfs- und Bridge-Funktionen sind passend. Monitor/Listener bewusst im App-Core lassen, bis RuntimeContext existiert. | mittel | mittel |
| `app/services/loxone.py` | gut | Sauber abgegrenzt. Weiter nur als Bridge-/Options-Service verwenden. | niedrig | niedrig |
| `app/services/influx.py` | gut-mittel | Influx-Zugriff ist fachlich passend. Explorer-Routen spaeter in `routes/influx.py` verschieben. | mittel | mittel |
| `app/services/object.py` | mittel | Fachlich sinnvoll, aber einzelne Funktionen sind gross. Spaeter Objektmodell in `models/` und Mapping-Sync in eigenen Service trennen. | mittel | mittel-hoch |
| `app/services/runtime.py` | mittel | Gute Richtung fuer Status/Live-Log/Broker. Sollte spaeter zentraler RuntimeContext statt loser Parameter werden. | hoch | mittel |
| `app/services/backup.py` | gut | Backup-/Restore-Logik ist kompakt und klar. Route spaeter in `routes/backup.py`, Service kann bleiben. | niedrig | niedrig |
| `app/services/template.py` | mittel | Hilft bei wiederkehrenden HTML-Helfern, ersetzt aber noch keine echte Template-Struktur. Spaeter nach `templates/` und Jinja-Partial-Struktur ueberfuehren. | mittel | hoch |
| `app/runtime/*.py` | gut | RuntimeContext-Grundgeruest. LiveLog, Bridge-State, MQTT-Monitor-State, UDP-State, Broker-State und KNX-Runtime-State sind angebunden; alte KNX-Globals sind entfernt, xknx erst nach Tests migrieren. | mittel | niedrig |
| `KNX_RUNTIME_MIGRATION_PLAN.md` | gut | Detailplan fuer die spaetere KNX-State-Migration. Vor KNX-Aenderungen zuerst Smoke-Tests und Reihenfolge pruefen. | hoch | niedrig |
| `LEGACY_REMOVAL_PLAN.md` | gut | Zielplan fuer App Factory, Blueprints, Templates/Static und finale Entfernung von `app/core.py`. | hoch | niedrig |
| `config/*.json` | mittel | Daten liegen klar getrennt. Spaeter Schema-/Validation-Modelle in `models/` oder `utils/validation.py` ergaenzen. | mittel | mittel |
| `logs/` und `backups/` | gut | Runtime-Artefakte getrennt. Nicht in fachliche Module mischen. | niedrig | niedrig |

## Was liegt noch in `app/core.py`?

| Block | Beispiele | Einschätzung | Zielort spaeter |
|---|---|---|---|
| Flask-App, Hooks und Basislayout | `app = Flask(...)`, `force_utf8_response`, `render_layout` | Muss bis zur Blueprint-Einfuehrung zentral bleiben. | `app/routes/*`, `templates/` |
| Dashboard und Shell | `dashboard_content`, `/`, `/dashboard_embed`, Sidebar-/Statusfragmente | Stark routen- und UI-nah. | `routes/dashboard.py`, `templates/dashboard/` |
| Settings und Config-Routen | `/settings`, `/save`, `/save_core`, `/save_mqtt`, `/save_influx` | Gute Blueprint-Kandidaten, Logik teils schon in Services. | `routes/settings.py` |
| MQTT Monitor / Topic Manager | `monitor`, `topics2_content`, `topics`, Save/Data-Routen | Sehr grosser Block mit HTML, JS, State und Config-Zugriff. | `routes/mqtt.py`, `services/mqtt.py`, `templates/mqtt/` |
| Mapping-Seiten | `mqtt2lox`, `mqtt2udp`, `mqtt2knx`, `udp2knx`, Shared Mapping Explorer | UI-lastig, viele wiederholte Muster. | `routes/mappings.py`, `templates/mappings/` |
| KNX Monitor und Listener | `_knx_listener_async`, `knx_listener_runner`, `add_knx_monitor_entry`, `/events/knx_monitor` | Sensibler Live-State; vorerst im App-Core lassen. | spaeter `routes/knx.py` + RuntimeContext |
| Bridge-Orchestrierung | `bridge_async`, `bridge_runner`, `/start`, `/stop`, MQTT/UDP/KNX/Loxone-Verkettung | Zentraler Laufzeitkern, riskant fuer Umbauten. | `engine/bridge.py`, `services/runtime.py` |
| Objektmanager-Routen | `objects_page`, `objects_edit`, Sync-/Rebuild-Routen | Service existiert, Routen/UI noch gross. | `routes/objects.py`, `models/object.py` |
| Influx Explorer | Explorer- und Settings-Routen | Service existiert, Routen koennen spaeter raus. | `routes/influx.py` |
| Plugin- und Sidebar-Verwaltung | `/plugins`, `/plugins/save`, Sidebar Links | Sollte getrennt werden, sobald Plugin-Konzept stabilisiert wird. | `routes/plugins.py`, `plugins/` |
| Backup/Restore-Routen | `/backup`, `/restore`, Download/Upload | Service ist kompakt vorhanden. | `routes/backup.py` |
| Suche/Konflikte | `collect_global_search_items`, `collect_config_conflicts` | Fachlich eigenstaendig. | `services/search.py`, `services/validation.py` |

## Kandidaten fuer `routes/`

Hohe Prioritaet:

- `routes/dashboard.py`: Dashboard, Shell-Status, Live-Log-Seiten.
- `routes/mqtt.py`: MQTT Monitor, Topic Manager, MQTT-Broker-Seiten.
- `routes/mappings.py`: MQTT->Loxone, MQTT->UDP, MQTT->KNX, UDP->MQTT, UDP->KNX.
- `routes/settings.py`: Core-, MQTT-, Influx-, Sidebar- und Plugin-Speichern.

Mittlere Prioritaet:

- `routes/knx.py`: KNX Monitor, KNX Settings, KNX Mapping-Routen. Erst nach RuntimeContext.
- `routes/influx.py`: Influx Explorer und Status.
- `routes/objects.py`: Objektmanager.
- `routes/backup.py`: Backup/Restore.
- `routes/plugins.py`: Plugin-UI und Plugin-Konfiguration.

## Funktionen

### Extrem grosse Funktionen ueber 200 Zeilen

| Funktion | Datei | Zeilen | Bewertung |
|---|---|---:|---|
| `monitor` | `app/core.py` | ca. 1.301 | kritisch: HTML, JS, State und Aktionen in einer Funktion |
| `mqtt2lox` | `app/core.py` | ca. 862 | kritisch: grosse Mapping-UI |
| `topics2_content` | `app/core.py` | ca. 743 | kritisch: Topic-UI und Datenlogik stark gemischt |
| `mqtt2udp` | `app/core.py` | ca. 426 | mittel-kritisch: Mapping-UI |
| `knx_monitor` | `app/core.py` | ca. 410 | mittel-kritisch: sensibel wegen Live-State |
| `shared_mapping_explorer_script` | `app/core.py` | ca. 263 | mittel: JS-Block spaeter in static asset |
| `topics` | `app/core.py` | ca. 242 | mittel-kritisch |
| `bridge_async` | `app/core.py` | ca. 205 | kritisch wegen Runtime-Verhalten |
| `ensure_object_mappings` | `app/services/object.py` | ca. 269 | mittel: fachlich gross, aber bereits im Service |

### Weitere grosse Funktionen ueber 100 Zeilen

- `collect_config_conflicts`, `render_shared_mapping_explorer_page`, `udp_input_page`, `collect_global_search_items`, `mqtt_brokers_page`, `handle_mqtt_command`, `dashboard_content`, `live_log_console_content` in `app/core.py`.
- `cleanup_object_mappings`, `sync_objects_from_expert_mappings` in `app/services/object.py`.
- `embedded_page` in `app/services/template.py`.

### Doppelte oder adapterartige Funktionen

Viele doppelte Funktionsnamen sind App-Core-Adapter fuer bereits ausgelagerte Services. Das ist aktuell stabilisierend, aber langfristig aufzuraeumen:

- Config-Loader/Saver doppelt in `app/core.py` und `app/services/config.py`.
- UDP-Hilfen doppelt in `app/core.py` und `app/services/udp.py`.
- Backup-Hilfen doppelt in `app/core.py` und `app/services/backup.py`.
- Runtime-/Broker-Hilfen doppelt in `app/core.py` und `app/services/runtime.py`.
- Template-Hilfen doppelt in `app/core.py` und `app/services/template.py`.

Hinweis: Nicht alle Duplikate sind Fehler. Viele App-Core-Funktionen sind bewusst kleine Wrapper, damit bestehende Routen und alte Aufrufstellen stabil bleiben.

### Potenziell unbenutzte Funktionen

Ohne Laufzeit-/Template-Analyse lassen sich unbenutzte Funktionen nicht sicher entfernen. Kandidaten sollten nur mit Tests und `rg`-Pruefung behandelt werden. Prioritaet haben Wrapper, die nur noch an eine Service-Funktion delegieren.

## Imports

### Auffaellige unbenutzte Import-Kandidaten

| Datei | Kandidat | Bewertung |
|---|---|---|
| `app/main.py` | `APP_VERSION` | Wird importiert, aber im Modul nicht direkt verwendet. Niedriges Risiko, spaeter bereinigen. |
| `app/core.py` | `subprocess`, `shutil`, `zipfile` | AST sieht keine direkte Nutzung. Vor Entfernung mit Textsuche und Backup/Runtime-Routen pruefen. |

### Doppelte Imports

`app/core.py` enthaelt weiterhin viele Import- und Konstantenbloecke aus der Port-Historie. Kritisch ist das nicht sofort, aber es erschwert Review und Fehleranalyse.

## Zyklische Abhaengigkeiten

Keine harte zyklische Service-Import-Schleife wurde gefunden.

Auffaellige Kante:

```text
app/main.py -> app/engine/port.py -> app/core.py -> app/services/config.py -> app/engine/port.py
```

Diese Kette funktioniert aktuell, ist architektonisch aber unschoen. `services/config.py` sollte langfristig nicht aus `engine.port` importieren, sondern Pfade/Defaults aus einem neutralen Context oder Settings-Modul erhalten.

Weitere lokale Abhaengigkeiten:

- `app/core.py` importiert alle Service-Module.
- `app/services/udp.py` importiert `services.config`.
- Die meisten anderen Services sind weitgehend frei von gegenseitigen Service-Abhaengigkeiten.

## Globale Variablen und States

Wichtige globale States:

- `live_log` in `app/core.py`.
- `knx_monitor_log` und `knx_monitor_values` in `app/core.py`.
- `sse_versions` in `app/core.py`.
- Pfad- und Config-Konstanten in `app/core.py`, `app/services/config.py` und `app/engine/port.py`.
- MQTT-State in `app/services/mqtt.py`: `mqtt_monitor_values`, `mqtt_clients`, `mqtt_client`.
- UDP-State in `app/services/udp.py`: `mqtt2udp_last_seen`, `udp2mqtt_last_seen`, `udp_input_last_seen`.
- Runtime-/Broker-State teils in `app/core.py`, teils in `app/services/runtime.py`.

Empfehlung:

- Einen `RuntimeContext` einfuehren, aber erst nach Route-Gruppierung planen.
- Darin Live-Log, Monitor-Listen, MQTT-Clients, UDP-Last-Seen, Broker-Prozess, Bridge-Thread und SSE-Versionen buendeln.
- Config-Pfade separat in einem `Settings`-/`AppContext` halten, nicht in `engine`.

## Services

Die Services sind nach der ersten Modularisierung grob sinnvoll getrennt:

- `config`: JSON-Dateien, Defaults, sichere Loader/Saver.
- `mqtt`: MQTT-Config und Monitor-/Client-State.
- `udp`: UDP Listener, Mapping-Hilfen, Presets.
- `knx`: KNX-Konvertierung und Bridge-Funktionen ohne Monitorliste.
- `loxone`: Loxone-Bridge-Hilfen.
- `influx`: Influx-Verbindung, Schreiben, Explorer-Abfragen.
- `object`: Objektmanager- und Mapping-Sync.
- `runtime`: Status, Live-Log, interner Broker.
- `backup`: Backup/Restore-Dateilogik.
- `template`: wiederverwendbare HTML-Helfer.

Auffaelligkeiten:

- `config.py` ist sehr zentral und hat viele Defaults und Pfade. Das ist okay, aber sollte nicht von `engine.port` abhaengen.
- `object.py` enthaelt komplexe Mapping-Logik und koennte spaeter in Objektmodell, Candidate-Merge und Mapping-Sync getrennt werden.
- `template.py` ist ein Zwischenzustand. Langfristig sollten grosse HTML-Bloecke echte Templates werden.
- Service-Funktionen erhalten viele Callback-/Loader-Parameter. Das ist fuer die Stabilisierung gut, sollte spaeter durch Context-Objekte lesbarer werden.

## Flask

117 Routen liegen noch in `app/core.py`. Das ist die groesste strukturelle Baustelle.

Empfohlene Reihenfolge:

1. Nur Routen in Blueprints gruppieren, ohne Service-Logik erneut zu verschieben.
2. Gemeinsame Context-Parameter fuer Config, Runtime-State und Logger einfuehren.
3. Grosse HTML-Bloecke in echte Templates ueberfuehren.
4. Danach erst Bridge-Orchestrierung und Live-Monitore weiter entflechten.

## Plugins

Plugin-Code ist aktuell vor allem Konfiguration und UI im App-Core:

- `config/plugins.json`
- `DEFAULT_PLUGINS`
- `/plugins`
- `/plugins/save`
- Sidebar-/Plugin-Sichtbarkeit

Empfehlung:

- Kurzfristig nur nach `routes/plugins.py` auslagern.
- Mittelfristig Plugin-Metadaten in `models/plugin.py`.
- Langfristig echtes `app/plugins/` nur dann, wenn Plugins eigene Hooks oder Runtime-Logik bekommen.

## Performance

Auffaellige Stellen:

- Grosse HTML-/JS-Strings werden bei jedem Request neu gebaut.
- Mapping-Seiten durchsuchen und rendern teils grosse Config-Strukturen mehrfach.
- Global Search und Conflict Scanner laufen ueber viele Configs und sollten spaeter gecacht oder inkrementell berechnet werden.
- Influx Explorer kann je nach Bucket/Measurement teuer sein; gute Fehlergrenzen und Timeouts bleiben wichtig.
- SSE-Endpunkte sollten bei wachsendem Log klare Limits behalten.

Aktuell ist keine offensichtliche Performance-Katastrophe sichtbar, aber die groessten Routen sind schwer testbar und dadurch riskant.

## Zielstruktur

```text
app/
  engine/
    port.py
    bridge.py
  services/
    config.py
    mqtt.py
    udp.py
    knx.py
    loxone.py
    influx.py
    object.py
    runtime.py
    backup.py
    search.py
    validation.py
  routes/
    dashboard.py
    settings.py
    mqtt.py
    udp.py
    knx.py
    loxone.py
    influx.py
    objects.py
    mappings.py
    backup.py
    plugins.py
  plugins/
    registry.py
  models/
    config.py
    mapping.py
    object.py
    plugin.py
    runtime.py
  utils/
    encoding.py
    json_io.py
    html.py
    network.py
  templates/
    layout.html
    dashboard/
    mappings/
    mqtt/
    knx/
    influx/
  static/
    css/
    js/
```

## Priorisierte Empfehlungen

| Prioritaet | Empfehlung | Aufwand | Risiko |
|---|---|---|---|
| 1 | Tests fuer Hauptseiten, JSON-Endpunkte und SSE-Payloads einfuehren. | mittel | niedrig |
| 2 | Blueprint-Plan erstellen, aber zuerst nur Routen gruppieren. | mittel | mittel |
| 3 | `RuntimeContext` fuer Live-Log, Monitor-State, MQTT/UDP-State und Broker-Prozess entwerfen. | mittel-hoch | mittel |
| 4 | `services/config.py` von `engine.port` entkoppeln. | mittel | mittel |
| 5 | Grosse Mapping- und Monitor-HTML-Bloecke schrittweise in Templates/Static JS ueberfuehren. | hoch | mittel-hoch |
| 6 | App-Core-Wrapper erst entfernen, wenn Routen und Tests stabil sind. | mittel | mittel |
| 7 | Plugin-Verwaltung als eigene Route/Registry planen. | niedrig-mittel | niedrig |

## Wichtigste Erkenntnisse

- Die erste Modularisierung hat Services fachlich erkennbar getrennt, aber der App-Core bleibt der zentrale Engpass.
- Die groessten Risiken liegen nicht in einzelnen Services, sondern in den grossen Flask-Routen mit gemischtem HTML, JS, State und Config-Zugriff.
- Der naechste sinnvolle Schritt ist nicht weitere blinde Auslagerung, sondern ein getesteter Blueprint- und RuntimeContext-Plan.

## Groesste Baustellen

- `app/core.py` mit 117 Routen, 279 Funktionen und sehr grossen HTML-/JS-Funktionen.
- Globale Live-States fuer MQTT, UDP, KNX, Live-Log und Broker-Prozess.
- Doppelte App-Core-Wrapper zu bereits vorhandenen Services.
- `services/config.py` importiert aus `engine.port` und sollte neutraler werden.

## Empfohlene naechste Schritte

1. Smoke-/Regressionstests fuer Dashboard, MQTT Hub, KNX Monitor, Influx Explorer, Objektmanager und Live-Log festlegen.
2. Blueprint-Schnitt planen: zuerst Routen verschieben, keine Fachlogik.
3. Das RuntimeContext-Grundgeruest aus `app/runtime/` erst nach Tests instanziieren und schrittweise verdrahten.
4. Danach `routes/dashboard.py` und `routes/settings.py` als risikoarme erste Blueprint-Kandidaten angehen.
