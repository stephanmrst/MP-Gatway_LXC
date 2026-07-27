# Blueprint-Migrationsplan 32.3.2

Stand: Analyse von `app/core.py` mit 117 Flask-Routen.

Dies ist nur ein Migrationsplan. Es wurden keine Routen verschoben, keine Blueprint-Dateien angelegt und keine Logik oder UI geaendert.

Seit 32.4.8 beschreibt `LEGACY_REMOVAL_PLAN.md`, wie dieser Blueprint-Plan in die vollstaendige Entfernung von `app/core.py` eingebettet wird.

## Legende

| Markierung | Bedeutung |
|---|---|
| `SSE` | Eventstream-Route mit laufender Verbindung |
| `JSON` | Daten-/API-Route mit JSON-Antwort |
| `WRITE` | POST-/Write-Route oder mutierende Aktion |
| `STATE` | Route liest oder aendert globalen Live-State |

## Empfohlene Reihenfolge

| Reihenfolge | Ziel-Blueprint | Begruendung |
|---:|---|---|
| 1 | `dashboard` | Niedriges Risiko fuer reine Seitenrouten und Shell-Fragmente. |
| 2 | `config` | Settings-Routen sind klar gruppierbar, brauchen aber Save-Regressionstests. |
| 3 | `backup` | Kompakter Bereich mit wenigen Routen. |
| 4 | `objects` | Service existiert bereits; Routen bleiben fachlich geschlossen. |
| 5 | `influx` | Explorer und Write-Routen haben klare Abhaengigkeiten. |
| 6 | `loxone` | Ueberschaubare Mapping-/Test-Routen. |
| 7 | `udp` | Mehr Live-State und Testsendungen, daher nach einfachen Bereichen. |
| 8 | `mqtt` | Grosse Monitor-/Topic-Routen mit viel UI und State. |
| 9 | `api` | JSON-Endpunkte erst migrieren, wenn ihre Domain-Routen stabil sind. |
| 10 | `events` | SSE-Routen wegen Live-Verbindungen und State zuletzt kapseln. |
| 11 | `knx` | KNX Monitor/Listener wegen xknx und Live-State sehr vorsichtig migrieren. |
| 12 | `system` | Bridge Start/Stop und interner Broker zuletzt oder zusammen mit RuntimeContext. |

## Routenplan

