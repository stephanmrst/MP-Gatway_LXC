# TODO 35.0.2

- MQTT A → B/C mit gleichen und unterschiedlichen Topics im Feldtest prüfen.
- Echo-Schutz bei retained Nachrichten und Broker-Reconnect weiter beobachten.

# MP-Gateway 34.6.7

- OpenCCU-Objekte als eigene Quelle im Objektmanager
- OpenCCU Explorer nur noch mit „Objekt erstellen“
- Kompaktere Objektnamen und Schriftgrößen

## 34.6.5 Nachtest

- [ ] XML-API-Geräteanzahl und Kanalnamen gegen OpenCCU prüfen.
- [ ] Suche, unabhängiges Scrollen der Geräteliste und feststehende rechte Seite testen.
- [ ] Online-/Offline-Anzeige mit `ONLINE` beziehungsweise `UNREACH` sowie normalen Livewerten prüfen.
- [ ] Objekt erstellen und Objekt verknüpfen für mehrere Datenpunkttypen testen.

## 34.3.2

- [x] Linke Objektliste auf reine Objektnamen reduzieren.

## Ab 34.3.1
- Dreispalten-Layout mit großen Objektbeständen testen.
- Responsive Breiten und Scrollverhalten auf kleinen Displays prüfen.
- Optional: Duplizieren-Funktion im Objekt-Explorer ergänzen.


## 33.4.67 Nachtest
- KNX 0/0/9 mehrfach schalten und identische Reihenfolge in MQTT und UDP prüfen.
- Neues Objekt anlegen: UDP-Ziel muss zunächst deaktiviert sein.
- UDP-Ziel speichern und ohne Neustart testen.
## 33.4.58

- Optionales, schaltbares KNX-Diagnose-Logging statt dauerhaftem Hot-Path-Logging vorsehen.

## 33.4.55

- Navigation pruefen: MQTT Hub ist entfernt und `/mqtt` oeffnet den MQTT Explorer.
- KNX Testcenter unter `/knx` inklusive Senden, Wiederholen, Monitor-Eintrag und Diagnose pruefen.
- Direkte Aufrufe aller alten Mapping-Explorer pruefen: Weiterleitung auf `/objects_v33`.
- Spaeter separat entscheiden, wann Legacy-Mappingdateien nach vollstaendiger Objektmigration auch aus Runtime und Code entfernt werden koennen.

# TODO

## 33.0.x

