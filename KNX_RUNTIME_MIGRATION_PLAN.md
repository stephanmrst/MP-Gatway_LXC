# KNX Runtime Migration Plan 32.4.7

Stand: Analyse von `app/core.py` und `app/services/knx.py`.

Phase A ist seit 32.4.2 umgesetzt: Die KNX-LastSeen-Dicts fuer MQTT->KNX, KNX->MQTT und KNX->Loxone werden in `runtime_context.knx` gepflegt und von den betroffenen KNX-Seiten gelesen. Phase B ist seit 32.4.3 umgesetzt: `knx_monitor_values` liegt in `runtime_context.knx.monitor_values`. Phase C ist seit 32.4.4 umgesetzt: `knx_monitor_log` liegt in `runtime_context.knx.monitor_log`. Phase D1 ist seit 32.4.5 umgesetzt: Die KNX-Listener-Verwaltung liegt in `runtime_context.knx`. Phase E ist seit 32.4.6 umgesetzt: `sse_versions["knx"]` wurde durch `runtime_context.knx.monitor_version` ersetzt. Seit 32.4.7 sind die alten KNX-Global-State-Reste in `app/core.py` entfernt. xknx bleibt unveraendert im App-Core.

## Ziel

KNX ist der sensibelste Runtime-Bereich, weil Listener, xknx-Callbacks, AsyncIO, Monitor-SSE und mehrere Bridge-Richtungen zusammenlaufen. Die Migration soll deshalb nicht in einem Schritt erfolgen, sondern von einfachen Last-Seen-Dicts bis zur SSE-Versionierung.

## Erkannte KNX-States