| Route | Methode | Aktuelle Funktion | Ziel-Blueprint | Abhaengigkeiten | Markierung | Risiko | Reihenfolge |
|---|---|---|---|---|---|---|---:|
| `/dashboard_embed` | GET | `dashboard_embed` | dashboard | Layout, Dashboard-Renderer |  | niedrig | 1 |
| `/live_log` | GET | `live_log_console` | dashboard | Runtime/Live-Log | STATE | mittel | 1 |
| `/live_log_page` | GET | `live_log_page` | dashboard | Runtime/Live-Log, Layout | STATE | mittel | 1 |
| `/settings_embed` | GET | `settings_embed` | config | Config-Loader, Layout |  | niedrig | 2 |
| `/core_settings_embed` | GET | `core_settings_embed` | config | Config-Loader |  | niedrig | 2 |
| `/mqtt_settings_embed` | GET | `mqtt_settings_embed` | config | MQTT-Config |  | niedrig | 2 |
| `/influx_settings_embed` | GET | `influx_settings_embed` | config | Influx-Config |  | niedrig | 2 |
| `/global_search` | GET | `global_search` | api | Config-Scanner, Suchindex | JSON | mittel | 9 |
| `/conflicts` | GET | `conflicts` | api | Config-Scanner, Validation | JSON | mittel | 9 |
| `/conflicts_page` | GET | `conflicts_page` | dashboard | Conflict-Renderer |  | niedrig | 1 |
| `/global_search_page` | GET | `global_search_page` | dashboard | Search-Renderer |  | niedrig | 1 |
| `/plugins` | GET | `plugins_page` | system | Plugin-Config, Sidebar |  | mittel | 12 |
| `/sidebar_links/save` | POST | `sidebar_links_save` | config | Sidebar-Config | WRITE | mittel | 2 |
| `/plugins/save` | POST | `save_plugins` | system | Plugin-Config | WRITE | mittel | 12 |
| `/shell_status` | GET | `shell_status` | dashboard | Runtime-Status | JSON | niedrig | 1 |
| `/live_log_data` | GET | `live_log_data` | api | Runtime/Live-Log | JSON, STATE | mittel | 9 |
| `/` | GET | `index` | dashboard | Layout, Dashboard |  | niedrig | 1 |
| `/settings` | GET | `settings_page` | config | Config-Loader, Layout |  | niedrig | 2 |
| `/save` | POST | `save` | config | Core-Config | WRITE | mittel | 2 |
| `/save_core` | POST | `save_core` | config | Core-Config | WRITE | mittel | 2 |
| `/internal_broker/save` | POST | `internal_broker_save` | system | Runtime-Service, Broker-Config | WRITE | hoch | 12 |
| `/internal_broker/start` | POST | `internal_broker_start` | system | Runtime-Service, Broker-Prozess | WRITE, STATE | hoch | 12 |
| `/internal_broker/stop` | POST | `internal_broker_stop` | system | Runtime-Service, Broker-Prozess | WRITE, STATE | hoch | 12 |
| `/internal_broker/status` | GET | `internal_broker_status_route` | system | Runtime-Service, Broker-Prozess | JSON, STATE | mittel | 12 |
| `/save_mqtt` | POST | `save_mqtt` | config | MQTT-Config | WRITE | mittel | 2 |
| `/save_influx` | POST | `save_influx` | config | Influx-Config | WRITE | mittel | 2 |
| `/test/loxone` | POST | `test_loxone` | loxone | Loxone-WebSocket, Config | WRITE | mittel | 6 |
| `/test/mqtt` | POST | `test_mqtt` | mqtt | MQTT-Service, Config | WRITE | mittel | 8 |
| `/start` | POST | `start_bridge` | system | Bridge-Thread, Runtime-State | WRITE, STATE | hoch | 12 |
| `/stop` | POST | `stop_bridge` | system | Bridge-Thread, Runtime-State | WRITE, STATE | hoch | 12 |
| `/topics2` | GET | `topics2_page` | mqtt | Topic-Config, Layout |  | mittel | 8 |
| `/topics2/data` | GET | `topics2_data` | api | Topic-Config | JSON | mittel | 9 |
| `/topics2/save` | POST | `topics2_save` | mqtt | Topic-Config | WRITE | mittel | 8 |
| `/topics` | GET | `topics` | mqtt | Topic-Config, grosse UI |  | hoch | 8 |
| `/topics/save` | POST | `topics_save` | mqtt | Topic-Config | WRITE | mittel | 8 |
| `/mqtt2lox` | GET | `mqtt2lox` | loxone | MQTT2Lox-Config, grosse UI |  | hoch | 6 |
| `/mqtt2lox/save` | POST | `mqtt2lox_save` | loxone | MQTT2Lox-Config | WRITE | mittel | 6 |
| `/mqtt2lox/test/<int:index>` | POST | `mqtt2lox_test` | loxone | Loxone-Service, MQTT2Lox-Config | WRITE | mittel | 6 |
| `/mqtt2lox_data` | GET | `mqtt2lox_data` | api | MQTT2Lox-Config | JSON | mittel | 9 |
| `/mqtt2udp` | GET | `mqtt2udp` | udp | UDP-Service, MQTT2UDP-Config | STATE | mittel | 7 |
| `/mqtt2udp/save` | POST | `mqtt2udp_save` | udp | MQTT2UDP-Config | WRITE | mittel | 7 |
| `/mqtt2udp/test/<int:index>` | POST | `mqtt2udp_test` | udp | UDP-Service, MQTT2UDP-Config | WRITE | mittel | 7 |
| `/mqtt2udp_data` | GET | `mqtt2udp_data` | api | MQTT2UDP-Config, Last-Seen-State | JSON, STATE | mittel | 9 |
| `/udp_presets` | GET | `udp_presets` | udp | UDP-Presets | JSON | niedrig | 7 |
| `/udp_presets/save` | POST | `udp_presets_save` | udp | UDP-Presets | WRITE | mittel | 7 |
| `/mqtt2udp/copy/<int:index>` | POST | `mqtt2udp_copy` | udp | MQTT2UDP-Config | WRITE | mittel | 7 |
| `/test/influx` | POST | `test_influx` | influx | Influx-Service, Config | WRITE | mittel | 5 |
| `/monitor` | GET | `monitor` | mqtt | MQTT-Monitor-State, grosse UI | STATE | hoch | 8 |
| `/clear_monitor` | GET | `clear_monitor` | mqtt | Monitor-/Live-Log-State | WRITE, STATE | hoch | 8 |
| `/clear_log` | GET | `clear_log` | dashboard | Live-Log-State | WRITE, STATE | mittel | 1 |
| `/topics_data` | GET | `topics_data` | api | Topic-Config | JSON | mittel | 9 |
| `/mqtt` | GET | `mqtt_hub` | mqtt | MQTT-Hub Layout |  | niedrig | 8 |
| `/knx` | GET | `knx_hub` | knx | KNX-Hub Layout |  | niedrig | 11 |
| `/udp2knx` | GET | `udp2knx` | knx | UDP2KNX-Config, KNX-Service |  | mittel | 11 |
| `/udp2knx_data` | GET | `udp2knx_data` | api | UDP2KNX-Config | JSON | mittel | 9 |
| `/udp2knx/save` | POST | `udp2knx_save` | knx | UDP2KNX-Config | WRITE | mittel | 11 |
| `/udp2knx/test/<int:index>` | POST | `udp2knx_test` | knx | KNX-Service, UDP2KNX-Config | WRITE | hoch | 11 |
| `/knx2lox` | GET | `knx2lox` | knx | KNX2Lox-Config |  | mittel | 11 |
| `/knx2lox_data` | GET | `knx2lox_data` | api | KNX2Lox-Config | JSON | mittel | 9 |
| `/knx2lox/save` | POST | `knx2lox_save` | knx | KNX2Lox-Config | WRITE | mittel | 11 |
| `/knx_settings_embed` | GET | `knx_settings_embed` | knx | KNX-Config |  | niedrig | 11 |
| `/mqtt2knx` | GET | `mqtt2knx` | knx | MQTT2KNX-Config |  | mittel | 11 |
| `/knx/save` | POST | `knx_save` | knx | KNX-Config | WRITE | hoch | 11 |
| `/knx/test` | POST | `knx_test` | knx | xknx, KNX-Config | WRITE | hoch | 11 |
| `/mqtt2knx/save` | POST | `mqtt2knx_save` | knx | MQTT2KNX-Config | WRITE | mittel | 11 |
| `/mqtt2knx/test/<int:index>` | POST | `mqtt2knx_test` | knx | KNX-Service, MQTT2KNX-Config | WRITE | hoch | 11 |
| `/mqtt2knx_data` | GET | `mqtt2knx_data` | api | MQTT2KNX-Config | JSON | mittel | 9 |
| `/knx2mqtt` | GET | `knx2mqtt` | knx | KNX2MQTT-Config |  | mittel | 11 |
| `/knx2mqtt/save` | POST | `knx2mqtt_save` | knx | KNX2MQTT-Config | WRITE | mittel | 11 |
| `/knx2mqtt_data` | GET | `knx2mqtt_data` | api | KNX2MQTT-Config | JSON | mittel | 9 |
| `/knx_monitor` | GET | `knx_monitor` | knx | KNX-Monitor-State, Listener, grosse UI | STATE | hoch | 11 |
| `/knx_monitor/influx` | POST | `knx_monitor_influx` | knx | KNX-Monitor, Influx-Config | WRITE, STATE | hoch | 11 |
| `/knx_monitor/influx_type` | POST | `knx_monitor_influx_type` | knx | KNX-Monitor, Influx-Config | WRITE, STATE | hoch | 11 |
| `/knx_monitor/influx_topic` | POST | `knx_monitor_influx_topic` | knx | KNX-Monitor, Influx-Config | WRITE, STATE | hoch | 11 |
| `/knx_listener_start` | POST | `knx_listener_start` | knx | KNX-Listener, xknx | WRITE, STATE | hoch | 11 |
| `/knx_monitor_data` | GET | `knx_monitor_data` | api | KNX-Monitor-Log | JSON, STATE | hoch | 9 |
| `/events/status` | GET | `events_status` | events | Runtime-Status-SSE | SSE, STATE | hoch | 10 |
| `/events/live_log` | GET | `events_live_log` | events | Live-Log-SSE | SSE, STATE | hoch | 10 |
| `/events/live_log_full` | GET | `events_live_log_full` | events | Live-Log-SSE | SSE, STATE | hoch | 10 |
| `/events/mqtt_monitor` | GET | `events_mqtt_monitor` | events | MQTT-Monitor-SSE | SSE, STATE | hoch | 10 |
| `/events/knx_monitor` | GET | `events_knx_monitor` | events | KNX-Monitor-SSE | SSE, STATE | hoch | 10 |
| `/templates` | GET | `mapping_templates_page` | config | Mapping-Template-Service |  | mittel | 2 |
| `/templates/export` | POST | `templates_export` | config | Mapping-Template-Service | JSON, WRITE | mittel | 2 |
| `/templates/import` | POST | `templates_import` | config | Mapping-Template-Service | WRITE | mittel | 2 |
| `/backup` | GET | `backup_config` | backup | Backup-Service |  | niedrig | 3 |
| `/restore` | POST | `restore_config` | backup | Backup-Service, Dateiupload | WRITE | mittel | 3 |
| `/udp2mqtt` | GET | `udp2mqtt` | udp | UDP2MQTT-Config, Last-Seen-State | STATE | mittel | 7 |
| `/udp2mqtt/save` | POST | `udp2mqtt_save` | udp | UDP2MQTT-Config | WRITE | mittel | 7 |
| `/udp2mqtt/test/<int:index>` | POST | `udp2mqtt_test` | udp | MQTT-Client, UDP2MQTT-Config | WRITE, STATE | hoch | 7 |
| `/udp2mqtt_data` | GET | `udp2mqtt_data` | api | UDP2MQTT-Config, Last-Seen-State | JSON, STATE | mittel | 9 |
| `/udp_input` | GET | `udp_input_page` | udp | UDP-Input-State, Presets | STATE | mittel | 7 |
| `/udp_input/save` | POST | `udp_input_save` | udp | UDP-Input-Config | WRITE | mittel | 7 |
| `/udp_input/test` | POST | `udp_input_test` | udp | UDP-Service | WRITE | mittel | 7 |
| `/udp_input_data` | GET | `udp_input_data` | api | UDP-Input-State | JSON, STATE | mittel | 9 |
| `/mqtt_brokers` | GET | `mqtt_brokers_page` | mqtt | MQTT-Broker-Config |  | mittel | 8 |
| `/test/mqtt_broker/<int:index>` | POST | `test_mqtt_broker` | mqtt | MQTT-Service | WRITE | mittel | 8 |
| `/mqtt_brokers/save` | POST | `mqtt_brokers_save` | mqtt | MQTT-Broker-Config | WRITE | mittel | 8 |
| `/udp_discovery_status` | GET | `udp_discovery_status` | api | UDP-Discovery-State | JSON, STATE | mittel | 9 |
| `/udp_discovery_toggle` | POST | `udp_discovery_toggle` | udp | UDP-Discovery-State | WRITE, STATE | mittel | 7 |
| `/monitor_data` | GET | `monitor_data` | api | MQTT-Monitor-State | JSON, STATE | hoch | 9 |
| `/monitor_settings` | GET | `monitor_settings` | api | Monitor-Settings | JSON | niedrig | 9 |
| `/monitor_topic_config` | GET | `monitor_topic_config` | api | Topic-Config | JSON | mittel | 9 |
| `/monitor/influx_topic` | POST | `monitor_influx_topic` | mqtt | Monitor-Topic-Config, Influx | WRITE, STATE | hoch | 8 |
| `/monitor/influx_json_key` | POST | `monitor_influx_json_key` | mqtt | Monitor-Topic-Config, Influx | WRITE, STATE | hoch | 8 |
| `/monitor/influx_json_key_type` | POST | `monitor_influx_json_key_type` | mqtt | Monitor-Topic-Config, Influx | WRITE, STATE | hoch | 8 |
| `/monitor/favorite` | POST | `monitor_favorite` | mqtt | Monitor-Topic-Config | WRITE, STATE | mittel | 8 |
| `/monitor/alias` | POST | `monitor_alias` | mqtt | Monitor-Topic-Config | WRITE, STATE | mittel | 8 |
| `/influx_explorer` | GET | `influx_explorer` | influx | Influx-Service, Layout |  | mittel | 5 |
| `/influx_explorer/delete` | POST | `influx_explorer_delete` | influx | Influx-Service | WRITE | hoch | 5 |
| `/influx_explorer/delete_selected` | POST | `influx_explorer_delete_selected` | influx | Influx-Service | WRITE | hoch | 5 |
| `/objects` | GET | `objects` | objects | Object-Service |  | mittel | 4 |
| `/objects/edit/<object_id>` | GET | `objects_edit` | objects | Object-Service |  | mittel | 4 |
| `/objects/sync_from_mappings` | POST | `objects_sync_from_mappings` | objects | Object-Service, Mapping-Configs | WRITE | hoch | 4 |
| `/objects/rebuild_mappings` | POST | `objects_rebuild_mappings` | objects | Object-Service, Mapping-Configs | WRITE | hoch | 4 |
| `/objects/save` | POST | `objects_save` | objects | Object-Service | WRITE | mittel | 4 |
| `/objects/delete` | POST | `objects_delete` | objects | Object-Service | WRITE | mittel | 4 |
| `/objects/delete_all` | POST | `objects_delete_all` | objects | Object-Service | WRITE | hoch | 4 |

