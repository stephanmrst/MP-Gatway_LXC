# RuntimeContext-Plan 32.4.7

Stand: Analyse der globalen Variablen und States in `app/core.py`.

Dies ist nur ein Plan. Es wurden keine Dateien verschoben, keine Funktionen verschoben und keine Logik oder UI geaendert.

## Ziel

Ein spaeterer `RuntimeContext` soll Laufzeit-State zentral, nachvollziehbar und thread-bewusst halten. Aktuell liegen Live-Log, Monitorlisten, MQTT/UDP/KNX-Last-Seen-Werte, Bridge-Flags, Broker-Prozess und Config-Aliase verteilt in `app/core.py` und einzelnen Services.

Seit 32.3.4 existiert unter `app/runtime/` ein Grundgeruest aus Dataclasses. Seit 32.3.5 nutzt LiveLog den RuntimeContext. Seit 32.3.7 ist auch der Bridge-State vollstaendig in `runtime_context.bridge` migriert. Seit 32.3.8 wird MQTT-Monitor-State zusaetzlich in `runtime_context.mqtt` gepflegt und von Monitor-Datenrouten bevorzugt gelesen. Seit 32.3.9 werden UDP-Laufzeitdaten zusaetzlich in `runtime_context.udp` gepflegt und von UDP-Seiten bevorzugt gelesen. Seit 32.4.0 ist der interne Broker-State vollstaendig in `runtime_context.broker` migriert. Seit 32.4.7 liegt der KNX-Runtime-State fuer LastSeen, Monitor-Werte, Monitor-Log, Listener-Verwaltung und KNX-SSE-Versionierung vollstaendig in `runtime_context.knx`; alte KNX-Globals wurden entfernt. Seit 32.4.8 beschreibt `LEGACY_REMOVAL_PLAN.md`, wie RuntimeContext und Blueprints aus dem App-Core herausgeloest werden. xknx bleibt unveraendert im App-Core.

Empfohlene Zielbereiche:

- `runtime.live_log`
- `runtime.mqtt_monitor`
- `runtime.knx_monitor`
- `runtime.udp_state`
- `runtime.bridge_state`
- `runtime.broker_state`
- `runtime.config_cache`
- `bleibt lokal`

## Markierungen

| Markierung | Bedeutung |
|---|---|
| `LIST` | Liste oder `deque` |
| `DICT` | Dictionary oder Mapping |
| `LOCK` | Lock/RLock |
| `THREAD` | Thread-Referenz |
| `PROCESS` | Subprozess-/Broker-Prozess |
| `FLAG` | Start/Stop-/Status-Flag |
| `SSE_VERSION` | Eventstream-Version/Invalidierung |
| `IO` | WebSocket, MQTT-Client, Eventloop oder externe Verbindung |
| `ALIAS` | Service-/Config-Funktionsalias, kein eigener Runtime-State |
| `CONST` | Pfad, Default oder HTML-Konstante |

## Wichtigste Runtime-States