| Variable | Typ | Zweck | liest | schreibt | Routen | Services | Thread-/Async-Risiko | SSE-Risiko | Empfehlung |
|---|---|---|---|---|---|---|---|---|---|
| `runtime_context.knx.monitor_log` | `deque(maxlen=15)` | Zentrale KNX-Monitor-Liste fuer RX/TX-Telegramme. Seit 32.4.4 bevorzugte Lesequelle; alter Deque bleibt parallel. | `knx_monitor_payload`, `/knx_monitor_data`, `/events/knx_monitor` indirekt | `add_knx_monitor_entry` spiegelt ueber Wrapper | `/knx_monitor`, `/knx_monitor_data`, `/events/knx_monitor` | `knx_service` indirekt per Callback `add_monitor_entry` | hoch: xknx Callback/Listener schreibt, HTTP/SSE liest | hoch | umgesetzt in Phase C |
| `runtime_context.knx.monitor_values` | `dict` | Letzter KNX-Wert pro Gruppenadresse. Seit 32.4.3 bevorzugte Lesequelle; alter Dict bleibt parallel. | `knx_monitor_payload`, `knx_hub_content`, `/knx_monitor_data` indirekt | `add_knx_monitor_entry` spiegelt ueber Wrapper | `/knx`, `/knx_monitor`, `/knx_monitor_data`, `/events/knx_monitor` | indirekt ueber Monitor-Callback | hoch: geteilter Dict zwischen Listener und Routes | hoch | umgesetzt in Phase B |
| `runtime_context.knx.listener_thread` | `threading.Thread` oder `None` | Separater KNX Listener fuer Live-Monitor und KNX-Empfang. Seit 32.4.5 primaere Thread-Referenz. | `ensure_knx_listener_started`, Listener-Wrapper | `ensure_knx_listener_started`, Listener-Wrapper | `/knx_listener_start`, `/knx_monitor` indirekt | xknx, App-Core Listener | sehr hoch: Thread-Lifecycle, Auto-Start, xknx | mittel | umgesetzt in Phase D1 |
| `runtime_context.knx.listener_running` | `bool` | Gepufferter Running-State der Listener-Verwaltung. | Listener-Wrapper | `ensure_knx_listener_started`, Listener-Wrapper | `/knx_listener_start`, `/knx_monitor` indirekt | App-Core Listener-Verwaltung | mittel-hoch: Thread-Zustand wird aus `is_alive()` aktualisiert | niedrig | umgesetzt in Phase D1 |
| `runtime_context.knx.start_requested` | `bool` | Start-Anforderung der Listener-Verwaltung. | Listener-Wrapper | `request_knx_start` | `/knx_listener_start`, `/knx_monitor` indirekt | App-Core Listener-Verwaltung | mittel | niedrig | umgesetzt in Phase D1 |
| `runtime_context.knx.stop_requested` | `bool` | Stop-Anforderung der Listener-Verwaltung, aktuell nur vorbereitet. | Listener-Wrapper | `request_knx_stop` | keine direkte Route | App-Core Listener-Verwaltung | mittel | niedrig | umgesetzt in Phase D1 |
| `runtime_context.knx.mqtt2knx_last_seen` | `dict` | Letzter MQTT->KNX Treffer pro MQTT-Topic. Seit 32.4.2 bevorzugte Lesequelle; alter Dict bleibt parallel. | `mqtt2knx`, `mqtt2knx_data` | `knx_service.handle_mqtt_to_knx` per optionalem Callback | `/mqtt2knx`, `/mqtt2knx_data`, `/mqtt2knx/test/<int:index>` | `app/services/knx.py` | mittel: MQTT Callback/Route schreibt, UI liest | niedrig | umgesetzt in Phase A |
| `runtime_context.knx.knx2mqtt_last_seen` | `dict` | Letzter KNX->MQTT Treffer pro Gruppenadresse. Seit 32.4.2 bevorzugte Lesequelle; alter Dict bleibt parallel. | `knx2mqtt`, `knx2mqtt_data` | `_knx_listener_async` via `knx_service.publish_knx_to_mqtt` und optionalem Callback | `/knx2mqtt`, `/knx2mqtt_data` | `knx_service.publish_knx_to_mqtt` | hoch: xknx Callback schreibt | niedrig-mittel | umgesetzt in Phase A |
| `udp2knx_last_seen` | `dict` | Letzter UDP->KNX Treffer pro UDP-Topic. Liegt seit 32.3.9 zusaetzlich in `runtime_context.udp`. | `udp2knx`, `udp2knx_data` | `_handle_udp_to_knx_service`, `knx_service.handle_udp_to_knx` | `/udp2knx`, `/udp2knx_data`, `/udp2knx/test/<int:index>` | `knx_service`, UDP RuntimeState | mittel-hoch: UDP Listener/Route schreibt | niedrig | vorerst `runtime.udp.udp2knx_last_seen`, spaeter Schnitt zu `runtime.knx` klaeren |
| `runtime_context.knx.knx2lox_last_seen` | `dict` | Letzter KNX->Loxone Treffer pro Gruppenadresse. Seit 32.4.2 bevorzugte Lesequelle; alter Dict bleibt parallel. | `knx2lox`, `knx2lox_data` | `_knx_listener_async` via `knx_service.publish_knx_to_loxone` und optionalem Callback | `/knx2lox`, `/knx2lox_data` | `knx_service.publish_knx_to_loxone`, `requests` | hoch: xknx Callback schreibt, HTTP-Request an Loxone | niedrig-mittel | umgesetzt in Phase A |
| `runtime_context.knx.monitor_version` | `int` | Aenderungsversion fuer KNX-Monitor-SSE. Seit 32.4.6 Ersatz fuer `sse_versions["knx"]`. | `sse_response`, `/events/knx_monitor` indirekt | `bump_sse("knx")` in `add_knx_monitor_entry` | `/events/knx_monitor` | keine direkte Service-Abhaengigkeit | mittel: Runtime-Lock vorhanden | hoch | umgesetzt in Phase E |
| `telegram_received_cb` | xknx Callback-Funktion | Empfang von KNX-Telegrammen, Monitor-Update, KNX->MQTT, KNX->Loxone. | xknx Telegram Queue | registriert in `_knx_listener_async` | indirekt `/knx_listener_start`, `/knx_monitor` | xknx, `knx_service` | sehr hoch: Fremdcallback in Listener-Kontext | hoch, weil Monitor-SSE getriggert wird | erst nach Monitor-State migrieren |
| `xknx` | lokale XKNX-Instanz | KNX-Verbindung in Listener und Sendefunktionen. | `_knx_listener_async`, `_send_knx_xknx` | lokale Funktion | indirekt alle KNX-Live-Pfade | xknx | sehr hoch: AsyncIO, Start/Stop, Gateway | mittel | bleibt lokal bis Listener-Migration |
| `ConnectionConfig`/`ConnectionType` | lokale xknx-Konfiguration | Tunneling/Routing-Verbindung zum KNX-Gateway. | Listener und Sendefunktion | aus `load_knx_config()` | KNX Settings/Test/Listener | xknx | mittel-hoch | niedrig | bleibt lokal |
| `runtime_context.bridge.stop_requested` | RuntimeContext-Flag | Stop-Signal fuer Bridge und aktuell auch KNX Listener Loop. | `_knx_listener_async` | Bridge Start/Stop | `/start`, `/stop`, indirekt KNX Listener | Bridge Runtime | hoch: Cross-Domain-Abhaengigkeit | niedrig | spaeter eigenes `runtime.knx.stop_requested` pruefen |

