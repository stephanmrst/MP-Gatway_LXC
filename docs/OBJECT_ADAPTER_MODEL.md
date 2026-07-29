# Object Adapter Model V33

## Ziel

Das Adaptermodell beschreibt, wie ein fachliches Objekt mit Protokollen verbunden wird. Ein Objekt kann mehrere Adapter besitzen, zum Beispiel MQTT fuer Status, KNX fuer Schalten, Loxone fuer Visualisierung und Influx fuer Historie.

Diese Datei definiert nur das V33-Zielmodell. Es wird noch keine Runtime angebunden, keine UI geaendert und keine bestehende Mapping-Datei ersetzt.

## Gemeinsame Felder

Jeder Adapter besitzt gemeinsame Verwaltungsfelder:

| Feld | Typ | Bedeutung |
|---|---|---|
| `enabled` | bool | Adapter ist aktiv und darf spaeter fuer Mapping-Vorschlaege oder Synchronisierung verwendet werden. |
| `direction` | string | Richtung des Adapters: `read`, `write` oder `both`. |
| `datatype` | string | Fachlicher Datentyp: `auto`, `bool`, `number`, `text`, `json`, `enum` oder protokollspezifisch erweitert. |
| `readonly` | bool | Adapter darf nur gelesen werden. Entspricht logisch `direction = read`, bleibt aber als klares UI-/Validierungsflag verfuegbar. |
| `writeonly` | bool | Adapter darf nur geschrieben werden. Entspricht logisch `direction = write`, bleibt aber als klares UI-/Validierungsflag verfuegbar. |

Regeln:

- `readonly` und `writeonly` duerfen nicht gleichzeitig aktiv sein.
- `direction = read` setzt fachlich `readonly`.
- `direction = write` setzt fachlich `writeonly`.
- `direction = both` darf weder strikt `readonly` noch strikt `writeonly` sein.
- `datatype = auto` bleibt der sichere Standard fuer bestehende Mappings.

## MQTT Adapter

MQTT verbindet ein Objekt mit einem Topic und optional einem JSON-Key.

| Feld | Bedeutung |
|---|---|
| `topic` | MQTT Topic, zum Beispiel `haus/wohnzimmer/licht/state`. |
| `qos` | MQTT QoS: `0`, `1` oder `2`; Standard fuer bestehende Mappings ist `0`. |
| `retain` | MQTT Retain-Flag fuer Publish-Operationen. |
| `direction` | `read`, `write` oder `both`; beschreibt Subscribe/Publish-Verwendung. |
| `json_key` | Optionaler JSON-Key innerhalb eines Payloads. |
| `datatype` | `auto`, `bool`, `number`, `text`, `json` oder `enum`. |

Validierung:

- `topic` ist Pflicht, wenn der Adapter aktiv ist.
- `qos` muss `0`, `1` oder `2` sein.
- `json_key` ist nur relevant, wenn Payloads JSON enthalten.

## Loxone Adapter

Loxone verbindet ein Objekt mit einem Control, Eingang oder Ausgang.

| Feld | Bedeutung |
|---|---|
| `uuid` | Loxone UUID oder eindeutige IO-/Control-Referenz. |
| `direction` | Richtung: `read`, `write` oder `both`. |
| `datatype` | `auto`, `bool`, `number`, `text` oder ein spaeterer Loxone-spezifischer Typ. |

Validierung:

- `uuid` ist Pflicht, wenn der Adapter aktiv ist.
- Loxone-Schreibadapter muessen spaeter pruefen, ob der Zieltyp beschreibbar ist.

## UDP Adapter

UDP verbindet ein Objekt mit einem Ziel oder Eingang fuer einfache Datagramme.

| Feld | Bedeutung |
|---|---|
| `target_ip` | Ziel-IP fuer ausgehende UDP-Nachrichten. |
| `target_port` | Ziel-Port fuer ausgehende UDP-Nachrichten. |
| `format` | Payload-Format, zum Beispiel `raw`, `json`, `topic_value` oder `text`. |
| `direction` | `read`, `write` oder `both`. |

Validierung:

- Bei `write` oder `both` sind `target_ip` und `target_port` erforderlich.
- `target_port` muss ein gueltiger Port im Bereich `1..65535` sein.
- `format = raw` bleibt der kompatible Standard.

## KNX Adapter

KNX verbindet ein Objekt mit einer Gruppenadresse und einem DPT.

| Feld | Bedeutung |
|---|---|
| `group_address` | KNX Gruppenadresse, zum Beispiel `1/2/3`. |
| `dpt` | KNX DPT, zum Beispiel `1.001`, `5.001`, `9.001`. |
| `direction` | `read`, `write` oder `both`. |

Validierung:

- `group_address` ist Pflicht, wenn der Adapter aktiv ist.
- `group_address` muss normalisiert werden, bevor sie gespeichert oder verglichen wird.
- `dpt = auto` kann spaeter aus Mapping, Wert oder Objektart abgeleitet werden.

## Influx Adapter

Influx beschreibt, wie Objektwerte historisiert werden.

| Feld | Bedeutung |
|---|---|
| `measurement` | Influx Measurement. |
| `field` | Field-Name fuer den Wert. |
| `tags` | Tag-Dict, zum Beispiel Raum, Objektname oder Protokoll. |
| `datatype` | `auto`, `bool`, `number`, `text` oder `json`. |

Validierung:

- `measurement` und `field` sind Pflicht, wenn der Adapter aktiv ist.
- Tags duerfen keine leeren Schluessel enthalten.
- `datatype` muss zur spaeteren Schreibstrategie passen.

## Migrationshinweise

- Bestehende Mapping-Dateien bleiben vorerst fuehrend.
- Adapter koennen spaeter aus bestehenden Mappings abgeleitet werden.
- Schreibende Migrationen brauchen eine Vorschau und klare Konfliktmeldungen.
- Protokollspezifische Felder duerfen in `meta` gespiegelt werden, solange das Datenmodell stabilisiert wird.

## Exit-Kriterien

Das Adaptermodell ist bereit fuer eine aktive Implementierungsphase, wenn:

- alle Adaptertypen validierbare Pflichtfelder besitzen,
- bestehende Mappings ohne Informationsverlust als Adapter dargestellt werden koennen,
- Konflikte zwischen `direction`, `readonly` und `writeonly` eindeutig erkannt werden,
- keine Runtime-Funktion direkt vom Dokumentationsmodell abhaengt,
- bestehende Seiten und Bridges unveraendert laufen.