- KNX 33.4.52 im laufenden System pruefen: `0/2/0` bis `0/2/5` zeigen Temperatur/Feuchte inklusive Einheit und DPT-1 bleibt `0`/`1`.
- KNX History 33.4.52 pruefen: 15 Eintraege bleiben nach zwei Minuten Inaktivitaet, SSE-Reconnect und Browser-Reload erhalten.
- KNX 33.4.51 manuell pruefen: DPT `1.001` bleibt `0`/`1`; konfigurierte DPT `9.001` und `9.007` liefern wieder die bekannten Temperatur-/Feuchtewerte.
- KNX Explorer 33.4.51 manuell pruefen: linke Gruppenadressliste verhaelt sich wie im Stand 33.4.47 und verliert bei History-Snapshots keine Eintraege.
- KNX History 33.4.51 manuell pruefen: 15 Telegramme bleiben nach zwei Minuten ohne neue Telegramme sichtbar; leere API-/SSE-Snapshots werden ignoriert.
- KNX History 33.4.51 manuell pruefen: nur der Button `Verlauf leeren` uebernimmt einen explizit markierten leeren Snapshot.
- Die Pruefpunkte fuer die zurueckgezogenen Decoder-/DPT-/Gruppenadress-Erweiterungen 33.4.48 bis 33.4.50 sind historisch und gelten nicht mehr als Ziel fuer 33.4.51.
- KNX Explorer 33.4.50 pruefen: `0/2/0` bis `0/2/5` erhalten ihren DPT aus `config/knx_group_addresses.json`, ausser ein Objekt oder eine Route liefert priorisiert einen DPT.
- KNX Explorer 33.4.50 pruefen: DPT-Aenderung im Detailbereich speichert per `/api/knx/group-address/dpt` und aktualisiert den sichtbaren Wert ohne Neustart.
- KNX Explorer 33.4.50 pruefen: fehlender 2-Byte-DPT erscheint als `9.xxx auto` ohne Einheit, konkreter `9.001`/`9.007` mit `°C`/`%`.
- KNX Decoder 33.4.50 pruefen: DPT-Hauptgruppen 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18 und 20 bleiben decodierbar.
- KNX History 33.4.50 pruefen: `backendCount === 0` taucht im Explorer-Code nicht mehr als Loeschfreigabe auf.
- KNX Explorer 33.4.49 pruefen: ein leerer Snapshot nach vorhandenen Verlaufseintraegen darf die sichtbare History nicht leeren.
- KNX Explorer 33.4.49 pruefen: Browser-Konsole zeigt bei ignoriertem leerem Snapshot `keep_previous_empty_snapshot` mit `backend_count`.
- KNX Explorer 33.4.48 pruefen: `0/2/2`, DPT `9.001`, APDU `19 2F` erscheint als `24.24 °C`, nicht als `Raw: 192F`.
- KNX Explorer 33.4.48 pruefen: `0/2/3`, DPT `9.007`, APDU `1B 1F` erscheint als `63.92 %`, nicht als Raw.
- KNX Explorer 33.4.48 pruefen: `0/2/5`, DPT `9.007`, APDU `1B 0F` erscheint als `62.64 %`, nicht als Raw.
- KNX Explorer 33.4.48 pruefen: DPT `1.001` mit APDU `00`/`01` bleibt parallel als `0`/`1` sichtbar.
- KNX Explorer 33.4.48 pruefen: 15 Verlaufseintraege bleiben nach 2 Minuten ohne Telegramme sichtbar und `history_object_id` bleibt zwischen API-Aufrufen gleich.
- KNX Explorer 33.4.47 pruefen: Telegrammempfang und `/knx_monitor_data` loggen dieselbe `history_object_id`.
- KNX Explorer 33.4.47 pruefen: History wird nur bei `snapshot=true` und vorhandenem `history` ersetzt.
- KNX Explorer 33.4.47 pruefen: parallele/stale Polling-Antworten ueberschreiben keinen neueren Verlauf.
- KNX Explorer 33.4.47 pruefen: es erscheinen keine `KNX HISTORY CHANGE action=clear` Logs ohne expliziten Benutzerbefehl.
- KNX Explorer 33.4.46 pruefen: ein einzelner Verlaufseintrag bleibt nach 30 Sekunden ohne neue Telegramme sichtbar.
- KNX Explorer 33.4.46 pruefen: 15 Verlaufseintraege bleiben nach 2 Minuten ohne neue Telegramme sichtbar.
- KNX Explorer 33.4.46 pruefen: SSE-/Polling-Teilpayloads ohne `log` leeren die sichtbare History nicht.
- KNX Explorer 33.4.46 pruefen: KNX-Statuswechsel auf idle/disconnected veraendert nur den Status, nicht den Verlauf.
- KNX Explorer 33.4.45 pruefen: DPT `1.001` mit APDU `01` erscheint im Explorer als `1`, nicht als `true`, `True` oder `EIN`.
- KNX Explorer 33.4.45 pruefen: DPT `1.001` mit APDU `00` erscheint im Explorer als `0`, nicht als `false`, `False` oder `AUS`.
- KNX->MQTT 33.4.45 pruefen: DPT-1-Werte werden als Payload `1`/`0` veroeffentlicht.
- KNX Explorer 33.4.45 pruefen: 20 Telegramme ergeben genau 15 Verlaufseintraege, neuester Eintrag oben.
- KNX Explorer 33.4.45 pruefen: gleiche Gruppenadresse und gleicher Wert erscheinen mehrfach im Verlauf und ueberschreiben sich nicht.
- KNX Explorer 33.4.45 pruefen: Browser-Refresh, Seitenwechsel und KNX-Reconnect leeren den serverseitigen Verlauf nicht.
- KNX Performance 33.4.44 pruefen: `KNX PERF CALLBACK_DONE` fuer Schalttelegramme bleibt im niedrigen Millisekundenbereich.
- KNX Performance 33.4.44 pruefen: `ROUTING WORKER queue_wait_ms` bleibt nahe 0 ms und waechst bei 20 schnellen Telegrammen nicht dauerhaft.
- KNX Performance 33.4.44 pruefen: `KNX TO MQTT ... delay_ms` liegt im Zielbereich, wenn der MQTT-Client verbunden ist.
- KNX Performance 33.4.44 pruefen: Objekt-DPT `unbekannt` auf `0/0/9` zeigt trotzdem `1/0` per `payload_inferred`.
- KNX Explorer 33.4.43 pruefen: `0/0/9` mit xknx-`DPTBinary(1)` erscheint als `1`, auch wenn kein Objekt-DPT gefunden wird.
- KNX Explorer 33.4.43 pruefen: `0/0/9` mit xknx-`DPTBinary(0)` erscheint als `0`, auch wenn kein Objekt-DPT gefunden wird.
- KNX Explorer 33.4.43 pruefen: API-Eintrag fuer `0/0/9` enthaelt `value=1/0`, `display_value`, `raw_value`, `decoded` und `dpt_source`.
- KNX Explorer 33.4.43 pruefen: unbekannte Nicht-Binary-Payloads ohne DPT bleiben `Raw: <HEX>`.
- KNX Explorer 33.4.42 pruefen: ETS Write `0/0/1`, DPT `1.001`, APDU `01` erscheint in der Liste als `1`.
- KNX Explorer 33.4.42 pruefen: ETS Write `0/0/1`, DPT `1.001`, APDU `00` erscheint in der Liste als `0` und nicht als Raw.
- KNX Explorer 33.4.42 pruefen: zweimal derselbe DPT-1-Wert aktualisiert Zeitstempel und erhoeht `receive_count`.
- KNX Explorer 33.4.42 pruefen: GroupValueRead erscheint als `Leseanfrage`, ohne erfundenen Wert zu routen.
- KNX Explorer 33.4.42 pruefen: DPT `9.xxx` und `14.xxx` bleiben numerisch decodierbar.
- KNX Explorer 33.4.41 pruefen: alle empfangenen `GroupValueWrite`-Telegramme erscheinen mit Zeit, Typ, GA, DPT, Wert und APDU.
- KNX Explorer 33.4.41 pruefen: DPT `1.001` zeigt `1` fuer `01` und `0` fuer `00`; `0`/`False` darf nicht verschwinden.
- KNX Explorer 33.4.41 pruefen: unbekannter oder nicht decodierbarer DPT erscheint als `Raw: <APDU>` mit Status `Raw`.
- KNX Listener 33.4.40 pruefen: RX-Registrierung erfolgt wieder via `register_telegram_received_cb`.
- KNX Explorer 33.4.40 pruefen: empfangene Bus-Telegramme erscheinen nach dem Listener-Start wieder als `Empfangen`.
- KNX Explorer 33.4.40 pruefen: Objekt-Button-Fix aus 33.4.39 bleibt funktionsfaehig.
- KNX Explorer 33.4.39 pruefen: Button `Objekt erstellen / verknuepfen` funktioniert im eingebetteten Explorer und oeffnet den Objektmanager.
- KNX Explorer 33.4.39 pruefen: Shell-PostMessage nutzt `mqtt2lox:navigateFrame` mit `activeHref=/objects_v33`.
- KNX Explorer 33.4.39 pruefen: KNX-Prefill bleibt mit Gruppenadresse, DPT, Quelle KNX und letztem Wert erhalten.
- KNX Explorer 33.4.38 pruefen: echte KNX-Bus-RX-Telegramme erscheinen links und im Verlauf wieder als `Empfangen`.
- KNX Explorer 33.4.38 pruefen: `OUT/ERROR` fuer dieselbe Gruppenadresse bleibt im Verlauf, ueberschreibt aber keinen vorhandenen RX-Liveeintrag links.
- KNX Listener 33.4.38 pruefen: Log zeigt `KNX Listener RX Callback registriert via XKNX telegram_received_cb`.
- KNX Explorer 33.4.37 pruefen: Objektmanager-Route nach KNX erscheint sofort als `Senden` in der linken Gruppenadressenliste.
- KNX Explorer 33.4.37 pruefen: bei fehlender Tunnelverbindung zeigt die Ziel-GA den Status `ERROR` statt dass der Explorer leer bleibt.
- KNX Explorer 33.4.37 pruefen: `/knx_monitor_data` enthaelt fuer fehlgeschlagene Objekt-Sends einen `last`-Eintrag mit GA, Wert, DPT, Richtung `OUT` und Status `ERROR`.
- KNX TX 33.4.36 pruefen: bei Tunnel-Fehler erscheint vor dem Sendefehler `KNX TX prepared` mit GA, DPT, Rohwert, normalisiertem Wert, Payload-Laenge und Payload-Hex.
- KNX TX 33.4.36 pruefen: bei `0/3/1`, DPT `9.001`, Wert `69.28` muss die vorbereitete Payload-Laenge `2` sein, auch wenn der Tunnel nicht aktiv ist.
- KNX Runtime 33.4.36 pruefen: nach `Tunnel connection could not be established` enthaelt der Sendefehler Status, Gateway, lokale IP und `last_error`.
- KNX Explorer 33.4.35 pruefen: Objekt-Button oeffnet den zentralen Objektmanager-Import mit Quelle KNX, Gruppenadresse und DPT.
- KNX Explorer 33.4.35 pruefen: gespeichertes Objekt enthaelt `knx.group_address` und `knx.dpt`, aber kein neues Legacy-KNX-Mapping.
- KNX Explorer 33.4.35 pruefen: weitere Routen werden ausschliesslich im Objektmanager konfiguriert.
- KNX TX 33.4.34 pruefen: DPT-9-Testsendung `69.28` loggt `payload_len=2` und `payload_hex=16c4`.
- KNX TX 33.4.34 pruefen: APDU-Hex darf laenger sein, aber die reine DPT-Payload muss bei `9.001` exakt 2 Bytes haben.
- KNX TX 33.4.34 pruefen: Objekt-/MQTT-/UDP-KNX-Einstieg loggt den DPT vor dem Senden.
- KNX TX 33.4.33 pruefen: `69.28` auf GA `0/3/1` mit DPT `9.001` erscheint in ETS/Loxone als interpretierbarer 2-Byte-Float.
- KNX TX 33.4.33 pruefen: Log enthaelt `KNX TX ga=... dpt=... raw=... normalized=... method=group_value_write encoder=...`.
- KNX TX 33.4.33 pruefen: Ziel ohne DPT sendet nicht und loggt `KNX send skipped: missing DPT for GA ...`.
- Explorer UI 33.4.32 pruefen: MQTT Explorer zeigt kein Expertenmapping-Accordion und kein Expertenmapping-Dropdown bei JSON-Keys mehr.
- Explorer UI 33.4.32 pruefen: Loxone, UDP und KNX Explorer zeigen keine Expertenmapping-/Experteneinstellungs-Accordions mehr.
- Explorer UI 33.4.32 pruefen: Backend-Routen fuer alte Mapping-Seiten bleiben direkt erreichbar und werden nicht geloescht.
- KNX Explorer 33.4.31 pruefen: keine grossen Dashboard-Karten oder separate Statusbadge-Leiste mehr sichtbar.
- KNX Explorer 33.4.31 pruefen: Verlauf steht nur rechts im Detailbereich und die Aktionsspalte ist aus der Verlaufstabelle entfernt.
- KNX Explorer 33.4.31 pruefen: Objekt erstellen/verknuepfen, GA kopieren und Verlauf funktionieren am ausgewaehlten Eintrag.
- KNX Explorer 33.4.30 pruefen: Sidebar, KNX-Hub, Seitentitel und Seitenkopf duerfen nicht mehr `KNX Monitor` als UI-Label zeigen.
- KNX Explorer 33.4.30 pruefen: Suche, Richtungsfilter, Pause, Verlauf leeren, Gruppenadressenliste, Detailwert und Telegrammverlauf muessen weiter funktionieren.
- KNX Explorer 33.4.30 pruefen: `/knx_monitor`, `/knx_monitor_data`, SSE, Influx-Schalter, Influx-Typ, Influx-Topic und Objektanlage bleiben unveraendert erreichbar.
- Objektmanager-Filter 33.4.29 pruefen: MQTT-Quelle mit UDP-Ziel darf nur im MQTT-Filter erscheinen.
- Objektmanager-Filter 33.4.29 pruefen: UDP-Quelle mit MQTT-Ziel darf nur im UDP-Filter erscheinen.
- Objektmanager-Filter 33.4.29 pruefen: Aktivstatus und Influx-Ziele duerfen die Filterauswahl nicht beeinflussen.
- Sidebar 33.4.28 pruefen: Es darf nur noch `UDP Explorer` sichtbar sein; `UDP Hub` und `UDP Monitor` duerfen nicht mehr in der Navigation erscheinen.
- UDP Explorer 33.4.28 pruefen: Monitor, Einstellungen und Mapping-Links bleiben aus dem UDP Explorer erreichbar.
- Live-API Debug 33.4.27 pruefen: `LIVE TAB DEBUG` muss Memory-State und API-Return fuer das ausgewaehlte Objekt zeigen.
- UDP Live Debug 33.4.27 pruefen: `UDP LIVE UPDATE DEBUG` muss before/after Memory-State mit dem extrahierten UDP-Wert zeigen.
- Live-API Store 33.4.27 pruefen: UDP-Update und `/api/objects/live` muessen denselben Objekt-Service-Store verwenden.
- Object-Live-State 33.4.26 pruefen: MQTT, Loxone, KNX und UDP muessen denselben zentralen Updater nutzen und `status=aktiv` liefern.
- UDP Live-Tab 33.4.26 pruefen: nach UDP-Empfang muessen Wert, Zeitstempel, Endpoint und Status `aktiv` ohne Seitenreload erscheinen.
- UDP Live-State 33.4.25 pruefen: `Victron/Netz/Leistung:-30` muss in der Objektkarte als Wert `-30` erscheinen und UDP->MQTT weiter routen.
- UDP JSON Live-State 33.4.25 pruefen: `params/pm1:0/apower` muss den Leaf-Wert `4` in der Objektkarte anzeigen.
- UDP Match 33.4.25 pruefen: JSON-Pakete duerfen keine anderen UDP-Objekte auf demselben Listen-Port mit dem Platzhalter `JSON` ueberschreiben.
- Objektkarten Quelle 33.4.24 pruefen: `display_source` muss nach Reload immer Routing-Quelle zeigen und niemals Live-Echo.
- API 33.4.24 pruefen: `display_source` muessen Karten, Detailansicht und Live-Polling erhalten.
- UDP->MQTT 33.4.23 pruefen: Target-MQTT darf die Eingangsquelle nicht mehr ueberschreiben, auch nicht bei internen Ruecklaeufen.
- MQTT-Echo-Schutz 33.4.23 pruefen: topic-basierte Objekt-Routings sollen interne Publishes sicher ignorieren.
- Objektkarten Quelle 33.4.22 pruefen: Browser-Reload darf nicht mehr auf MQTT-Zielinfos oder Badges zurueckfallen.
- Objekt-API 33.4.22 pruefen: `route_source` und `input_protocol` muessen fuer Karten und Routing sichtbar bleiben.
- Objektkarten Quelle 33.4.21 pruefen: wenn kein Livecache vorhanden ist, muss die Anzeige aus der konfigurierten Eingangsseite kommen und nicht aus MQTT-Zielen.
- Objektliste 33.4.21 pruefen: Scrollposition und Auswahl sollen beim Refresh erhalten bleiben.
- UDP Live-Cache 33.4.20 pruefen: UDP muss live_value, last_value und source_protocol direkt setzen, bevor MQTT-Weiterleitung laeuft.
- Objektkarte Quelle 33.4.19 pruefen: bei Loxone/UDP/KNX/MQTT muss immer die letzte Livequelle angezeigt werden, nicht ein Route-Badge.
- UDP Topic:Wert 33.4.18 pruefen: `Victron/Netz/Leistung:-30` darf niemals durch einen JSON-Path laufen oder `JSON path not found` ausloesen.
- UDP Livequelle 33.4.17 pruefen: Objektkarte und Live-Tab muessen die echte Eingangsquelle aus dem Live-Cache anzeigen, nicht die letzte Route.
- UDP Topic:Wert 33.4.17 pruefen: Ein Payload wie `Victron/Netz/Leistung:-17` muss als UDP-Wert erkannt, im Objekt aktualisiert und an MQTT weitergereicht werden.