## Wichtige Funktionen

| Funktion | Datei | Bedeutung | Risiko | Migrationshinweis |
|---|---|---|---|---|
| `add_knx_monitor_entry` | `app/core.py` | Schreibt alten `knx_monitor_log`, alten `knx_monitor_values`, RuntimeContext-Spiegel, Influx und `bump_sse("knx")`. | sehr hoch | Grundlogik nicht umbauen; Listener und SSE erst spaeter migrieren. |
| `knx_monitor_payload` | `app/core.py` | Baut Payload fuer JSON und SSE aus Monitor-State. | hoch | Monitor-Werte und Monitor-Log lesen seit 32.4.4 bevorzugt aus RuntimeContext. |
| `_knx_listener_async` | `app/core.py` | Startet xknx, registriert Telegrammcallback, verarbeitet RX und stoppt bei Bridge-Stop. | sehr hoch | Zuletzt anfassen; Listener bleibt bis Tests stabil sind im App-Core. |
| `knx_listener_runner` | `app/core.py` | Fuehrt `_knx_listener_async` via `asyncio.run` im Thread aus. | hoch | Erst nach Listener-Thread-Plan migrieren. |
| `ensure_knx_listener_started` | `app/core.py` | Auto-/Manual-Start des Listener-Threads. | hoch | Nutzt seit 32.4.5 RuntimeContext-Wrapper; Listener selbst bleibt unveraendert. |
| `/knx_listener_start` | `app/core.py` | Manueller Listener-Start. | hoch | Erst mit Listener-Thread-Migration umstellen. |
| `/knx_monitor_data` | `app/core.py` | JSON-Payload und Debugprint `[KNX MONITOR DATA]`. | mittel-hoch | Nach Monitor-Werte/Log-Migration umstellen. |
| `/events/knx_monitor` | `app/core.py` | SSE-Payload und Debugprint `[KNX SSE]`. | sehr hoch | Nutzt seit 32.4.6 indirekt `runtime_context.knx.monitor_version`; Route selbst bleibt unveraendert. |
| `knx_service.handle_mqtt_to_knx` | `app/services/knx.py` | MQTT->KNX Mapping und Last-Seen. | mittel | Optionalen Callback oder RuntimeContext-Wrapper wie bei UDP planen. |
| `knx_service.handle_udp_to_knx` | `app/services/knx.py` | UDP->KNX Mapping und Last-Seen. | mittel | Ist bereits mit UDP-State gekoppelt; keine Doppelquelle erzeugen. |
| `knx_service.publish_knx_to_mqtt` | `app/services/knx.py` | KNX->MQTT Mapping und Last-Seen. | hoch | Schreibt aus Listener-Callback. |
| `knx_service.publish_knx_to_loxone` | `app/services/knx.py` | KNX->Loxone HTTP-Weiterleitung und Last-Seen. | hoch | Schreibt aus Listener-Callback und macht Netzwerk-I/O. |
| `knx_service.send_knx_value` | `app/services/knx.py` | TX via xknx, ruft optional `add_monitor_entry`. | hoch | Monitor-Callback muss nach Migration weiter zentral schreiben. |

## Betroffene Routen

| Route | Bereich | State | Risiko |
|---|---|---|---|
| `/knx` | KNX Hub | `knx_monitor_values`, Last-Seen-Zaehlung | mittel |
| `/knx_monitor` | Monitor UI | Listener Auto-Start, Monitor-State | hoch |
| `/knx_monitor_data` | JSON | `knx_monitor_log`, `knx_monitor_values` | hoch |
| `/events/knx_monitor` | SSE | Monitor-Payload, `runtime_context.knx.monitor_version` | sehr hoch |
| `/knx_listener_start` | POST | `knx_listener_thread` | hoch |
| `/mqtt2knx`, `/mqtt2knx_data`, `/mqtt2knx/test/<int:index>` | MQTT->KNX | `mqtt2knx_last_seen` | mittel |
| `/udp2knx`, `/udp2knx_data`, `/udp2knx/test/<int:index>` | UDP->KNX | `udp2knx_last_seen` und `runtime_context.udp` | mittel |
| `/knx2mqtt`, `/knx2mqtt_data` | KNX->MQTT | `knx2mqtt_last_seen` | hoch |
| `/knx2lox`, `/knx2lox_data` | KNX->Loxone | `knx2lox_last_seen` | hoch |

## xknx / AsyncIO / Callback-Bezuege