| Variable | Typ | Zweck | liest | schreibt | betroffene Routen | Services | Risiko | Empfehlung |
|---|---|---|---|---|---|---|---|---|
| `live_log` | `deque(maxlen=100)` | Zentrale Live-Log-Liste fuer Dashboard, Live-Log und SSE. Seit 32.3.5 wird jeder neue Eintrag zusaetzlich nach `runtime_context.live_log.entries` gespiegelt. | `dashboard_content`, `live_log_payload`, `live_log_full_payload`, `live_log_console_content` | `add_log_entry`, Clear-Routen indirekt | `/live_log`, `/live_log_page`, `/live_log_data`, `/events/live_log`, `/events/live_log_full`, `/clear_log`, `/clear_monitor` | `runtime_service` nutzt Payload-Hilfen | hoch: `LIST`, `SSE`, mehrere Requests | `runtime.live_log` |
| `runtime_context.knx.monitor_log` | `deque(maxlen=15)` | KNX-Monitor-Eintraege fuer UI, JSON und SSE. Seit 32.4.4 bevorzugte Quelle fuer Monitor-Payload; alter Deque bleibt parallel. | `knx_monitor_payload`, `knx_monitor_data`, `events_knx_monitor` indirekt | `add_knx_monitor_entry` ueber Wrapper | `/knx_monitor`, `/knx_monitor_data`, `/events/knx_monitor` | `knx_service` nur per Callback | hoch: `LIST`, KNX-Thread, SSE | `runtime.knx_monitor` |
| `runtime_context.knx.monitor_values` | `dict` | Letzte KNX-Werte pro Gruppenadresse. Seit 32.4.3 bevorzugte Quelle fuer Hub und Monitor-Payload; alter Dict bleibt parallel. | `knx_hub_content`, `knx_monitor_payload`, `/knx_monitor_data` indirekt | `add_knx_monitor_entry` ueber Wrapper | `/knx`, `/knx_monitor`, `/knx_monitor_data` | KNX-Service indirekt | hoch: `DICT`, KNX-Thread | `runtime.knx_monitor` |
| `sse_versions` | `dict` | Versionen fuer Eventstream-Aenderungen ohne KNX. | `event_stream`, `sse_response` | `bump_sse` | `/events/status`, `/events/live_log`, `/events/mqtt_monitor` | `runtime_service` | hoch: `SSE_VERSION`, parallele Clients | `runtime.live_log` plus Monitor-Substates |
| `runtime_context.knx.monitor_version` | int | Version fuer KNX-Monitor-SSE. Seit 32.4.6 Ersatz fuer `sse_versions["knx"]`. | `sse_response`, `/events/knx_monitor` indirekt | `bump_sse("knx")` | `/events/knx_monitor` | Runtime/KNX | hoch: `SSE_VERSION`, parallele Clients | `runtime.knx_monitor` |
| `runtime_context.bridge.thread` | `Thread`/`None` | Aktiver Bridge-Thread. | `start_bridge`, Restart-Worker | `start_bridge`, `restart_bridge_async` | `/start` | Runtime/Bridge | hoch: `THREAD`, Start/Stop-Race | `runtime.bridge_state` |
| `runtime_context.bridge.running` | `bool` | Bridge laeuft ja/nein. | `start_bridge`, Status/UI | `bridge_async`, `bridge_runner`, `start_bridge`, Restart-Worker | `/`, `/start`, `/events/status`, `/shell_status` | `runtime_service` | hoch: `FLAG`, Thread-State | `runtime.bridge_state` |
| `runtime_context.bridge.stop_requested` | `bool` | Stop-Signal fuer Bridge/KNX-Schleifen. | `bridge_async`, `_knx_listener_async` | `/start`, `/stop`, `bridge_async`, Restart-Worker | `/start`, `/stop` | Bridge/KNX | hoch: `FLAG`, Thread/async loop | `runtime.bridge_state` |
| `runtime_context.bridge.status` | `str` | Sichtbarer Status oben links und Status-SSE. | `index`, `render_layout`, `shell_status_payload`, `status_sse_response` | `bridge_async`, `bridge_runner`, `/start`, `/stop` | `/`, `/shell_status`, `/events/status`, `/start`, `/stop` | `runtime_service` | mittel-hoch: UI/SSE-Konsistenz | `runtime.bridge_state` |
| `runtime_context.broker.process` | Prozess/`None` | Mosquitto-Prozess fuer internen Broker. Seit 32.4.0 primaerer Speicherort. | `get_internal_broker_status`, Stop | `start_internal_broker_process`, `stop_internal_broker_process` | `/internal_broker/start`, `/internal_broker/stop`, `/internal_broker/status` | `runtime_service` | hoch: `PROCESS`, Lifecycle | `runtime.broker_state` |
| `ws` | WebSocket/`None` | Loxone WebSocket im Bridge-Betrieb. | `handle_mqtt_command`, `send_command` | `bridge_async`, `handle_mqtt_command` | keine direkte Route, wirkt auf Bridge | Loxone/Bridge | hoch: `IO`, async/thread | `runtime.bridge_state` |
| `main_loop` | asyncio Loop/`None` | Eventloop fuer thread-sichere Loxone-Kommandos. | `handle_mqtt_command` | `bridge_async`, `handle_mqtt_command` | keine direkte Route, wirkt auf Bridge | Bridge | hoch: `IO`, async/thread | `runtime.bridge_state` |
| `mqtt_client` | MQTT-Client/`None` | Haupt-MQTT-Client fuer Bridge und Tests. Seit 32.3.8 zusaetzlich in `runtime_context.mqtt.mqtt_client` gespiegelt. | KNX/UDP Publish, Tests | `bridge_async`, `handle_udp_to_mqtt`, `publish_value`, UDP-Listener | `/udp2mqtt/test/<int:index>` | `mqtt_service`, `udp_service`, `knx_service` | hoch: `IO`, Thread/Callback | `runtime.mqtt_monitor` oder `runtime.bridge_state` |
| `mqtt_clients` | dict/list aus Service | Broker-Client-Sammlung. Seit 32.3.8 zusaetzlich in `runtime_context.mqtt.mqtt_clients` gespiegelt. | `bridge_async` | `bridge_async` | keine direkte Route | `mqtt_service` | mittel: geteilter Service-State | `runtime.mqtt_monitor` |
| `runtime_context.mqtt.mqtt_monitor_values` | dict | MQTT-Monitor-Werte fuer UI/SSE. Seit 32.3.8 bevorzugte Quelle fuer Monitor-Reader. | `monitor_data`, `events_mqtt_monitor`, `mqtt_hub_content` | MQTT Callback zusaetzlich zum alten Service-State | `/monitor_data`, `/events/mqtt_monitor`, `/mqtt` | `mqtt_service` | hoch: `DICT`, Callback, SSE | `runtime.mqtt_monitor` |
| `runtime_context.knx.listener_thread` | Thread/`None` | Separater KNX-Listener-Thread. Seit 32.4.5 primaere Thread-Referenz. | `ensure_knx_listener_started`, Listener-Wrapper | `ensure_knx_listener_started`, Listener-Wrapper | `/knx_listener_start`, `/knx_monitor` indirekt | KNX/xknx | hoch: `THREAD`, externer Bus | `runtime.knx_monitor` |
| `runtime_context.knx.listener_running` | bool | Running-State der KNX-Listener-Verwaltung. | Listener-Wrapper | `ensure_knx_listener_started`, `is_knx_listener_running` | `/knx_listener_start`, `/knx_monitor` indirekt | KNX/xknx | mittel-hoch: Thread-Zustand | `runtime.knx_monitor` |
| `runtime_context.knx.start_requested` | bool | Start-Anforderung der KNX-Listener-Verwaltung. | Listener-Wrapper | `request_knx_start` | `/knx_listener_start`, `/knx_monitor` indirekt | KNX/xknx | mittel | `runtime.knx_monitor` |
| `runtime_context.knx.stop_requested` | bool | Stop-Anforderung der KNX-Listener-Verwaltung, aktuell nur vorbereitet. | Listener-Wrapper | `request_knx_stop` | keine direkte Route | KNX/xknx | mittel | `runtime.knx_monitor` |

