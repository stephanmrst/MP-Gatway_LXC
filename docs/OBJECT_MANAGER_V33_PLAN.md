# Object Manager V33 Plan

## Leitbild

Ein Objekt. Alle Protokolle.

V33 soll den Objektmanager zur zentralen fachlichen Sicht machen. Ein Raum, ein Sensor, ein Aktor oder ein virtueller Zustand soll als ein Objekt beschrieben werden; MQTT, Loxone, UDP, KNX und Influx werden daran als Adapter angebunden.

## Ziel

Der Objektmanager wird schrittweise zur zentralen Datenquelle fuer:

- Anzeigenamen, Raum, Typ und fachliche Beschreibung.
- Protokolladressen und technische Endpunkte.
- Mapping-Erzeugung und Mapping-Abgleich.
- Influx-Schreibentscheidungen und Feldtypen.
- Spaetere Validierung von Dubletten, Konflikten und fehlenden Verknuepfungen.

Bestehende Mapping-Dateien bleiben vorerst die aktive Laufzeitquelle. V33 fuehrt zunaechst ein Modell und einen Migrationspfad ein, ohne bestehende Bridge-, Monitor- oder Protokollfunktionen umzubauen.

## Kompatibilitaet

Bestehende Mappings bleiben kompatibel:

- `mqtt2lox.json`
- `mqtt2udp_config.json`
- `udp2mqtt.json`
- `mqtt2knx.json`
- `udp2knx.json`
- `knx2mqtt.json`
- `knx2lox.json`
- `topic_config.json`
- `monitor_settings.json`

Die erste V33-Phase darf keine bestehenden Mappings entfernen, umbenennen oder automatisch ersetzen. Objekte koennen spaeter als Quelle fuer neue oder synchronisierte Mappings dienen, aber die Runtime liest weiterhin die bekannten Dateien, bis eine eigene Migrationsphase abgeschlossen ist.

## Objektmodell V33

Ein `ObjectDefinition` beschreibt ein fachliches Objekt.

Kernfelder:

- `id`: stabile technische ID.
- `name`: Anzeigename.
- `room`: Raum oder Bereich.
- `type`: fachlicher Typ, zum Beispiel Sensor, Schalter, Licht, Temperatur, Kontakt.
- `enabled`: globale Aktivierung des Objekts.
- `notes`: Freitext fuer Betrieb und Migration.
- `tags`: spaetere Gruppierung und Suche.
- `adapters`: Protokolladapter pro Objekt.
- `flags`: optionale Steuerflags fuer Sync, Influx, Tests und Migration.

Das Modell soll bewusst fachlich bleiben. Es ersetzt keine Protokollimplementation und oeffnet keine Netzwerkverbindung.

## Adaptermodell

Ein `ObjectAdapter` beschreibt eine Protokollverknuepfung eines Objekts.

Geplante Adaptertypen:

- `mqtt`
- `loxone`
- `udp`
- `knx`
- `influx`

Ein Adapter enthaelt:

- `protocol`: Adaptertyp.
- `direction`: Richtung, zum Beispiel `in`, `out` oder `both`.
- `address`: Hauptadresse, zum Beispiel MQTT Topic, KNX Gruppenadresse, UDP Topic oder Loxone IO.
- `json_key`: optionaler JSON-Key.
- `value_type`: fachlicher Werttyp, zum Beispiel `auto`, `number`, `bool`, `text`.
- `enabled`: Adapter-Aktivierung.
- `meta`: zusaetzliche protokollspezifische Daten.

Adapter duerfen spaeter Mapping-Vorschlaege erzeugen. In dieser Version werden sie nur als Datenmodell vorbereitet.

## Flags

`ObjectFlags` sammelt kuenftige Steuermerkmale:

- `auto_create_mappings`: Mappings aus Objektadaptern vorschlagen oder erzeugen.
- `sync_from_mappings`: bestehende Mappings in Objekte zurueckspiegeln.
- `influx_enabled`: Objekt fuer Influx vormerken.
- `test_mode`: Objekt fuer Test-/Demo-Daten markieren.

Flags sind nicht als Runtime-Flags gedacht. Sie beschreiben Planungs- und Verwaltungsverhalten im Objektmanager.

## Migrationsstrategie

Phase 1: Modell einfuehren

- `app/services/object_model.py` enthaelt Dataclasses und Validierungshelfer.
- Keine aktive App-Logik nutzt das Modell.
- Bestehende Objekt- und Mapping-Dateien bleiben unveraendert.

Phase 2: Read-only Analyse

- Bestehende Mappings werden gelesen und als Objektkandidaten angezeigt.
- Keine automatische Speicherung ohne ausdrueckliche Benutzeraktion.
- Konflikte werden nur gemeldet.

Phase 3: Objektzentrierte Bearbeitung

- Objektmanager bearbeitet Objektdefinitionen.
- Adapter koennen Mapping-Vorschlaege erzeugen.
- Bestehende Mapping-Dateien bleiben die Runtime-Quelle.

Phase 4: Kontrollierte Synchronisierung

- Objekte koennen Mappings gezielt erzeugen oder aktualisieren.
- Jede Richtung bekommt einen Dry-Run und eine Rueckmeldung.
- Konflikte verhindern automatische Schreiboperationen.

Phase 5: Runtime-Umstellung

- Erst nach stabilen Smoke-Tests kann die Runtime Objektdefinitionen direkt lesen.
- Alte Mapping-Dateien bleiben als Export- oder Kompatibilitaetsschicht verfuegbar.

## Risiken

- Unterschiedliche Protokolle haben unterschiedliche Adress- und Wertmodelle.
- Automatische Migration kann Dubletten oder falsche Verknuepfungen erzeugen.
- KNX und SSE sind laufzeitkritisch und duerfen nicht nebenbei umgebaut werden.
- Bestehende Nutzerkonfigurationen muessen jederzeit rueckwaertskompatibel bleiben.
- Objektzentrierung darf die schnelle manuelle Mapping-Bearbeitung nicht verschlechtern.

## Exit-Kriterien

Eine spaetere aktive Objektmanager-2.0-Phase ist erst bereit, wenn:

- bestehende Mappings unveraendert geladen und gespeichert werden koennen,
- Objektkandidaten reproduzierbar aus Mappings erzeugt werden,
- Konflikte sichtbar und nachvollziehbar sind,
- jede Schreiboperation einen Dry-Run oder eine klare Vorschau hat,
- `python -m compileall app` sauber laeuft,
- Dashboard, MQTT, UDP, Loxone, KNX, Influx, Backup, Restore, Objektmanager, Live Log, SSE, Bridge und interner Broker unveraendert funktionieren.