- UDP JSON Debug 33.4.16 pruefen: der volle JSON-Pfad muss live auf den Leaf-Wert aufgeloest werden, damit MQTT nicht `JSON` sendet.

- UDP JSON Debug 33.4.15 pruefen: `[object Object]` muss im Monitor wieder zu JSON-Text normalisiert werden, wenn JSON-Daten vorhanden sind.

- UDP JSON Debug 33.4.14 pruefen: Rohpayload soll im Explorer und beim Kopieren konsistent als Text auftauchen, nicht als `[object Object]`.

- UDP JSON Debug 33.4.13 pruefen: JSON soll auch dann im Explorer auftauchen, wenn `payload_raw` im Monitor bereits als Objekt ankommt.

- UDP JSON Debug 33.4.12 pruefen: `payload_raw` darf im Explorer nicht mehr als `[object Object]` landen, wenn der Monitor ein JSON-Objekt normalisiert.

- UDP JSON Debug 33.4.11 pruefen: Listener muss Rohbytes, Text-Repr und geparste Details loggen, damit der Explorer nicht mehr mit einem unsichtbar geaenderten Payload verwechselt wird.

- UDP Explorer 33.4.10 pruefen: JSON ohne Topic muss als stabiler Monitor-Eintrag mit Leaf-Werten erscheinen und die Tabelle rechts darf nicht leer bleiben.
- UDP Explorer 33.4.6 pruefen: JSON-Payloads muessen auch bei eingebetteten oder anders formatierten Rohdaten wie im MQTT Explorer rechts als Keys erscheinen.
- UDP Explorer 33.4.5 pruefen: Der Baum muss links stabil bleiben, JSON-Keys muessen rechts sichtbar sein und der Expertenbereich darf standardmaessig eingeklappt bleiben.
- UDP Explorer 33.4.4 pruefen: Die linke Baumansicht soll MQTT-Discover aehnlich wirken, Auswahl darf beim Update nicht springen und Experteninfos muessen eingeklappt bleiben.
- UDP Explorer 33.4.3 pruefen: Die linke Liste muss kompakt bleiben, die rechte Detailkarte soll JSON-, Topic- und Wertdaten getrennt anzeigen und die Einstellungen duerfen den Explorer nicht dominieren.
- UDP Explorer 33.4.2 pruefen: Live-Quellen muessen als stabiler Eintrag aktualisiert werden, Auswahl und Scroll-Verhalten duerfen bei Folgepaketen nicht springen.
- UDP Explorer 33.4.1 pruefen: Seitenleiste muss UDP Hub mit Explorer und Monitor zeigen, Start/Stop muss denselben Shared Listener nutzen und JSON/Topic/Wert-Matches sollen Objektanlage ausloesen.