## Mapping- und Last-Seen-State

| Variable | Typ | Zweck | liest | schreibt | betroffene Routen | Services | Risiko | Empfehlung |
|---|---|---|---|---|---|---|---|---|
| `state_mapping` | `dict` | Loxone-State-Topic-Mapping aus Bridge/Topics. | Topic-Manager, Dashboard, `message_callback`, `topics_data` | `load_mapping` | `/topics`, `/topics_data` | Bridge/Loxone | mittel: `DICT`, Bridge-Refresh | `runtime.config_cache` |
| `control_mapping` | `dict` | Loxone-Control-Mapping fuer MQTT-Kommandos. | `handle_mqtt_command`, `mqtt2lox`, `knx2lox` | `load_mapping` | `/mqtt2lox`, `/knx2lox` | Bridge/Loxone | mittel: `DICT` | `runtime.config_cache` |
| `last_values` | `dict` | Rohwerte fuer Loxone-/Topic-Anzeige. | Topic-Manager, `publish_value`, `topics` | `bridge_async`, `publish_value` | `/topics` | Bridge/Loxone | mittel-hoch: `DICT`, Bridge-Callback | `runtime.mqtt_monitor` |
| `display_values` | `dict` | Formatierte Werte fuer Topic-Anzeige. | Topic-Manager, `topics`, `topics_data` | `bridge_async`, `publish_value` | `/topics`, `/topics_data` | Bridge/Loxone | mittel-hoch: `DICT`, UI/Bridge | `runtime.mqtt_monitor` |
| `mqtt2lox_last_seen` | `dict` | Letzter Treffer fuer MQTT->Loxone. | `mqtt2lox`, `mqtt2lox_data`, `render_mapping_card` | `on_mqtt_message` | `/mqtt2lox`, `/mqtt2lox_data` | Loxone/Bridge | mittel: `DICT`, MQTT Callback | `runtime.mqtt_monitor` |
| `runtime_context.udp.mqtt2udp_last_seen` | dict | Letzter Treffer fuer MQTT->UDP. Seit 32.3.9 bevorzugte Quelle fuer Seiten und Datenrouten. | `mqtt2udp`, `mqtt2udp_data` | `udp_service` per optionalem Callback | `/mqtt2udp`, `/mqtt2udp_data` | `udp_service` | mittel: Service-State | `runtime.udp_state` |
| `runtime_context.udp.udp2mqtt_last_seen` | dict | Letzter Treffer fuer UDP->MQTT. Seit 32.3.9 bevorzugte Quelle fuer Seiten und Datenrouten. | `udp2mqtt`, `udp2mqtt_data` | `handle_udp_to_mqtt`/`udp_service` per optionalem Callback | `/udp2mqtt`, `/udp2mqtt_data` | `udp_service` | mittel: UDP Thread | `runtime.udp_state` |
| `runtime_context.knx.mqtt2knx_last_seen` | dict | Letzter Treffer fuer MQTT->KNX. Seit 32.4.2 bevorzugte Quelle fuer Seiten und Datenrouten; alter Dict bleibt parallel. | `mqtt2knx`, `mqtt2knx_data`, `_handle_mqtt_to_knx_service` | `knx_service` per optionalem Callback | `/mqtt2knx`, `/mqtt2knx_data` | `knx_service` | mittel-hoch: KNX/MQTT | `runtime.knx_monitor` |
| `runtime_context.knx.knx2mqtt_last_seen` | dict | Letzter Treffer fuer KNX->MQTT. Seit 32.4.2 bevorzugte Quelle fuer Seiten und Datenrouten; alter Dict bleibt parallel. | `knx2mqtt`, `knx2mqtt_data`, KNX Listener | `knx_service` per optionalem Callback | `/knx2mqtt`, `/knx2mqtt_data` | KNX/MQTT | hoch: KNX Thread | `runtime.knx_monitor` |
| `runtime_context.udp.udp2knx_last_seen` | dict | Letzter Treffer fuer UDP->KNX. Seit 32.3.9 bevorzugte Quelle fuer Seiten und Datenrouten. | `udp2knx`, `udp2knx_data`, `_handle_udp_to_knx_service` | UDP/KNX-Service, App-Core-Spiegelung | `/udp2knx`, `/udp2knx_data` | `udp_service`, `knx_service` | mittel-hoch: UDP/KNX | `runtime.udp_state` oder `runtime.knx_monitor` |
| `runtime_context.knx.knx2lox_last_seen` | dict | Letzter Treffer fuer KNX->Loxone. Seit 32.4.2 bevorzugte Quelle fuer Seiten und Datenrouten; alter Dict bleibt parallel. | `knx2lox`, `knx2lox_data`, KNX Listener | `knx_service` per optionalem Callback | `/knx2lox`, `/knx2lox_data` | KNX/Loxone | hoch: KNX Thread | `runtime.knx_monitor` |
| `runtime_context.udp.udp_input_last_seen` | dict | Letzter UDP-Input pro Port. Seit 32.3.9 bevorzugte Quelle fuer `/udp_input_data`. | `udp_input_data` | UDP-Input-Thread per optionalem Callback | `/udp_input`, `/udp_input_data` | `udp_service` | mittel: UDP Thread | `runtime.udp_state` |