## Blueprint-Zusammenfassung

| Ziel-Blueprint | Route-Anzahl | Hinweise |
|---|---:|---|
| `dashboard` | 8 | Startseite, Shell, Live-Log-Seiten und einfache UI-Fragmente. |
| `mqtt` | 16 | MQTT Hub, Monitor, Topics, Broker und Monitor-Schreibaktionen. |
| `loxone` | 4 | MQTT->Loxone Seite, Save/Test und Loxone-Verbindungstest. |
| `udp` | 13 | MQTT/UDP-Mappings, UDP Input, Presets und Discovery. |
| `knx` | 19 | KNX Hub, Settings, Mappings, Monitor und Listener-Start. |
| `influx` | 4 | Influx-Test und Explorer inklusive Delete-Routen. |
| `objects` | 7 | Objektmanager und Mapping-Sync/Rebuild. |
| `config` | 13 | Settings, Saves, Template Import/Export, Sidebar. |
| `backup` | 2 | Backup und Restore. |
| `api` | 18 | JSON-/Daten-Endpunkte aus mehreren Domains. |
| `events` | 5 | SSE-Endpunkte fuer Status, Live-Log, MQTT und KNX. |
| `system` | 8 | Bridge, Broker und Plugin-System. |

## Besondere Risikogruppen