- UDP-Basis 33.4.0 pruefen: "+ Neu" darf kein Leerformular-Fehler mehr sein, Quellenwahl muss LOXONE/MQTT/UDP/KNX anbieten und der UDP-Monitor muss RX-Eintraege liefern.
- UDP-Quelle 33.4.0 pruefen: UDP Input muss Topic/Wert oder JSON sauber zerlegen und denselben Object-Router wie MQTT und Loxone nutzen.
- MQTT externe Broker 33.3.89 pruefen: Queue-voll-Meldungen muessen gedrosselt werden und der Gateway-Stop muss MQTT/UDP/KNX wirklich beenden.
- MQTT externe Broker 33.3.88 pruefen: Pro Broker muss ein eigener Client mit Queue-Worker, Auto-Reconnect, Healthcheck und Statusanzeige laufen.
- Loxone-Zielroute 33.3.87 pruefen: Der Routing-Tab und die linke Infokachel muessen Loxone-Ziele wieder als aktiv anzeigen, wenn Zielhaken, Ziel-UUID und Gateway-Konfiguration vorhanden sind.
- Loxone-Zielroute 33.3.86 pruefen: Die linke Infokachel und der Routing-Tab muessen Loxone-Ziele nur dann als aktiv markieren, wenn Zielhaken, Ziel-UUID und Verbindung vorhanden sind.
- Object-Routing 33.3.82 pruefen: UDP-Ausgabe muss den bestehenden Sender wieder mit korrekter Signatur erreichen.
- Object-Routing 33.3.81 pruefen: Legacy-Fallbacks duerfen erst blockiert werden, wenn ein Objektziel wirklich erfolgreich gesendet hat.
- Object-Routing 33.3.80 pruefen: LOXONE/MQTT/UDP/KNX sollen dieselbe Objekt-Routenschleife nutzen und die Quelle darf nicht in den Zieladapter kippen.
- KNX 33.3.79 pruefen: ausgehende KNX-Telegramme duerfen die Live-Quelle nicht mehr auf KNX ziehen.
- UDP 33.3.78 pruefen: ein geloeschtes UDP Topic soll beim Speichern wieder `<Objektname>/value` bekommen.
- UDP 33.3.77 pruefen: neue UDP-Adapter muessen beim ersten Speichern wieder `<Objektname>/value` vorbelegt bekommen, vorhandene Adapter duerfen ihr geloeschtes Topic aber behalten.
- UDP 33.3.76 pruefen: Deaktivieren im Objektmanager muss persistieren und ein geloeschtes UDP Topic darf beim Speichern nicht mehr wieder eingesetzt werden.
- MQTT->UDP 33.3.75 pruefen: normale MQTT-Topics muessen den frischen Payload senden, JSON-Key-Objekte den extrahierten Live-Wert.
- MQTT->UDP 33.3.74 pruefen: der Wrapper muss ohne doppelt gesetztes `object_id` durchlaufen.
- MQTT->UDP 33.3.73 pruefen: der Router darf nicht mehr vor dem Sender an einem Helper-Fehler im object_service abbrechen.
- Objekt-UDP 33.3.72 pruefen: gespeicherte UDP-Zielwerte muessen den Adapter beim Save automatisch aktivieren.
- Objektstatus 33.3.71 pruefen: ein Objekt soll erst dann aktiv werden, wenn mindestens ein echtes Quelle-Ziel-Paar vorhanden ist.
- MQTT->UDP 33.3.70 pruefen: der Routenloader muss mit lokaler UDP-Pruefung arbeiten und den Grund fuer verworfene Routen sichtbar machen.
- MQTT->UDP 33.3.69 pruefen: der Router muss den Eintritt, die verfuegbaren Routen und den konkreten Abbruchgrund loggen, wenn der UDP-Sender nicht erreicht wird.
- MQTT->UDP 33.3.68 pruefen: MQTT-Quellen mit `in`/`both` muessen den Objektmanager-UDP-Dispatch ausloesen und die Herkunft darf in der Objektkachel nicht mehr auf alte Monitorwerte kippen.
- MQTT->UDP 33.3.67 pruefen: direkte Sendung ueber den bestehenden UDP-Ausgang muss mit JSON-Key-Werten ankommen.
- MQTT->UDP 33.3.66 pruefen: MQTT-JSON-Key-Werte muessen denselben UDP-Ausgang wie Loxone->UDP verwenden.
- MQTT->UDP 33.3.65 pruefen: MQTT-Eingang, objektbasierter UDP-Dispatch und UDP-Start/OK-Logs muessen bei JSON-Key-Objekten sichtbar sein.
- MQTT JSON-Key "+ Objekt" 33.3.64 pruefen: Split-Key-Buttons muessen Topic, JSON-Key, Typ und Name an den Objektmanager uebergeben und den Live-Match auf `topic / json_key` aufloesen.
- KNX-Testcenter 33.3.63 pruefen: Zeitstempel-Fallback, JSON-Fehlerantwort und getrennte Buttons fuer Senden/Wiederholen/Monitor leeren muessen stabil bleiben.
- KNX-Testcenter 33.3.62 pruefen: Backend liefert bei Fehlern JSON statt HTML-500 und `Auto` wird vor dem Senden auf einen konkreten DPT aufgeloest.
- KNX-Testcenter 33.3.61 pruefen: Submit laeuft per JSON-Fetch, Fehler erscheinen in der Diagnose und das Testcenter steht unter den Uebersichtskacheln.
- KNX-Testcenter 33.3.60 pruefen: Senden, Wiederholen, Monitor leeren und Diagnose-Kopie muessen stabil funktionieren.
- KNX-Monitor 33.3.59 pruefen: RX/OUT-Filter, Richtungssymbole und Statusfarben muessen klar getrennt bleiben.
- KNX Write 33.3.58 pruefen: GroupValueWrite muss mit APDU-Payload im Busmonitor sichtbar sein und Loxone soll Write/Len/Val anzeigen.
- KNX-Sendepfad 33.3.57 pruefen: `OUT_PENDING`/`OUT_OK`/`OUT_ERROR` muessen nach echtem Write sichtbar sein, inklusive Exception-Logging.
- KNX-Import 33.3.56 pruefen: Sender und Listener muessen denselben `app.core`-Runtime-State sehen.
- KNX-Ausgang 33.3.55 pruefen: Senden nutzt die laufende KNX Runtime-Verbindung und erzeugt keinen neuen Tunnel pro Wert.
- KNX Monitor 33.3.55 pruefen: selbst gesendete Objektmanager-Telegramme erscheinen als `OUT` mit Quelle `Objektmanager`.
- KNX-Ausgang 33.3.54 pruefen: aktive Routen mit Gruppenadresse und DPT senden echte Telegramme und erscheinen im KNX Monitor als `WRITE`.
- KNX-Tab 33.3.54 pruefen: DPT-Auswahl wird gespeichert, geladen und bei fehlender Gruppenadresse/DPT blockiert.
- Objekt-Routing 33.3.53 pruefen: KNX im Objektmanager als Ziel speichern, im Routing-Tab anzeigen und im Runtime-Dispatch aus Loxone/MQTT/UDP senden.
- Objekt-Routing 33.3.53 pruefen: KNX-Routen werden bei Deaktivieren und Loeschen des Objekts sauber deaktiviert bzw. entfernt.
- Objekt-UI 33.3.53 pruefen: KNX-Ausgang im Objektmanager erscheint in Routing-Vorschau und Runtime-Dispatch.
- Objekt-UI 33.3.52 pruefen: Detailkopf und Objektkarte links zeigen pro Objekt nur noch ein einziges Status-Badge.
- Objekt-Routing 33.3.51 pruefen: Routing-Tab zeigt getrennte Haupt-Routen und direkte Rueck-Routen zur aktuellen Quelle.
- Objekt-Routing 33.3.51 pruefen: Rueck-Routen zeigen nur direkt konfigurierte und technisch moegliche Rueckwege, keine Legacy- oder Echo-Pfade.
- Objekt-Routing 33.3.50 pruefen: Routing-Tab zeigt nur objektbasierte Routen mit aktiven Quellen und Zielen, ohne Selbst- oder Legacy-Routen.
- Objekt-Routing 33.3.50 pruefen: Influx-Ziele im Routing-Tab zeigen `Measurement / Field / Topic` als Zieladresse.
- Objekt-Live 33.3.49 pruefen: Loxone-Wert mit MQTT/UDP/Influx-Zielrouting muss in Objektkarte, Live-Tab und API weiter `Quelle: Loxone` anzeigen.
- Objekt-Live 33.3.49 pruefen: Eigene MQTT-Publishes aus Objektmanager-Routing duerfen keinen Live-Cache-Source-Wechsel auf MQTT ausloesen.
- Objekt-Routing 33.3.48 pruefen: Influx-Tab Measurement, Field und Topic frei setzen, speichern, neu laden und als `_measurement`, `_field` und Tag `topic` in Influx wiederfinden.
- Objekt-Routing 33.3.48 pruefen: Leere Influx-Felder werden wieder auf Defaults gesetzt: Measurement aus Objektname, Field `value`, Topic `<object.name>/value`.
- Objekt-Routing 33.3.47 pruefen: Loxone+Influx-Objekt mit aktivem Influx-Ziel schreibt Livewerte direkt nach Influx, ohne `topic_config` oder Legacy-Mapping zu erzeugen.
- Objekt-Routing 33.3.47 pruefen: Influx-Zieladapter defaults `measurement=<Objektname>`, `field=value`, optionaler Bucket und Tags `object_id,source,unit`.
- Objekt-Routing 33.3.46 pruefen: Neues Objekt anlegen, UDP-Tab oeffnen und sicherstellen, dass `UDP Topic` als `<Objektname>/value` vorbelegt ist; nach manuellem Leeren und Speichern muss wieder dieser Default erscheinen.
- Objekt-Routing 33.3.46 pruefen: Payload-Modus `Nur Wert` sendet trotz gespeichertem UDP Topic nur den nackten Wert.
- Objekt-Routing 33.3.44 pruefen: UDP-Zieladapter speichern `udp_topic`/`payload_mode`, senden mit Custom-Topic als `topic:value` und ohne Topic nur den Wert.
- Objekt-Routing 33.3.43 pruefen: Legacy-Seiten duerfen keine Objektmanager-Routen mehr zaehlen/anzeigen und eigene MQTT-Ausgaben muessen als Echo uebersprungen werden.
- Objekt-Routing 33.3.42 pruefen: Loxone->UDP sendet pro Zielpaket nur einmal, ohne leeres Topic-Praefix und ohne MQTT-Loopback-Duplikat.
- Objekt-Routing 33.3.41 pruefen: Loxone->UDP darf pro Zielroute nur einmal senden und MQTT-Loopbacks muessen unterdrueckt bleiben.
- Objekt-Routing 33.3.40 pruefen: Loxone muss auf aktive MQTT- und UDP-Zieladapter weiterreichen, KNX bleibt vorerst vorbereitet.
- Objekt-Live 33.3.39 pruefen: kein Ein-Objekt-Fallback mehr, nur echte Zuordnung oder Info-Log.
- Objekt-Live 33.3.38 pruefen: `/api/objects/live` soll Loxone-Werte aus `core.display_values` und `core.last_values` spiegeln.
- Objekt-Live 33.3.37 pruefen: Fallback fuer Einzelobjekte soll nur im Loxone-Pfad greifen.
- Objekt-Live 33.3.36 pruefen: Loxone-Treffer ueber UUID, IO-Adresse und Objektname muessen sofort sichtbar werden.
- Objekt-Live-Werte 33.3.35 pruefen: Karten, Live-Tab und `/api/objects/live` zeigen Wert, Einheit, Quelle und erkannte Endpunkte ohne Page-Reload.
- Objekt-CRUD 33.3.34 pruefen: Bridge und CRUD duerfen sich nicht mehr ueber Lock-Inversion blockieren; Live-Wert-Callbacks muessen ueber den vorbereiteten Endpoint-Index laufen.
- Objekt-CRUD 33.3.32 pruefen: Delete bleibt sofort responsiv, Reload laeuft nur noch im Hintergrund und blockiert die Bridge nicht mehr.