## Locks, Threads und Eventstream-Versionen

| Variable | Markierung | Zweck | Risiko | Empfehlung |
|---|---|---|---|---|
| `_json_file_lock` | `LOCK` | Schutz fuer JSON-Datei-Lesen/-Schreiben in App-Core-Helfern. | mittel: Datei-I/O kann parallel aus Routen/Threads kommen. | `runtime.config_cache` oder `utils/json_io.py` |
| `bridge_thread` | `THREAD` | Bridge-Hauptthread. | hoch: Start/Stop und Join muessen atomar bleiben. | `runtime.bridge_state` |
| `knx_listener_thread` | `THREAD` | KNX-Monitor-/Listener-Thread. | hoch: xknx und Monitor-State. | `runtime.knx_monitor` |
| lokaler `udp_thread` | `THREAD` | UDP-Input-Listener in `bridge_async`. | mittel-hoch: aktuell lokale Referenz, kein zentraler Stop-State. | spaeter `runtime.udp_state` pruefen |
| `sse_versions` | `SSE_VERSION` | Versionszaehler fuer Polling/SSE-Payloads ohne KNX. | hoch: mehrere Clients, mehrere Eventbereiche. | verbleibende Eventbereiche spaeter pruefen |

Queues:

- Keine eigene Python-`Queue` als globale Variable gefunden.
- xknx verwendet intern `telegram_queue`; sie wird in `_knx_listener_async` registriert und ist externes Laufzeitverhalten.