- `_knx_listener_async` erzeugt eine lokale `XKNX`-Instanz und ruft `await xknx.start()`.
- Der Listener registriert `telegram_received_cb` ueber `xknx.telegram_queue.register_telegram_received_cb` oder `register_telegram_received_callback`.
- `telegram_received_cb` schreibt Monitor-State, KNX->MQTT und KNX->Loxone Last-Seen aus dem xknx-Kontext.
- Der Listener laeuft in `knx_listener_thread`, gestartet durch `ensure_knx_listener_started`.
- `knx_listener_runner` startet den AsyncIO-Kontext mit `asyncio.run(_knx_listener_async(knx_cfg))`.
- `knx_service.send_knx_value` nutzt `asyncio.run(_send_knx_xknx(...))`; bei bereits laufendem Eventloop wird ein Worker-Thread gestartet.
- Aktuell stoppt der Listener anhand von `runtime_context.bridge.stop_requested`. Eine spaetere KNX-State-Migration sollte pruefen, ob ein eigenes KNX-Stop-Flag noetig ist.

## Empfohlene Migrationsreihenfolge

| Schritt | Umfang | Empfehlung | Risiko |
|---|---|---|---|
| A | Nur LastSeen-Dicts | Erledigt in 32.4.2: `mqtt2knx_last_seen`, `knx2mqtt_last_seen`, `knx2lox_last_seen` werden in `runtime_context.knx` gespiegelt und bevorzugt gelesen. `udp2knx_last_seen` bleibt in `runtime_context.udp`. | mittel |
| B | Monitor-Werte | Erledigt in 32.4.3: `knx_monitor_values` wird in `runtime_context.knx.monitor_values` gespiegelt und Leser bevorzugt umgestellt. | hoch |
| C | Monitor-Log | Erledigt in 32.4.4: `knx_monitor_log` wird in `runtime_context.knx.monitor_log` gespiegelt und Leser bevorzugt umgestellt. `add_knx_monitor_entry` bleibt zentrale Schreibstelle. | hoch |
| D1 | Listener-Verwaltung | Erledigt in 32.4.5: `listener_thread`, `listener_running`, `start_requested` und `stop_requested` liegen in `runtime_context.knx`; `_knx_listener_async`, Callback, xknx und asyncio bleiben unveraendert. | hoch |
| D2 | Listener-Thread/Stop-Semantik | Spaeter pruefen, ob eigener KNX Stop-State den Bridge-Stop ergaenzen soll. | sehr hoch |
| E | SSE-Versionierung | Erledigt in 32.4.6: `sse_versions["knx"]` wurde durch `runtime_context.knx.monitor_version` ersetzt. | hoch |
| Cleanup | Alte KNX-Globals | Erledigt in 32.4.7: App-Core-Globals fuer KNX Monitor-Log, Monitor-Werte, LastSeen-Dicts und Listener-Thread entfernt. | mittel |

## Vorgeschlagene KNXState-Zielstruktur

```python
@dataclass
class KNXState:
    monitor_log: deque
    monitor_values: dict
    mqtt2knx_last_seen: dict
    knx2mqtt_last_seen: dict
    knx2lox_last_seen: dict
    listener_thread: object
    listener_running: bool
    start_requested: bool
    stop_requested: bool
    monitor_version: int
    lock: RLock
```

`udp2knx_last_seen` sollte vorerst in `runtime_context.udp` bleiben, weil es durch UDP Input und UDP-Routen geschrieben wird. Bei einer spaeteren Domain-Trennung kann es entweder gespiegelt oder als gemeinsamer Mapping-State dokumentiert werden.

## Smoke-Tests vor jeder Migration

1. KNX Monitor oeffnet.
2. KNX Telegramm erzeugen.
3. Terminal zeigt `[KNX MONITOR ADD]`.
4. Terminal zeigt `[KNX SSE]` mit Wert groesser 0.
5. `/knx_monitor_data` liefert `log`-Eintraege.
6. MQTT->KNX Test funktioniert.
7. UDP->KNX Test funktioniert.
8. KNX->MQTT Empfang funktioniert.
9. KNX->Loxone Empfang funktioniert.
10. Dashboard, LiveLog und Status-SSE bleiben stabil.

## Leitplanken

- Keine zweite KNX-Monitor-Liste im Service anlegen.
- `add_knx_monitor_entry` bleibt bis zur Migration die zentrale Schreibstelle fuer Monitor-Log und Monitor-Werte.
- xknx-Listener erst migrieren, wenn Last-Seen, Monitor-Werte und Monitor-Log stabil im RuntimeContext laufen.
- SSE-Versionierung erst anfassen, wenn `/events/knx_monitor` per Smoke-Test abgesichert ist.
- `udp2knx_last_seen` nicht unkoordiniert aus `runtime_context.udp` herausziehen.