- Object Manager V33 Plan pruefen: Leitbild "Ein Objekt. Alle Protokolle.", Objektmodell, Adaptermodell, Migrationsstrategie und Exit-Kriterien.
- Object Adapter Model 33.0.1 pruefen: MQTT, Loxone, UDP, KNX und Influx gegen bestehende Mapping-Felder abgleichen.
- Passive Object Registry 33.0.2 pruefen: fehlende `data/objects_v33.json` liefert leere Liste, Speichern/Lesen funktioniert, keine bestehende Config wird veraendert.
- Passive Object Adapter Engine 33.0.3 pruefen: `validate`, `serialize`, `deserialize` und Registry-Roundtrip fuer alle Adapterklassen.
- Objektmanager V33 33.1.0 pruefen: `/objects_v33`, Suche, neues Objekt, Bearbeiten, Loeschen, keine Adapterbearbeitung und keine Aenderung bestehender Mappings.
- Objektidentitaet V33 33.1.1 pruefen: `uuid` als feste interne ID, `key` als technischer Schluessel, `name` frei aenderbar, Edit/Delete ueber `uuid`.
- Adapterverwaltung V33 33.1.2 pruefen: MQTT, UDP, KNX, Loxone und Influx als Cards/Chips anzeigen, Kurzstatus pruefen, aktivieren/deaktivieren, Platzhalterdialoge bearbeiten.
- Adapter-Komponenten V33 33.2.0 pruefen: eigene Editor-Komponenten fuer MQTT, UDP, KNX, Loxone und Influx, getrennte Objekt-/Adapter-Speicherung und Registry-Roundtrip.
- Branding 33.2.1 pruefen: App-Header und Browser-Titel zeigen `MP-Gateway`; `MQTT2Lox` bleibt technischer Projekt-/Repo-Name.
- Routing-Vorschau V33 33.2.2 pruefen: MQTT+Loxone, KNX+MQTT, MQTT+Influx, Richtungsauswertung und inaktive Adapter ohne echte Mapping-Dateien.
- Sidebar-Link V33 33.2.3 pruefen: `Objektmanager V33` oeffnet `/objects_v33`; alter Objektmanager bleibt auf `/objects`.
- Industrial-Dark-Layout V33 33.2.3 pruefen: linke Objektliste, rechte Detailansicht, Tabs, Adapter speichern, Routing-Vorschau sichtbar.
- Objektmanager-V33-Optik 33.2.4 pruefen: alle Protokolle pro Karte sichtbar, aktive farbig, inaktive grau, Auswahl deutlich.
- MP-Gateway-Designlinie 33.2.5 pruefen: Filterchips ohne Initialen, kraeftige Protokollfarben, `docs/UI_GUIDELINES.md` als Vorgabe fuer neue UI-Arbeit.
- Sidebar-Komponente 33.2.6/33.2.7 pruefen: Dashboard, MQTT Monitor, MQTT Hub, Loxone Monitor, Objektmanager, KNX, KNX Monitor, Suche, Konfig pruefen, InfluxDB, Grafana und Einstellungen nutzen dieselbe Sidebar-Optik.
- Layout-Fundament 33.2.7 pruefen: Sidebar-Gruppen `MP-Gateway` und `Externe Dienste`, beide Objektmanager-Links, `/objects_v33` unveraendert und alter `/objects`-Objektmanager erreichbar.
- Sidebar-Feinschliff 33.2.7a pruefen: keine `MP-Gateway`-Gruppenueberschrift, alter Objektmanager nicht in Sidebar, `Objektmanager V33` sichtbar, externe Dienste nur InfluxDB/Grafana.
- Sidebar-Link-Korrektur 33.2.7c pruefen: `Influx Explorer` -> `/influx_explorer`, `InfluxDB` und `Grafana` -> externe Config-URLs, leere URLs deaktiviert.
- Sidebar-Button-Restore 33.2.7g pruefen: aktive externe Config-Eintraege erscheinen generisch, neue Eintraege automatisch, deaktivierte verschwinden, `new_tab=false` oeffnet im rechten Content-Bereich.
- Objektmanager-Hintergrund 33.2.8 pruefen: Dashboard und `/objects_v33` wirken farblich zusammengehoerig, Sidebar unveraendert, Objektkarten und Protokoll-Badges unveraendert.
- Objektmanager-Arbeitsflaeche 33.2.8a pruefen: Objektliste und Editor wirken wie eine gemeinsame Oberflaeche, Objektkarten heben sich klar vom Hintergrund ab.
- Objektmanager-Core 33.9.0 pruefen: Objekt anlegen, bearbeiten, loeschen, aktivieren/deaktivieren, API-CRUD, Speicherung in `config/objects.json` und MQTT-Topic-Vorbefuellung.
- Vor Runtime-Anbindung definieren, wie `source_type/source_address/target_type` in technische MQTT/KNX/Loxone/UDP/Influx-Mappings uebersetzt werden.
- Objektbasierte Routen 33.3.0 pruefen: Status-Badges, Logging, Reload-Hook, MQTT->Loxone, MQTT->KNX, MQTT->UDP und MQTT->Influx.
- Unvollstaendige Objekte pruefen: kein Ziel oder ungueltiger UDP-Target erzeugt keine Runtime-Route, bleibt aber im Objektmanager sichtbar.
- Objektmanager-Architektur 33.3.1 pruefen: Allgemein-Tab enthaelt nur Stammdaten, Quelle/Ziel kommen nur aus Adapter-Tabs, Status haengt an vollstaendigen aktiven Endpunkten.
- Routing-Tab 33.3.1 pruefen: erzeugte Routen, Status, fehlende Endpunkte und Adapter-Fehler werden korrekt angezeigt.
- Route-Generator 33.3.1 pruefen: MQTT-, KNX- und UDP-basierte Endpunktpaare werden in bestehende Runtime-Mapping-Loader gemerged, ohne Mapping-Dateien zu schreiben.
- Explorer-Create 33.3.2 pruefen: Klick im Loxone Explorer erstellt ein Objekt, oeffnet danach den Loxone-Tab und speichert UUID/IO-Adresse nicht im Allgemein-Tab.
- Loxone-Adapter 33.3.2 pruefen: UUID, IO-Adresse, Control-Typ, Visu-Name, Raum und Einheit werden angezeigt, gespeichert und serialisiert.
- Loxone-Explorer-Fix 33.3.3 pruefen: Explorer-Create und alte `/objects_v33/new`-Vorbelegung setzen den Loxone-Adapter aktiv und oeffnen den Loxone-Tab.
- Statusregel 33.3.3 pruefen: Nur Loxone-Endpunkt ergibt `unvollstaendig`, erst ein zweiter vollstaendiger Endpunkt macht das Objekt aktiv/routingfaehig.
- Loxone-Import 33.3.4 pruefen: Explorer-Create speichert alle Loxone-Felder im `loxone`-Adapter, erzeugt keine UUID als Key und laedt den Loxone-Tab nach Reload wieder vollstaendig.
- Objektmodell-Konsolidierung 33.3.5 pruefen: keine neuen Legacy-Felder in `objects.json`, ein Protokollblock pro Protokoll, Explorer-Create erscheint links und rechts aus derselben Quelle.
- Loxone-Protokollblock 33.3.6 pruefen: Explorer-Create speichert UUID und Metadaten in `object.loxone`, Loxone-Tab laedt daraus und bleibt nach Redirect aktiv.
- Objektmanager-Pipeline 33.3.7 pruefen: Versionsanzeige aus `VERSION`, `/objects_v33/new` ohne Geisterobjekt, Explorer-Import nur ueber `create_from_explorer`, Loxone-Import ohne MQTT-Tab-Befuellung.
- Sidebar-Version 33.3.8 pruefen: Versionsdatei aendern, Server neu starten, Sidebar unten links zeigt den Dateiinhalt.
- Embedded-Explorer 33.3.9 pruefen: Loxone Explorer im Shell-IFrame nutzt `postMessage`, laedt den Objektmanager V33 mit Cache-Buster neu, zeigt den neuen Eintrag links und den Loxone-Tab rechts.
- Loxone-Race-Fix 33.3.10 pruefen: Button deaktiviert nach erstem Klick, gleiche Loxone-UUID ist idempotent, Redirect landet auf `tab=loxone`, Log enthaelt `source`, `uuid`, `name`, `object_id` und `action`.
- Delete-Fix 33.3.11 pruefen: Loeschen mit `id`, alter `uuid`, fehlendem Objekt, leerer `objects.json` und Doppelklick redirectet sauber auf `/objects_v33` und loggt `found/deleted/error`.
- IFrame-Loxone-Create 33.3.12 pruefen: `tm2CreateObjectSelected()` nutzt im IFrame und im separaten Fenster denselben direkten Redirect ohne Parent-Frame-Rewrite.
- Auto-Publish-Gate 33.3.13 pruefen: Loxone-Erfassung bleibt sichtbar, aber MQTT-Publish passiert nur bei aktivem Objekt mit Loxone- und MQTT-Endpunkt.
- Embedded-Debug 33.3.14 pruefen: Standalone- und IFrame-Klick vergleichen; gesucht werden fehlende `uuid`, `name`, `loxone_io`, `topic` oder abweichende Ziel-URL.
- Create-Failure-Logging 33.3.15 pruefen: direkt vor der Meldung muessen `CREATE OBJECT FAILED`, Request-Daten, JSON und `reason` im Log stehen.
- Explorer-State-Fix 33.3.16 pruefen: mehrfache Create-Versuche ohne F5 behalten keine veraltete `tm2Selected`-Referenz und loggen die aktuelle `selectedRow`.
- Loxone-Explorer-JS-Fix 33.3.17 pruefen: gerendertes `tm2CssEscape()` enthaelt kein kaputtes Regex-Literal und der Explorer zeigt wieder Topics.
- Interne Objekt-UUID 33.3.18 pruefen: Create aus UI und Explorer erzeugt stabile `obj_<uuid4hex>`-IDs, Namensaenderung aendert die ID nicht, alte Slug-IDs funktionieren nur noch als Legacy-Referenz.
- Objekt-Live-Wert 33.3.19 pruefen: Live-Tab, Objektkarten und `/api/objects/live` zeigen Wert, Einheit, Zeit, Quelle, Ziele und Status ohne `objects.json`-Persistenz.
- Objektanlage 33.3.20 pruefen: Standalone und IFrame erstellen/verknuepfen Loxone-Objekte mit Mindestdaten `source/explorer=loxone` und `uuid`, optionale Felder duerfen fehlen.
- Objekt-Delete 33.3.21 pruefen: Loeschen mit interner Objekt-UUID entfernt den Eintrag aus `config/objects.json`; Name, Key und Slug duerfen nicht mehr als Delete-ID wirken.
- `app/services/object_model.py` vorerst passiv lassen; keine Runtime-, UI-, Routen- oder Config-Verdrahtung ohne separate Migrationsphase.
- Vor aktiver Objektmanager-2.0-Arbeit Smoke-Tests fuer bestehende Mappings, Objektmanager, Dashboard, MQTT, UDP, Loxone, KNX, Influx, Live Log, SSE, Bridge und internen Broker festlegen.
- Read-only Analyse bestehender Mapping-Dateien als naechsten sicheren V33-Schritt planen.