## Config-, Pfad- und Service-Aliase

Diese globalen Namen sind keine eigentlichen Runtime-States, aber sie wirken wie globaler Kontext und sollten spaeter sauberer getrennt werden.

| Gruppe | Variablen | Zweck | Empfehlung |
|---|---|---|---|
| Pfade | `BASE_DIR`, `APP_ROOT`, `CONFIG_DIR`, `DATA_DIR`, `BACKUP_DIR` | Projekt-, Config-, Daten- und Backup-Pfade. | `runtime.config_cache` oder neutraler `AppSettings`/`Paths`-Context |
| Config-Dateien | `CONFIG_FILE`, `TOPIC_CONFIG_FILE`, `MQTT2LOX_FILE`, `MQTT2UDP_FILE`, `UDP2MQTT_FILE`, `UDP_PRESETS_FILE`, `MQTT_BROKERS_FILE`, `MONITOR_SETTINGS_FILE`, `PLUGIN_CONFIG_FILE`, `KNX_CONFIG_FILE`, `MQTT2KNX_FILE`, `KNX2MQTT_FILE`, `UDP2KNX_FILE`, `KNX2LOX_FILE`, `SIDEBAR_LINKS_FILE`, `INTERNAL_BROKER_FILE`, `OBJECTS_FILE` | Dateipfade fuer JSON-Configs. | `runtime.config_cache` oder `services.config` behalten, aber nicht in App-Core duplizieren |
| Default-Configs | `DEFAULT_CONFIG`, `DEFAULT_PLUGINS`, `DEFAULT_INTERNAL_BROKER_CONFIG`, `DEFAULT_KNX_CONFIG` | Fallback-Werte fuer Config-Loader. | in `services.config` belassen |
| Config-Funktionsaliase | `safe_load_json_file`, `safe_save_json_file`, `load_config`, `save_config`, `load_topic_config`, `save_topic_config`, `load_mqtt2lox_config`, `save_mqtt2lox_config`, `load_mqtt2udp_config`, `save_mqtt2udp_config`, `load_udp2mqtt_config`, `save_udp2mqtt_config`, `load_mqtt_brokers`, `save_mqtt_brokers`, `load_monitor_settings`, `save_monitor_settings`, `load_plugins_config`, `save_plugins_config`, `load_sidebar_links`, `save_sidebar_links`, `load_objects_config`, `save_objects_config`, `load_internal_broker_config`, `save_internal_broker_config`, `load_knx_config`, `save_knx_config`, `load_mqtt2knx_config`, `save_mqtt2knx_config`, `load_knx2mqtt_config`, `save_knx2mqtt_config`, `load_udp2knx_config`, `save_udp2knx_config`, `load_knx2lox_config`, `save_knx2lox_config` | App-Core-Kompatibilitaetsalias auf `services.config`. | bleibt vorerst lokal; spaeter direkte Service-Imports in Blueprints |
| Flask/UI-Konstanten | `app`, `APP_LAYOUT`, `SHELL_LAYOUT` | Flask-App und grosse HTML-Layouts. | `app` bleibt lokal bis App-Fabrik/Blueprints; Layouts spaeter `templates/` |