### SSE/Eventstream-Routen

- `/events/status`
- `/events/live_log`
- `/events/live_log_full`
- `/events/mqtt_monitor`
- `/events/knx_monitor`

Diese Routen sollten erst migriert werden, wenn ein `RuntimeContext` fuer Live-State und SSE-Versionen vorbereitet ist.

### JSON-Datenrouten

- `/global_search`, `/conflicts`, `/shell_status`, `/live_log_data`
- alle `*_data`-Routen fuer MQTT, UDP, KNX und Monitor
- `/monitor_settings`, `/monitor_topic_config`, `/udp_discovery_status`

Diese Routen eignen sich fuer `api`, sollten aber erst nach ihren fachlichen Seiten smoke-getestet werden.

### POST-/Write-Routen

Alle Save-, Test-, Delete-, Start-/Stop- und Import-/Export-Routen sind Write-Routen. Vor einer Blueprint-Migration sollten Form-Submit, Redirect, Flash/Log-Ausgabe und JSON-Response pro Route geprueft werden.

### Routen mit globalem State

Besonders sensibel:

- Bridge: `/start`, `/stop`
- Broker: `/internal_broker/start`, `/internal_broker/stop`, `/internal_broker/status`
- Live-Log: `/live_log*`, `/clear_log`, `/events/live_log*`
- MQTT Monitor: `/monitor`, `/monitor_data`, `/events/mqtt_monitor`, `/monitor/*`
- KNX Monitor: `/knx_monitor`, `/knx_monitor_data`, `/events/knx_monitor`, `/knx_listener_start`
- UDP Last-Seen/Discovery: `/mqtt2udp*`, `/udp2mqtt*`, `/udp_input*`, `/udp_discovery_*`

## Migrationsleitplanken

1. Zuerst Blueprints registrieren und Routen 1:1 verschieben, ohne fachliche Funktionen zu veraendern.
2. Jede Route nach dem Verschieben mit gleicher URL, gleicher Methode und gleicher Antwortart pruefen.
3. `events` und KNX-Monitor-Routen erst migrieren, wenn Status/SSE/Monitor-Smoke-Tests existieren.
4. `system`-Routen fuer Bridge und Broker zuletzt verschieben.
5. App-Core-Wrapper erst entfernen, wenn keine Route mehr direkt darauf angewiesen ist.
