# MP-Gateway 34.0.2

## Influx Explorer

- zeigt ausschließlich Serien mit real vorhandenen Datenpunkten im ausgewählten Zeitraum
- verwendet keine möglicherweise veralteten Measurement-/Tagwerte aus dem Influx-Schemaindex
- gelöschte Topics verschwinden nach dem Aktualisieren vollständig
- Measurements ohne `topic`-Tag bleiben separat sichtbar

## Docker

- Host-Netzwerk bleibt aktiv
- persistentes Volume `mpgateway_data`
- GitHub-sauberes Paket ohne lokale Konfigurationen und Laufzeitdaten