Hinweis: Einige Pfad- und Config-Namen werden im App-Core doppelt definiert, zuerst direkt und danach als Alias auf `services.config`. Das ist ein Port-Artefakt und sollte erst entfernt werden, wenn Tests fuer Config-Loader und Backup/Restore vorhanden sind.

## Routen nach State-Bereich

| Runtime-Bereich | Betroffene Routen |
|---|---|
| `runtime.live_log` | `/live_log`, `/live_log_page`, `/live_log_data`, `/events/live_log`, `/events/live_log_full`, `/clear_log`, `/clear_monitor` |
| `runtime.mqtt_monitor` | `/monitor`, `/monitor_data`, `/events/mqtt_monitor`, `/monitor/*`, `/topics`, `/topics_data`, `/mqtt2lox*`, `/mqtt2knx*`, `/udp2mqtt/test/<int:index>` |
| `runtime.knx_monitor` | `/knx`, `/knx_monitor`, `/knx_monitor_data`, `/events/knx_monitor`, `/knx_listener_start`, `/knx2mqtt*`, `/knx2lox*`, `/mqtt2knx*`, `/udp2knx*` |
| `runtime.udp_state` | `/mqtt2udp*`, `/udp2mqtt*`, `/udp_input*`, `/udp_discovery_status`, `/udp_discovery_toggle` |
| `runtime.bridge_state` | `/start`, `/stop`, `/shell_status`, `/events/status`, `/` |
| `runtime.broker_state` | `/internal_broker/start`, `/internal_broker/stop`, `/internal_broker/status`, `/internal_broker/save` |
| `runtime.config_cache` | `/settings*`, `/save*`, `/topics*`, Mapping-Save-Routen, Template Import/Export, Objects |

## Betroffene Services

| Service | State-Beruehrung | Empfehlung |
|---|---|---|
| `app/services/runtime.py` | Live-Log, Status-SSE, Broker-Helfer | Spaeter RuntimeContext-Hauptmodul oder Context-Nutzer |
| `app/services/mqtt.py` | `mqtt_monitor_values`, `mqtt_clients`, `mqtt_client` | State in `runtime.mqtt_monitor` oder Context verschieben |
| `app/services/udp.py` | `mqtt2udp_last_seen`, `udp2mqtt_last_seen`, `udp_input_last_seen` | State in `runtime.udp_state` sammeln |
| `app/services/knx.py` | nutzt Monitor nur ueber Callback, aber Bridge-Funktionen schreiben Last-Seen | Monitorliste nicht duplizieren; spaeter Context uebergeben |
| `app/services/config.py` | Pfade, Defaults, JSON-Lock | Pfade/Lock entweder dort belassen oder neutral in ConfigContext kapseln |
| `app/services/object.py` | Config-Loader/Saver ueber Parameter | Kann zunaechst context-los bleiben |
| `app/services/influx.py` | Config-Loader und Delete/Query | Kann zunaechst context-los bleiben |
| `app/services/backup.py` | Pfade/Backup-Dateien | Kann zunaechst context-los bleiben |

## KNX Detailplan

Die KNX-Migration wird vorsichtig nach dem separaten Detailplan `KNX_RUNTIME_MIGRATION_PLAN.md` umgesetzt. Phase A ist seit 32.4.2 erledigt: die KNX-LastSeen-Dicts werden im RuntimeContext gepflegt. Phase B ist seit 32.4.3 erledigt: `knx_monitor_values` wird im RuntimeContext gepflegt. Phase C ist seit 32.4.4 erledigt: `knx_monitor_log` wird im RuntimeContext gepflegt. Phase D1 ist seit 32.4.5 erledigt: die KNX-Listener-Verwaltung liegt in `runtime_context.knx`. Phase E ist seit 32.4.6 erledigt: `sse_versions["knx"]` wurde durch `runtime_context.knx.monitor_version` ersetzt. Seit 32.4.7 sind die alten KNX-Globals entfernt.