## 32.0.x

- Architektur-Review 32.3.1 auswerten: zuerst RuntimeContext/Blueprint-Plan festlegen, dann weitere Auslagerungen angehen.
- Blueprint-Plan 32.3.2 pruefen und vor der ersten Route-Migration Smoke-Tests fuer Seiten, JSON-Endpunkte und SSE vorbereiten.
- RuntimeContext-Plan 32.3.3 pruefen und vor State-Verschiebungen Tests fuer Live-Log, Status-SSE, MQTT Monitor, KNX Monitor und Bridge Start/Stop festlegen.
- RuntimeContext-Grundgeruest 32.3.4 vorerst ungenutzt lassen; erst nach Smoke-Tests Instanzierung und schrittweise Verdrahtung planen.
- LiveLog-Spiegelung 32.3.5 pruefen: Dashboard, Live Log, `/events/live_log` und keine doppelten sichtbaren Eintraege.
- Bridge-State 32.3.7 pruefen: Start/Stop, `/events/status`, Dashboard-Status und Live-Log-Meldungen.
- MQTT-Monitor-State 32.3.8 pruefen: MQTT Monitor, MQTT Hub, `/monitor_data`, `/events/mqtt_monitor`, Topic Explorer und Dashboard.
- UDP-State 32.3.9 pruefen: MQTT -> UDP, UDP -> MQTT, UDP -> KNX, UDP Input, Discovery, Dashboard und Live Log.
- BrokerState 32.4.0 pruefen: Broker starten, stoppen, Statusroute, Dashboard, LiveLog, MQTT und Bridge.
- KNX Runtime Migration Plan 32.4.1 pruefen und vor KNX-State-Migration Smoke-Tests fuer Monitor, `[KNX MONITOR ADD]`, `[KNX SSE]`, MQTT->KNX, UDP->KNX, KNX->MQTT und KNX->Loxone vorbereiten.
- KNX Runtime Phase A 32.4.2 pruefen: MQTT -> KNX, KNX -> MQTT, KNX -> Loxone, Dashboard und LiveLog.
- KNX Runtime Phase B 32.4.3 pruefen: KNX Monitor, `/knx_monitor_data`, KNX Hub, MQTT -> KNX, KNX -> MQTT und KNX -> Loxone.
- KNX Runtime Phase C 32.4.4 pruefen: KNX Monitor, `/knx_monitor_data`, `[KNX MONITOR ADD]`, `[KNX SSE]`, MQTT -> KNX, KNX -> MQTT, KNX -> Loxone, Dashboard und Live Log.
- KNX Runtime Phase D1 32.4.5 pruefen: KNX Monitor, Listener Auto-Start, manueller Listener-Start, KNX Telegramm, `[KNX MONITOR ADD]`, `[KNX SSE]`, MQTT -> KNX, KNX -> MQTT und KNX -> Loxone.
- KNX Runtime Phase E 32.4.6 pruefen: `/events/knx_monitor`, `[KNX SSE]`, KNX Monitor, `/knx_monitor_data`, LiveLog-SSE und Status-SSE.
- KNX Runtime Cleanup 32.4.7 pruefen: KNX Monitor, KNX Telegramm, `[KNX MONITOR ADD]`, `[KNX SSE]`, MQTT -> KNX, KNX -> MQTT und KNX -> Loxone.
- Legacy Removal Plan 32.4.8 auswerten: zuerst App Factory und Blueprint-Grundstruktur planen, dann Routen schrittweise aus `app/core.py` entfernen.
- Legacy Removal Phase A 32.4.9 pruefen: App startet unveraendert, `app/routes`-Platzhalter sind vorhanden, `app/extensions.py` und `app/__init__.py` brechen den Legacy-Start nicht.
- Legacy Removal Phase B 32.5.0 pruefen: Dashboard, Sidebar, `/shell_status`, Live Log, `/live_log_data`, `/clear_log` und `/clear_monitor`.
- Legacy Removal Phase C 32.5.1 pruefen: `/settings`, `/settings_embed`, Core-/MQTT-/Influx-Speichern, Sidebar-Links, Plugins, `/backup`, `/restore`, `/objects` und Objektaktionen.
- Legacy Removal Phase D Teil 1 32.6.0 pruefen: `/mqtt`, `/monitor`, `/monitor_data`, `/topics`, `/topics2`, `/mqtt_brokers`, Topic-Speichern und Broker-Test.
- Legacy Removal Phase D Teil 2 32.6.1 pruefen: `/mqtt2udp`, `/udp2mqtt`, `/udp_input`, `/udp_presets`, UDP-Data-Routen, UDP Discovery Status/Toggle und Test-Routen.
- Legacy Removal Phase D Teil 3 32.6.2 pruefen: `/mqtt2lox`, `/mqtt2lox/save`, `/mqtt2lox/test/<int:index>` und `/mqtt2lox_data`.
- Legacy Removal Phase D Teil 4 32.6.3 pruefen: `/test/influx`, `/influx_explorer`, `/influx_explorer/delete` und `/influx_explorer/delete_selected`.
- Legacy Removal Phase E 32.6.4 pruefen: `/global_search`, `/global_search_page`, `/conflicts`, `/conflicts_page` und Dashboard-AJAX-Routen.
- Legacy Removal Phase F 32.6.5 pruefen: `/events/status`, `/events/live_log`, `/events/live_log_full`, `/events/mqtt_monitor`, `/events/knx_monitor`, Reconnect und Keepalive.
- Legacy Removal Phase G Teil 1 32.6.6 pruefen: `/knx`, `/knx_settings_embed`, `/mqtt2knx`, `/udp2knx`, `/knx2mqtt`, `/knx2lox` und jeweilige Data-/Save-/Test-Routen.
- Legacy Removal Phase G Teil 2 32.6.7 pruefen: `/knx_monitor`, `/knx_monitor_data`, `/knx_monitor/influx`, `/knx_monitor/influx_type`, `/knx_monitor/influx_topic`, `/knx_listener_start` und KNX-SSE.
- Legacy Removal Phase H 32.6.8 pruefen: `/start`, `/stop`, `/test/loxone`, `/test/mqtt`, `/internal_broker/save`, `/internal_broker/start`, `/internal_broker/stop`, `/internal_broker/status`.
- Legacy Removal Phase J 32.7.0 pruefen: App Factory, Dashboard, MQTT, UDP, Loxone, KNX, Influx, Backup, Restore, Objektmanager, Live Log, SSE, Bridge und interner Broker.
- Legacy Cleanup 32.7.1 pruefen: alter Ordner entfernt, aktive App-Code-Suche nach alten Legacy-Lader-Begriffen ohne Treffer, Doku auf `app/core.py` aktualisiert.
- Umbenannte Module im laufenden Betrieb gegenpruefen: Dashboard, MQTT -> Loxone, MQTT -> UDP, MQTT -> KNX und Log-Leerzustand.
- Object-Service im laufenden Betrieb gegenpruefen: Objektliste, Objekt bearbeiten, Mapping-Sync, Mapping-Rebuild und Objekt loeschen.
- Loxone-Service im laufenden Betrieb gegenpruefen: MQTT -> Loxone, Loxone IO-Datalist und Dashboard-Zaehler.
- KNX-Service im laufenden Betrieb gegenpruefen: MQTT -> KNX, UDP -> KNX, KNX Monitor mit `[KNX MONITOR ADD]`/`[KNX SSE]`, KNX -> MQTT und KNX -> Loxone.
- Influx-Service im laufenden Betrieb gegenpruefen: Dashboard-Status, Influx Explorer, MQTT/KNX/UDP-Schreibpfade und Testverbindung.
- Runtime-Service im laufenden Betrieb gegenpruefen: Statusanzeige, Live Log, `/events/status`, `/events/live_log` und interner Broker.
- Backup-Service im laufenden Betrieb gegenpruefen: Backup erstellen, Restore-Route, Backup-Dateiliste und Live-Log-Eintraege.
- Template-Service im laufenden Betrieb gegenpruefen: Dashboard, MQTT Hub, Influx Explorer, Objektmanager, KNX Monitor und Mapping-Selects.
- MQTT-Publish-Hilfen aus dem Legacy-Core in `app/services/mqtt.py` ziehen.
- MQTT-Monitor-Endpunkte schrittweise kapseln, ohne URLs zu aendern.
- Service-Tests fuer MQTT-Brokerliste, Monitor-State und Testverbindung ergaenzen.
- Service-Tests fuer `app/services/udp.py` ergaenzen: Message-Format, Mapping, Presets und UDP-Testsendung.
- Weitere UDP-Routen nur bei Bedarf duenner an den Service anbinden; URLs und Formulare bleiben stabil.

## Spaeter

- Interne Broker-Prozessverwaltung aus dem Legacy-Core herausloesen.
- Runtime-/Bridge-Logik erst nach weiterer Port-Stabilisierung modularisieren.
- Objektmanager nur nach ausdruecklicher Freigabe umbauen.