Empfohlene Reihenfolge:

1. Nur KNX-LastSeen-Dicts. Erledigt in 32.4.2.
2. Monitor-Werte. Erledigt in 32.4.3.
3. Monitor-Log. Erledigt in 32.4.4.
4. Listener-Verwaltung. D1 erledigt in 32.4.5.
5. SSE-Versionierung. Erledigt in 32.4.6.

## Groesste Risiken

1. Bridge Start/Stop nutzt mehrere RuntimeContext-Felder und Threads: `runtime_context.bridge.thread`, `running`, `stop_requested`, `status`.
2. KNX Monitor schreibt aus Listener-/Callback-Kontext in `knx_monitor_log` und `knx_monitor_values`, waehrend JSON/SSE-Routen lesen.
3. MQTT- und UDP-State werden im RuntimeContext gespiegelt; alte MQTT-/UDP-Globals laufen bewusst parallel.
4. `sse_versions` koordiniert die verbleibenden Eventstream-Bereiche ohne expliziten Lock; KNX nutzt seit 32.4.6 `runtime_context.knx.monitor_version`.
5. `mqtt_client`, `ws` und `main_loop` verbinden Threading, asyncio und externe Netzwerkverbindungen.
6. Broker-Prozess-Lifecycle liegt seit 32.4.0 im RuntimeContext, muss aber im Betrieb mit Mosquitto getestet werden.

## Empfohlene Reihenfolge

| Reihenfolge | Schritt | Ziel | Risiko |
|---:|---|---|---|
| 1 | Tests/Smoke-Checks fuer Status, Live-Log, MQTT Monitor, KNX Monitor und UDP-Last-Seen dokumentieren | Sicherheitsnetz vor State-Bewegung | niedrig |
| 2 | Vorhandenes Dataclass-Grundgeruest in `app/runtime/` pruefen, aber noch nicht instanziieren | Zielbild klaeren | niedrig |
| 3 | LiveLog-Spiegelung aus 32.3.5 testen; danach erst LiveLog-Routen auf RuntimeContext umstellen | kleiner, gut sichtbarer Bereich | mittel |
| 4 | Bridge-State aus 32.3.7 im Betrieb pruefen und erst danach weitere Runtime-Bereiche migrieren | Status konsolidieren | mittel-hoch |
| 5 | MQTT-Monitor-State aus 32.3.8 und UDP-State aus 32.3.9 im Betrieb testen; danach erst alte parallele Globals entfernen | Callback-State sortieren | hoch |
| 6 | `runtime.knx_monitor` zuletzt anfassen | KNX Listener/SSE ist sensibel | hoch |
| 7 | BrokerState aus 32.4.0 im Betrieb testen; Prozess-Lifecycle und Statusroute pruefen | Prozess-Lifecycle kontrollieren | mittel-hoch |
| 8 | Config-Aliase erst nach Blueprint-Migration reduzieren | Port-Artefakte entfernen | mittel |

## Leitplanken

- Keine Monitorliste in Services duplizieren.
- Keine Thread-/Stop-Flags verschieben, bevor Start/Stop-Smoke-Tests existieren.
- SSE-Routen erst nach klarer Versionierungsstrategie anfassen.
- Context-Objekt zuerst nur einlesen/uebergeben, dann schrittweise Schreibpfade migrieren.
- App-Core-Aliase erst entfernen, wenn Blueprints und Tests stabil sind.
- Das Grundgeruest aus `app/runtime/` ist seit 32.4.7 fuer LiveLog, Bridge-State, MQTT-Monitor-State, UDP-State, Broker-State und KNX-Runtime-State importiert; xknx bleibt unveraendert im App-Core.
- Seit 32.4.7 gibt es fuer KNX Monitor-Log, Monitor-Werte, LastSeen-Dicts und Listener-Thread keine parallelen App-Core-Globals mehr.
