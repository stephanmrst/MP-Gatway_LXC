## 35.4.0 – 2026-07-30

- Online-Update vollständig auf GitHub Releases umgestellt.
- Neueste Stable-Version und Release-Liste direkt aus GitHub.
- Auswahl von Stable, Beta oder allen Releases.
- Bestimmte Versionen können installiert, erneut installiert oder als Downgrade eingespielt werden.
- Backup und Rollback bleiben aktiv.

# MP-Gateway 35.3.6

## 35.3.6 - 2026-07-30

- Radiolisten für Root-Disk und Debian-Template korrigiert.
- Dialog-Statuswerte werden nun zuverlässig als `on` und `off` übergeben.
- Vorauswahl bleibt `local-lvm` für Root-Disk und `local` für Templates, sofern vorhanden.
- Keine Änderungen an der MP-Gateway-Anwendung.

## 35.3.4 - 2026-07-30

- Root-Disk-Storage wird als Radioliste angezeigt; `local-lvm` ist nach Möglichkeit vorausgewählt.
- Template-Storage wird als Radioliste angezeigt; `local` ist nach Möglichkeit vorausgewählt.
- VLAN wurde in die gemeinsame Options-Checkliste verschoben und ist standardmäßig deaktiviert.
- Die VLAN-ID wird nur abgefragt, wenn „VLAN verwenden“ aktiviert wurde.

## 35.3.3 - 2026-07-30

- VLAN ist im LXC-Installer standardmäßig deaktiviert.
- Der VLAN-Dialog startet jetzt ausdrücklich mit „Nein“ als vorausgewählter Option.

- Fortschrittsbalken des Dialog-Installers repariert: Fortschrittswerte und Installationslog verwenden getrennte Ausgabekanäle.
- Abschlussdaten werden nach dem Dialog als kopierbarer Shelltext ausgegeben.
- Installationsdaten werden zusätzlich unter `/root/mp-gateway-35.3.3-installation.txt` gespeichert.

## 35.3.3 - 2026-07-30

- Neuer blauer Proxmox-/LXC-Installationsassistent auf Basis von `whiptail`.
- Navigation mit Zurück, Weiter und Abbrechen sowie abschließender Zusammenfassung.
- Auswahl von Storage, Netzwerk, Ressourcen, VLAN, Autostart und Root-SSH über Dialogfenster.
- Fortschrittsanzeige und verständliche Fehleranzeige mit Installationsprotokoll.
- Root-SSH lässt sich aus der Weboberfläche wieder zuverlässig aktivieren und deaktivieren.
- Systemd-Sandbox gibt ausschließlich `/etc/ssh/sshd_config.d` für den Admin-Helper frei.
- SSH-Konfiguration wird atomarm überschrieben, geprüft und anschließend neu geladen.

## 35.3.0 - 2026-07-27

- Alte Restore-Experimente entfernt: keine zusätzliche systemd Path-Unit, kein Admin-Helper-Neustart und kein direkter `systemctl`-Aufruf mehr.
- Restore-Code vereinfacht: Dateien wiederherstellen, Erfolg protokollieren und zentralen Prozessneustart anfordern.
- Restore und Web-Update verwenden jetzt gemeinsam `app/services/process_control.py`.
- Der zentrale Neustart beendet MP-Gateway verzögert mit Exit-Code 75; systemd (`Restart=on-failure`) und Docker (`restart: unless-stopped`) übernehmen den Neustart.
- Versionsdatei, Docker-Image-Tag und Update-Manifeste auf 35.3.0 angehoben.

## 35.2.1

- Restore beendet den laufenden Prozess nach erfolgreicher Antwort mit Exit-Code 75.
- systemd (`Restart=on-failure`) und Docker (`restart: unless-stopped`) starten MP-Gateway dadurch vollständig neu.
- Alle Hintergrunddienste lesen danach die wiederhergestellte Konfiguration frisch ein.
- Erfolgsdialog und automatischer Wechsel zum Dashboard bleiben erhalten.
- Lokal/Standalone muss MP-Gateway nach dem Restore manuell neu gestartet werden.

## 35.2.0 - 2026-07-27

- OpenCCU-Runtime erhält nach Restore die wiederhergestellte Konfiguration direkt statt sie erneut über einen möglicherweise abweichenden Modulpfad zu laden.
- Manueller OpenCCU-Speichervorgang und Backup-Restore verwenden jetzt dieselbe Runtime-Aktualisierung.
- Restore-Log zeigt den tatsächlich an die OpenCCU-Runtime übergebenen MQTT-Endpunkt und das Topic.
- Kein Prozess-, Docker- oder LXC-Neustart erforderlich.

## 35.1.9 - 2026-07-27

- OpenCCU-Runtime wird nach Restore explizit neu geladen.
- Wiederhergestellter Aktivierungsstatus und MQTT-Zugangsdaten gelten sofort.
- XML-API-Gerätecache wird nach Restore aktualisiert.
- Kein manueller OpenCCU Aus-/Ein-Schaltvorgang mehr erforderlich.
- Plattformneutral ohne Prozess-, Docker- oder LXC-Neustart.

## 35.1.8 - 2026-07-27

- Kritischer LXC-Pfadfehler behoben: `services.config` verwendet jetzt dieselbe `app.engine.port`-Instanz wie die Anwendung.
- Restore und Laufzeit lesen `config.json` dadurch aus demselben Verzeichnis (`/etc/mp-gateway`).
- Loxone und OpenCCU werden nach Restore live neu geladen; kein Prozessneustart mehr.
- Docker-Verhalten bleibt unverändert und funktionsfähig.

## 35.1.7

- Restore-Zielpfade korrigiert: CONFIG_DIR hat nun Vorrang vor DATA_DIR und Programmverzeichnis.
- `config.json` wird im LXC zuverlässig nach `/etc/mp-gateway/config.json` geschrieben.
- Gleichnamige Paketdateien können produktive Konfigurationen nicht mehr überlagern.
- Restore-Log zeigt zur Kontrolle den tatsächlich verwendeten Zielpfad.
- Erfolgsdialog und automatischer Wechsel zum Dashboard bleiben erhalten.

## 35.1.6

- Restore-Neustart ohne sudo, systemctl oder zusätzliche LXC-Units: Der Python-Prozess startet sich nach der HTTP-Antwort per `exec` neu.
- Erfolgsdialog nach der Wiederherstellung mit automatischer Erreichbarkeitsprüfung.
- Nach erfolgreichem Neustart wird zuverlässig das Dashboard geöffnet.

# Changelog

## 35.1.5

- Debian-LXC: Restore-Neustart nutzt jetzt eine root-eigene systemd Path-Unit und benötigt weder `sudo` noch `systemd-run` aus dem eingeschränkten Anwendungsdienst.
- Der MP-Gateway-Dienst setzt nach dem Restore nur `/var/lib/mp-gateway/.restart-request`; der Neustart erfolgt zwei Sekunden später außerhalb seiner Sandbox.
- Lokale Windows- und Docker-Starts ohne LXC-Helper brechen beim Restore nicht mehr mit `WinError 2` ab.
- Die Rückleitung bleibt auf `/settings_embed`, damit keine doppelte Sidebar entsteht.

## 35.1.3

## 35.1.4

- Restore-Neustart im Debian-LXC ohne `sudo`; der Dienst läuft bereits als root und funktioniert trotz `NoNewPrivileges=yes`.
- Restore leitet zurück auf `/settings_embed`, damit die komplette MP-Gateway-Shell nicht im Inhaltsfenster geladen wird und keine doppelte Sidebar mehr entsteht.
- Versions- und Installationsinformationen auf 35.1.4 aktualisiert.

- Restore-Neustart wird über eine eigenständige, verzögerte `systemd-run`-Unit ausgeführt.
- Der Neustart läuft dadurch außerhalb des MP-Gateway-Dienstes und wird beim Stoppen des Dienstes nicht mehr mit beendet.
- Fehler beim Einplanen des Neustarts werden im Live-Log als `Restore Neustart Fehler` ausgegeben.
- Installer, Sudo-Regel und Versionsinformationen auf 35.1.3 aktualisiert.

## 35.1.2

- Restore lädt die wiederhergestellte Konfiguration durch einen verzögerten, automatischen Dienstneustart neu.
- Loxone- und OpenCCU-Einstellungen aus `config.json` werden dadurch direkt nach dem Restore aktiv.
- Der privilegierte LXC-Helfer unterstützt den eng begrenzten Befehl `service restart`.
- Installer und Versionsinformationen auf 35.1.2 aktualisiert.

## 35.1.1
- Backup-Restore übernimmt `config.json` einschließlich Loxone- und OpenCCU-Einstellungen.
- `monitor_settings.json` und `udp_presets.json` werden beim Restore wiederhergestellt.
- systemd-Service enthält dauerhaft `PYTHONPATH=/opt/mp-gateway/app`.

## 35.1.0
- Debian-13-LXC-Installer und systemd-Service
- persistente Linux-Verzeichnisse für Konfiguration, Daten und Backups
- eingeschränkter Administrationshelfer für SSH-Einstellungen
- Schalter für Root-Login per SSH-Passwort in den Einstellungen
- SSH-Schlüsselzugriff bleibt beim Deaktivieren erhalten

# 35.0.2

- MQTT-zu-MQTT-Routing verwendet jetzt den konkreten Eingangs-Endpunkt aus Broker und Topic.
- Nur eine identische Rückroute auf demselben Broker und Topic wird blockiert.
- Weiterleitungen auf andere Broker oder andere Topics desselben Brokers bleiben erlaubt.
- Quellbroker wird vollständig an die zentrale Objektrouting-Logik übergeben.

# 35.0.1

- MQTT-Quellfelder werden nur noch bei echten MQTT-Quellobjekten angezeigt.
- MQTT-Ziel hinzufügen funktioniert auch nach dynamischem Objektwechsel im Objektmanager.
- MQTT-Zielzeilen werden nach Hinzufügen und Entfernen sauber neu indiziert und gespeichert.

# 35.0.0

- Mehrere MQTT-Ziele pro Objekt
- Broker-Auswahl, eigenes Topic, QoS und Retain je Ziel
- MQTT-Routing zwischen Haupt- und Zusatzbrokern
- Gleichzeitige Verteilung an mehrere Broker
- Automatische Migration bestehender MQTT-Ziele auf den Hauptbroker
- Brokerbezogener Echo- und Schleifenschutz
- Schutz vor identischer Rückroute auf demselben Broker und Topic
- MQTT-Zielliste im Objektmanager bearbeitbar

# 34.7.16

- KNX-Monitor zeigt DPT-1-Ausgangswerte einheitlich als `0` und `1` statt als Python-Boolean `False` und `True`.
- Die interne Bool-Darstellung für die xknx-Telegrammcodierung bleibt unverändert.
- Weiterhin genau ein sichtbarer Monitor-Eintrag je KNX-Sendeversuch.

# 34.7.15

- KNX-Monitor zeigt pro Sendeversuch nur noch einen finalen Eintrag.
- Sichtbarer PENDING-Eintrag vor dem eigentlichen Versand entfernt.
- Erfolgreiche DPT-1-Sendungen erscheinen einheitlich als 0 oder 1.
- Fehler nach erfolgreicher Wertkonvertierung verwenden ebenfalls den normalisierten Wert.

# 34.7.14

- OpenCCU-Booleanwerte werden beim Routing protokollübergreifend als `1` und `0` statt `True` und `False` ausgegeben.
- Die Umwandlung gilt für echte Python-Booleanwerte sowie die Textwerte `true`/`false`.
- Andere OpenCCU-Werte und alle übrigen Quellen bleiben unverändert.

# 34.7.13

- Gezielt behoben: OpenCCU-Werte werden nach einer Weiterleitung an den MQTT-Zieladapter nicht mehr über den eigenen Hauptbroker erneut als MQTT-Eingang geroutet.
- Der Echo-Schutz markiert ausschließlich MQTT-Publishes mit fachlicher Quelle `openccu`; externe MQTT-Quellen und andere Protokollquellen bleiben unverändert.
- Bei fehlgeschlagenem Publish wird die Markierung sofort entfernt.

# 34.7.12

- Diagnoseversion: protokolliert jeden zentralen Routing-Aufruf mit Trace-ID, Objekt-ID, Quelle, Wert, Thread und kompaktem Call-Stack.
- Keine funktionale Änderung an Routing, Zieladaptern oder UI.
- Dient zur eindeutigen Identifikation des noch vorhandenen zweiten Routing-Einstiegspunkts.

# 34.7.11

- Identische OpenCCU/CCU-Jack-Telegramme mit gleichem Topic, CCU-Zeitstempel und Rohpayload werden vor dem Objekt-Routing einmalig dedupliziert.
- Explorer-Empfang und Statistik bleiben erhalten; nur die doppelte Weiterleitung an UDP, MQTT, KNX und weitere Zieladapter wird unterdrückt.
- Echte Zustandswechsel und neue CCU-Zeitstempel werden weiterhin ohne Zeitfilter geroutet.

# 34.7.10

- MQTT/OpenCCU-Eingang ruft nach dem zentralen `record_live_value()`-Routing nicht mehr zusätzlich den alten MQTT-Router auf.
- Der zentrale Objektrouter sendet pro Eingangswert und Zieladapter höchstens einmal.
- Verhindert insbesondere dreifache UDP-Telegramme beim ersten OpenCCU-Livewert.

## 34.7.9
- OpenCCU MQTT-Zieladapter bleibt nach dem Speichern aktiv.
- OpenCCU-Livewerte werden an alle aktiven Zieladapter einschließlich MQTT und KNX geroutet.

# 34.7.7

- Objekt-Routing wird zentral direkt nach `record_live_value()` ausgelöst.
- MQTT-Zieladapter sendet Topic, QoS und Retain aus der Objektkonfiguration.
- KNX-Zielweiterleitung nutzt Gruppenadresse und DPT des Objektadapters.
- Echo-Schutz und bereits bediente Ziele verhindern doppelte Weiterleitungen.
- Keine Änderungen an UI oder Explorern.

# 34.7.6

- Objekt-Livecache vereinheitlicht: `services.object_service` und `app.services.object_service` zeigen nun auf dieselbe Modulinstanz.
- OpenCCU-MQTT-Runtime und Objektmanager/API verwenden dadurch denselben `OBJECT_LIVE_CACHE`.
- Behebt fehlende OpenCCU-Livewerte trotz korrekt empfangener und geparster CCU-Jack-Daten.
- Keine Änderungen am OpenCCU Explorer oder am Objektmanager-Layout.

## 34.7.5

- OpenCCU-Livewerte werden bei Topic-Treffer direkt per Objekt-ID in den zentralen Live-Cache geschrieben.
- Ein direkter Fallback umgeht einen veralteten Endpoint-Index nach Objektanlage oder Reparatur.

# Changelog

## 34.7.5
- OpenCCU-Objekte speichern jetzt Topic, Gerät, Kanal und Datenpunkt vollständig.
- Bereits vorhandene OpenCCU-Objekte werden beim erneuten Erstellen anhand von Topic oder Name erkannt und repariert.
- Der aktuelle Explorer-Wert wird beim Erstellen sofort in den zentralen Live-Cache übernommen.
- Keine Änderungen am OpenCCU Explorer Layout.

## 34.7.3

- OpenCCU/CCU-Jack JSON-Hüllen werden beim MQTT-Eingang entpackt; Explorer und Folgeverarbeitung verwenden direkt das Feld `v`.
- Status `s`, Zeitstempel `ts` und Roh-Payload bleiben als Diagnose-Metadaten erhalten.

## 34.7.2

- OpenCCU-Eingang technisch vom normalen MQTT-Zieladapter getrennt.
- CCU-Jack-Topic wird jetzt als eigene OpenCCU-Quelladresse gespeichert.
- Bestehende OpenCCU-Objekte aus 34.7.0 werden beim Laden automatisch migriert.
- MQTT erscheint bei OpenCCU-Objekten nicht mehr automatisch als aktiver Zieladapter.
- OpenCCU-Livewerte werden direkt über die OpenCCU-Quelle dem Objekt-Livecache zugeordnet.
- CCU-Jack-Payloads `{s, ts, v}` werden auf den eigentlichen Wert `v` reduziert.
- OpenCCU Explorer unverändert.

## 34.7.0

- Objektmanager: OpenCCU als fachliche Quelle konsistent dargestellt.
- OpenCCU im Adapterbereich mit CCU-Jack/MQTT als Transport ergänzt.
- Objektliste kompakter und lange Namen zweizeilig.
- CCU-Jack Payloads werden für bestehende OpenCCU-Objekte automatisch über `v` entpackt.
- OpenCCU Explorer unverändert.

- OpenCCU XML-Gerätecache vollständig von der MQTT-Laufzeit entkoppelt.
- Startfehler der OpenCCU-MQTT-Laufzeit durch fehlenden on_value-Konstruktorparameter behoben.
- Explorer zeigt Geräte und Kanäle auch bei ausgefallenem MQTT weiterhin an.
- Diagnosebereich für XML-API, MQTT, Geräte/Kanäle, Topics und letzte Nachricht ergänzt.
- OpenCCU-Livewerte direkt in den Objektmanager übernommen.
- Fachliche Quelle OpenCCU und technischer MQTT-Transport sauber getrennt.
- OpenCCU → MQTT als aktive Hauptroute behandelt.
- Objektmanager-Schrift und Karten kompakter dargestellt.

# MP-Gateway 34.7.0

## OpenCCU: Quelle und Adapter sauber getrennt

- Die fachliche Objektquelle wird jetzt konsequent aus `object.source` beziehungsweise kompatibel aus `origin_source` ermittelt.
- OpenCCU-Objekte zeigen in Objektliste, Live-Karte, Vorschau und Filter dauerhaft **OpenCCU** statt des technischen MQTT-Transportwegs.
- Der technische Empfangsweg bleibt separat als `adapter` / `transport_adapter` erhalten und beeinflusst die Quellenanzeige nicht mehr.
- Neue OpenCCU-Objekte speichern `source=openccu`; bereits vorhandene Objekte aus 34.6.6 bleiben kompatibel.
- Das Frontend bevorzugt für Live-Karten nun ausdrücklich die konfigurierte Objektquelle.
- OpenCCU-Objektnamen erhalten erste kompakte Datenpunktbezeichnungen, zum Beispiel `Presence`, `Temperatur`, `Luftfeuchtigkeit` oder `Batterie schwach`.

## Vorheriger Stand 34.6.6
- OpenCCU-Objekte als eigene Quelle im Objektmanager
- OpenCCU Explorer nur noch mit „Objekt erstellen“
- Kompaktere Objektnamen und Schriftgrößen

# 34.6.5

- OpenCCU Explorer vollständig auf die XML-API `/config/xmlapi/devicelist.cgi` als einzige Quelle für Geräte- und Kanalnamen umgestellt.
- Getrennte Geräte- und Kanal-Caches mit sichtbarem Lade- und Fehlerstatus ergänzt.
- Linke Seite zeigt ausschließlich Geräte mit Suche sowie Online-/Offline-Anzeige; nur die Geräteliste scrollt.
- Rechte, feststehende Detailseite zeigt Gerätedaten, Kanäle und die per CCU-Jack MQTT empfangenen Live-Datenpunkte.
- Pro Live-Datenpunkt stehen „Objekt erstellen“ und „Objekt verknüpfen“ bereit.
- Layout und feste Explorer-Höhe an den MQTT Explorer angeglichen.

# 34.6.4

- OpenCCU-Klarnamen werden jetzt über die native ReGa-Schnittstelle geladen.
- Topic-Zuordnung erfolgt robust über Seriennummer, Kanal und Datenpunkt.
- Status und konkrete Fehler der Namensauflösung werden im Explorer angezeigt.
- Fehler bei der Vorbelegung des Objektnamens behoben.

## 34.6.3

- OpenCCU Explorer löst MQTT-Topics über den CCU-Jack VEAP-Query-Dienst in Klarnamen auf.
- Geräte-, Kanal- und Datenpunkt-Metadaten werden zehn Minuten im Speicher gecacht.
- Neuer Button „Geräteliste aktualisieren“ mit sichtbarem REST-Cache-Status.
- Detailansicht zeigt Gerätename, Seriennummer, Gerätetyp, Kanal, Datenpunkt, CCU-Datentyp und Einheit.
- „Objekt erstellen“ übernimmt Klarname, MQTT-Topic, Datentyp und Einheit als Vorbelegung.
- MQTT-Empfang, Reconnect und Discovery-Verhalten bleiben unverändert.

## 34.6.2

- OpenCCU Explorer: Kartenhintergrund an das Dark-Mode-Layout angepasst.
- Hover- und Auswahlzustand der Discovery-Einträge klar lesbar gestaltet.
- Text-, Livewert- und Metadatenfarben korrigiert.

## 34.6.1

- Dedizierte CCU-Jack MQTT-Verbindung mit automatischem Reconnect.
- Automatisches Subscribe auf das konfigurierte Topic-Präfix.
- Live-Empfang mit Discovery-Liste ohne Duplikate; bestehende Topics werden aktualisiert.
- Detailansicht für Topic, Livewert, Datentyp, QoS, Retain und Zeitstempel.
- Objekte können direkt aus dem OpenCCU Explorer als MQTT-Quelle erstellt werden.
- REST und Klarnamen-Auflösung bleiben bewusst für eine spätere Version außen vor.

## 34.6.0

- OpenCCU / CCU-Jack Grundkonfiguration in den Einstellungen.
- Verbindungstest für OpenCCU HTTP und CCU-Jack MQTT.
- Neuer OpenCCU Explorer als Basis für Livewerte und Klarnamen.

# MP-Gateway 34.5.2

- Update-Status direkt im Sidebar-Footer ergänzt.
- Grüner Punkt zeigt eine aktuelle Version, Orange ein verfügbares Update und Rot eine fehlgeschlagene Prüfung.
- Bei verfügbarem Update erscheint zusätzlich der Hinweis „Update verfügbar“.
- Der komplette Sidebar-Footer öffnet direkt das Update-Center.
- Automatische Online-Prüfung startet verzögert und wird im Browser auf höchstens einmal pro 24 Stunden begrenzt.

# MP-Gateway 34.5.1

- Online-Updatequelle auf `stephanmrst/MP-Gateway` umgestellt.
- Das Release-Manifest wird aus dem `main`-Branch des neuen Repositorys geladen.
- Release-ZIP-Adressen zeigen jetzt auf das MP-Gateway-Repository.

# MP-Gateway 34.5.0

- Neues Update-Center mit Online-Update über ein öffentliches Release-Manifest.
- Online-Version, Veröffentlichungsdatum und Changelog werden direkt angezeigt.
- Online-ZIP wird gestreamt heruntergeladen und optional per SHA256 geprüft.
- Online- und lokale ZIP-Updates verwenden dieselbe Paketprüfung und Installationsroutine.
- Lokale ZIP-Updates bleiben für Entwicklung und Offline-Systeme vollständig erhalten.

# 34.4.6

- Sidebar-Footer bereinigt: Es wird nur noch „MP-Gateway 34.4.6“ angezeigt.
- Den veralteten Hinweis „MQTT2Lox Technikbasis“ aus der Sidebar entfernt.

# 34.4.5

- Browser-eigene Bestätigungsdialoge beim Installieren eines Updates und beim Neustart durch ein einheitliches MP-Gateway-Modal ersetzt.
- Neustart-Rückmeldungen werden jetzt innerhalb der Update-Seite angezeigt statt als Browser-Alert.

# 34.4.4

- Verhindert die doppelte Sidebar auch bei abgelehnten Updatepaketen, etwa bei einem Downgrade.
- Fehler der Paketprüfung werden über die eingebettete Update-Ansicht angezeigt.

# 34.4.3

- Update-Neustartstatus wird bei jedem Statusabruf sicher erneut abgeglichen.
- Der Status wird nur zurückgesetzt, wenn der laufende Prozess nach der Update-Installation gestartet wurde.
- Docker-Neustarts werden dadurch auch dann erkannt, wenn der einmalige Startup-Abgleich zu früh lief.

# 34.4.2

- Update-Installation auf eine reine JSON-Antwort umgestellt; die eingebettete Update-Seite aktualisiert nur Status, Version und Neustartanzeige, ohne ein vollständiges Layout in den Contentbereich zu laden.
- Neustartstatus wird beim echten Programmstart automatisch abgeglichen und nach erfolgreichem Start der installierten Version zurückgesetzt – einschließlich Docker-Neustarts über die Restart-Policy.

# 34.4.1

- Eigenständigen Update-Link aus der linken Sidebar entfernt.
- Der Update-Manager bleibt vollständig über Einstellungen → Update erreichbar.
- An der Update-Funktion selbst wurde nichts verändert.

# 34.4.0

- Plattformneutralen Update-Manager für Docker, LXC, Debian/systemd und Standalone ergänzt.
- Neue Update-Seite mit Systeminformationen, ZIP-Upload, Paketprüfung, Installation, Fortschrittsanzeige und Neustartfunktion.
- Updatepakete werden auf Produkt, Version, Mindestversion, Struktur, Größe und sichere ZIP-Pfade geprüft.
- Vor jeder Installation wird ein Programm-Backup erstellt; bei Fehlern erfolgt automatisch ein Rollback.
- Persistente Bereiche wie Konfiguration, Daten, Logs, Backups, Instanzdaten und `.env` werden niemals überschrieben.
- Docker-Webupdates bleiben im persistenten Anwendungsverzeichnis erhalten; neuere Container-Images können weiterhin regulär aktualisieren.

## 34.3.2

- Objektliste im Objektmanager auf eine reine, kompakte Namensliste reduziert.
- Initialen, Datentyp, Livewert, Quelle, Status und Adapter-Badges aus der linken Spalte entfernt.
- Dynamisch nachgeladene Objektkarten verwenden dieselbe reduzierte Darstellung.

## 34.3.1
- Objektmanager auf eine feste dreispaltige Explorer-Oberfläche umgestellt.
- Linke Objektliste beibehalten und mittleren Objekt-Explorer dauerhaft eingeblendet.
- Obere Registerkarten sowie Klassisch/Preview-Umschaltung entfernt.
- Klick auf Allgemein, Live, Routing oder einen Adapter öffnet direkt die passende Konfiguration rechts.
- Bestehende Speicher-, Adapter-, Routing- und Live-Backendlogik unverändert weiterverwendet.

# 34.3.0

- Objektmanager: umschaltbare klassische und neue Preview-Ansicht ergänzt.
- Neue rechte Objektübersicht mit echten Live-Daten, Objektinformationen, Adapterstatus und Routing.
- Adapter im Preview-Panel sind anklickbar und öffnen direkt den jeweiligen Konfigurations-Tab.
- Preview-Modus wird lokal im Browser gespeichert und bleibt bei Objektwechseln erhalten.
- Bestehende klassische Ansicht bleibt unverändert verfügbar.

# 34.2.2

- Influx Explorer: „Objekt öffnen“ navigiert wieder innerhalb der MP-Gateway-Hauptansicht, sodass die Sidebar erhalten bleibt.
- Das gefundene Objekt wird im Objektmanager über den korrekten Parameter `selected` direkt ausgewählt.
- Auch „Objekt erstellen“ verwendet nun dieselbe eingebettete Navigation.

# 34.2.1

- Influx Explorer liest jetzt alle vorhandenen Influx-Tags dynamisch statt nur `topic`.
- Measurements werden nativ gruppiert; Fields und unterschiedliche Tag-Serien bleiben getrennt sichtbar.
- Detailansicht zeigt Bucket, Measurement, Field, Datentyp, Zeit, Punktanzahl und sämtliche Tags.
- Bereits zugeordnete Objektmanager-Objekte werden erkannt und können direkt geöffnet werden.
- Nicht zugeordnete Serien bieten einen klaren Button „Objekt erstellen“.

# MP-Gateway 34.2.0

- Influx Explorer als Live-Monitor mit dreigeteilter Measurement-, Field- und Detailansicht neu aufgebaut.
- Daten werden in Sammelabfragen direkt aus realen Influx-Punkten gelesen; kein lokaler Topic-Cache.
- Automatische Aktualisierung alle 5 Sekunden mit Pause-, Suche- und Zeitraumfunktion.
- Letzter Wert, Zeitstempel, Datentyp und Punktanzahl je Field sichtbar.
- Influx-Serie kann direkt gelöscht und als Influx-Adapter in den Objektmanager übernommen werden.

# 34.1.2

- KNX kann im Objektmanager wieder gleichzeitig an MQTT und UDP geroutet werden.
- Die fehlende unterstützte Route `KNX -> UDP` wurde in der objektbasierten Routing-Matrix ergänzt.
- Routing-Tab und Dashboard-Zähler erkennen die UDP-Route dadurch wieder direkt aus `objects.json`.

# 34.1.1

- Quellenbestimmung korrigiert: explizite Eingänge (`direction=in`) haben Vorrang vor bidirektionalen Ziel-/Rückkanälen.
- Dashboard-Routenzähler werden direkt aus den aktiven Objekt-Routen berechnet.
- KNX → MQTT und andere objektbasierte Routen werden wieder korrekt angezeigt.

# 34.1.0

- Dashboard vollständig objektzentriert; alte Mapping-Kacheln entfernt.
- Sämtliche historischen Mapping-URLs leiten jetzt konsequent zum Objektmanager weiter.
- Auch alte Save-, Test-, Copy- und Data-Endpunkte können keine Legacy-Dateien mehr verändern.
- Runtime-Routen werden weiterhin ausschließlich aus `objects.json` erzeugt.
- Docker archiviert vorhandene V33-Mappingdateien beim Start unverändert im Backup-Verzeichnis.
- Keine funktionale Erweiterung; reine Konsolidierungs- und Aufräumversion vor dem Influx-Monitor-Umbau.

# 34.0.6

- Docker-Start synchronisiert nun auch das top-level Verzeichnis `static/` aus dem Container-Image in das persistente Anwendungsverzeichnis.
- Behebt `GET /static/css/sidebar.css 404` bei neu erstellten Containern.
- Sidebar- und Hauptlayout-CSS werden damit im Container wieder vollständig geladen.

# 34.0.5

- Objekt Export / Import direkt in die Einstellungen integriert.
- Keine separate Seite mehr für den normalen Export-/Import-Ablauf.
- Import-Ergebnis wird direkt in den Einstellungen angezeigt.

# 34.0.4

- Dashboard-Fehler bei fehlender interner Broker-Konfiguration behoben.
- Zugriff auf die zentrale Standardkonfiguration des internen Brokers korrigiert.

# 34.0.2

- Fehlende `_object_routes()`-Brücke zur neuen Objekt-Runtime wiederhergestellt.
- Verbliebene Dashboard-, Explorer- und Legacy-UI-Aufrufe auf die objektbasierten Loader umgestellt.
- Keine alten Mapping-Dateien werden dadurch wieder aktiviert; `objects.json` bleibt die einzige Routing-Quelle.

# 34.0.1

- Objektmanager ist die einzige Runtime-Quelle für Routen und Influx-Ziele.
- Legacy-Dateien wie `topic_config.json`, `mqtt2lox.json`, `mqtt2udp_config.json` und weitere Mapping-Dateien werden von der Runtime ignoriert.
- „Template Export / Import“ heißt jetzt „Objekt Export / Import“.
- Export und Import enthalten ausschließlich vollständige Objektmanager-Objekte aus `objects.json`.
- Alte Mapping-Templates werden bewusst nicht mehr importiert.

# 34.0.1

- Influx Explorer ermittelt Serien jetzt ausschließlich aus tatsächlich vorhandenen Datenpunkten im gewählten Zeitraum.
- Historische beziehungsweise gelöschte Topic-Werte aus dem Influx-Schemaindex werden nicht mehr angezeigt.
- Nach dem Löschen verschwinden leere Serien vollständig aus der Tabelle.
- Serien ohne `topic`-Tag werden sauber von getaggten Serien getrennt.

# 33.4.69

- Influx Explorer vollständig auf echte InfluxDB-Liveabfragen umgestellt.
- Liest alle tatsächlich vorhandenen Measurements im konfigurierten Bucket, nicht mehr nur das konfigurierte Standard-Measurement.
- Zeigt Topic-Tags nur dort, wo sie in Influx wirklich vorhanden sind.
- Measurements ohne Topic-Tag werden ebenfalls angezeigt.
- Gelöschte Einträge verschwinden nach dem Neuladen vollständig.
- Löschen arbeitet jetzt gezielt nach Measurement und optionalem Topic-Tag.
- Zeitraumfilter für 1 Stunde bis 1 Jahr ergänzt.

# 33.4.68-rc2

- GitHub-saubere Docker-Version ohne lokale Konfigurations-, Objekt- oder Laufzeitdaten.
- Leere persistente Verzeichnisse werden über `.gitkeep` bereitgestellt.
- Persönliche Beispiel-IP-Adressen in den Standardwerten wurden neutralisiert.
- Docker-Hostnetzwerk und das zentrale Volume `mpgateway_data` bleiben unverändert.

# 33.4.68-rc1

- Docker RC1 mit einem persistenten Volume `mpgateway_data`.
- Komplette Anwendung wird beim ersten Start einmalig in das Volume kopiert.
- KNX-, MQTT- und UDP-Runtime unverändert gegenüber 33.4.67.

## 33.4.67

- Sidebar aufgeraeumt: `Objektmanager V33` heisst jetzt `Objektmanager` und steht direkt unter dem Dashboard.
- `KNX Testcenter` steht jetzt direkt unter der globalen Suche.
- Keine Aenderungen an KNX-, MQTT- oder UDP-Runtime.


## 33.4.66
- Basis wieder auf den stabilen Stand 33.4.63 gesetzt.
- Neu gespeicherte UDP-Ziele werden nach dem Adapter-Speichern in den KNX-RAM-Index übernommen.
- Der Index-Neuaufbau läuft ausschließlich im asynchronen Objekt-Routen-Reload, niemals im KNX-Empfangspfad.
- Neue Objekte aktivieren UDP-Senden nicht mehr automatisch.
- Die UDP-Routenprüfung berücksichtigt `target_enabled`.
## 33.4.58

- KNX-DPT-1-Telegramme ohne hinterlegte Zuordnung werden im Explorer als `1.001` statt `unbekannt` gekennzeichnet.
- Hohe Laufzeitlast durch ausführliche KNX-PERF-/TRACE-Logs im Telegramm-, Routing- und Snapshot-Pfad entfernt.
- KNX-Explorer und KNX→MQTT reagieren dadurch wieder unmittelbar, ohne DPT-9- oder Verlaufslogik zu verändern.

# 33.4.56

- Alte Legacy-Mappingdaten vollständig entfernt.
- Die bisherigen JSON-Mappingdateien für MQTT/Loxone/UDP/KNX sind jetzt leer.
- Objektmanager-V33-Routen, KNX-Testcenter und aktuelle Explorer bleiben unverändert.
- KNX-DPT-Decodierung, Verlauf und Laufzeitpfade wurden nicht verändert.

## 33.4.55

- MQTT Hub aus der Sidebar entfernt; `/mqtt` leitet direkt auf den MQTT Explorer weiter.
- KNX Hub auf ein eigenstaendiges KNX Testcenter reduziert; Gateway-Einstellungen und KNX Explorer sind dort direkt verlinkt.
- Alte Mapping-Explorer fuer MQTT->Loxone, MQTT->UDP, UDP->MQTT, MQTT->KNX, UDP->KNX, KNX->MQTT und KNX->Loxone aus dem sichtbaren Workflow entfernt; direkte GET-Aufrufe leiten zum Objektmanager V33 weiter.
- Bestehende Legacy-Mappingdaten und Runtime-Loader bleiben vorerst kompatibel, damit vorhandene Installationen beim UI-Cleanup keine Routen verlieren.
- KNX-DPT-Decodierung, Explorer-Verlauf, Routing und Performancepfad unveraendert gelassen.

## 33.4.54

- KNX-Verlaufspuffer auf 250 Ereignisse erweitert; die UI zeigt weiterhin maximal 15 Zeilen.
- Ohne Auswahl werden die letzten 15 Telegramme insgesamt angezeigt.
- Bei ausgewaehlter Gruppenadresse werden deren letzte bis zu 15 Telegramme angezeigt, statt nur Treffer aus dem globalen 15er-Puffer.
- KNX-DPT-Decodierung, Routing und Performancepfad unveraendert gelassen.

## 33.4.53

- KNX Explorer: Die Auswahl einer Gruppenadresse in der linken Liste filtert den Verlauf nicht mehr. Die Auswahl bleibt ausschließlich für die Detailansicht aktiv.
- Dadurch zeigt der Verlauf wieder unabhängig von der markierten Gruppenadresse die letzten maximal 15 Telegramme.
- KNX-DPT-Decodierung, Routing und Performance bleiben unverändert.

# Changelog

## 33.4.52

- KNX-Telegramme ohne konfigurierte DPT-Zuordnung werden wieder vorsichtig anhand ihrer Payload-Laenge decodiert (`5.xxx auto`, `9.xxx auto`, `14.xxx auto`) statt nur als Raw angezeigt; DPT-1 bleibt als echte Integerwerte `0`/`1`.
- Konkrete DPTs aus `topic_config` werden in den schnellen KNX-GA-Runtime-Index uebernommen; fuer `0/2/0` bis `0/2/5` sind `9.001`/`9.007` hinterlegt.
- Bekannte DPT-Einheiten werden im Explorer wieder angezeigt, ohne Einheiten bei automatischer Erkennung zu erfinden.
- Der KNX-Verlauf wird zusaetzlich im Browser-LocalStorage gespiegelt und ueberlebt damit leere Snapshots, SSE-Reconnects und Seiten-Reloads; nur der manuelle Clear loescht ihn.
- DPT 12/13 wurden im vorhandenen Decoder ergaenzt und 27 KNX-Regressionstests laufen erfolgreich.

## 33.4.51

- KNX-Decodierung, DPT-Lookup, Runtime-GA-Index und Gruppenadressliste wurden exakt auf den nachweisbaren Code-Snapshot 33.4.47 zurueckgesetzt; der KNX-Speed-/Routing-Worker aus 33.4.44 und die DPT-1-Normalisierung aus 33.4.45 bleiben erhalten.
- Die in 33.4.48 bis 33.4.50 eingefuehrte breite DPT-Dispatcher-/Payload-Laengen-Inferenz, die zusaetzliche Gruppenadress-DPT-Datei und der DPT-Editor im KNX Explorer wurden zurueckgenommen.
- `applyKnxSnapshot()` behaelt seine bisherige `data.last`-/`knxLatestByGa`-Behandlung; nur der History-Block ignoriert leere Snapshots und leert ausschliesslich bei `history_cleared=true` plus `clear_reason=explicit_user_action`.
- Nur die erfolgreiche Antwort des manuellen KNX-Clear-Endpunkts setzt die beiden expliziten Clear-Felder.
- Regressionstests sichern DPT `1.001`, numerische DPT-9-Werte, den unveraenderten Latest-State und den Schutz vor automatischem History-Leeren ab.

## 33.4.50

- KNX-Gruppenadressen erhalten mit `config/knx_group_addresses.json` eine persistente DPT-/Namenszuordnung; die Test-GAs `0/2/0` bis `0/2/5` sind dort mit `9.001`/`9.007` hinterlegt.
- Der KNX-Runtime-Index liest die Gruppenadress-Konfiguration nach Objekt-/Routen-DPTs und vor `topic_config`, loggt `KNX DPT LOOKUP ...` und nutzt sie ohne Dateizugriff im Telegramm-Callback.
- Der KNX Explorer kann den DPT einer ausgewählten Gruppenadresse direkt speichern; die API `/api/knx/group-address/dpt` aktualisiert Config, Runtime-Index und den aktuellen Explorer-Eintrag ohne Neustart.
- Die KNX-Decodierung nutzt einen Dispatcher fuer DPT-Hauptgruppen 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18 und 20.
- Fehlende DPTs werden vorsichtig ueber Payload-Typ/-Laenge als `1.xxx auto`, `5.xxx auto`, `9.xxx auto`, `14.xxx auto` oder `16.xxx auto` decodiert; Einheiten werden nur bei konkretem DPT gesetzt.
- Der KNX-History-Snapshot-Block nutzt kein `backendCount === 0` mehr als Loeschfreigabe.

## 33.4.49

- Der KNX Explorer behaelt eine bereits sichtbare lokale History, wenn ein spaeter Snapshot leer ist; leere Snapshots ersetzen den Verlauf nur noch beim initial leeren Zustand.
- Das Frontend loggt bei ignorierten leeren Snapshots zusaetzlich `backend_count`, damit API-/Runtime-Rennen sichtbar bleiben.
- DPT-9-Decoding aus 33.4.48 bleibt unveraendert; der schnelle KNX-RX-/Routingpfad wurde nicht umgebaut.

## 33.4.48

- KNX-DPT-9-Werte werden aus den echten 2-Byte-APDU-Nutzdaten wieder als KNX-Float decodiert, z. B. `19 2F` zu `24.24` und `1B 1F` zu `63.92`.
- DPT `9.001` und `9.007` liefern im Explorer wieder zweistellige `display_value`-Werte inklusive Einheit (`°C` bzw. `%`) statt `Raw: <HEX>`.
- Der KNX-Runtime-GA-Index ergaenzt DPTs aus Legacy- und Topic-Konfigurationen, ohne vorhandene Objektmetadaten fuer dieselbe Gruppenadresse durch Minimaldaten zu ersetzen.
- Tests sichern DPT `1.001`, DPT `9.001`, DPT `9.007`, Raw-Fallback und die KNX-History-Snapshot-Stabilitaet gemeinsam ab.

## 33.4.47

- KNX-History-Schreibzugriffe laufen jetzt ueber zentrale Funktionen fuer Append, Snapshot und manuelles Clear.
- Die KNX-API kennzeichnet Verlaufsausgaben eindeutig als `snapshot=true` mit `history`, `history_count` und `history_object_id`; `log` bleibt nur als Legacy-Alias enthalten.
- Der KNX Explorer uebernimmt History nur noch aus expliziten Snapshots oder aus expliziten `knx_history_entry` Live-Events; Status-/Teilpayloads koennen den Verlauf nicht mehr ersetzen.
- Frontend-Polling nutzt eine Request-Sequenz, damit aeltere Antworten keinen neueren Verlauf ueberschreiben.
- Backend-Logs enthalten `KNX HISTORY INSTANCE` und `KNX HISTORY CHANGE` mit Objekt-ID, Groesse und Grund.

## 33.4.46

- Der KNX Explorer trennt den lokalen History-State jetzt explizit vom aktuellen Gruppenadress-State, damit Status-/Teil-Updates den Verlauf nicht leeren.
- Leere oder unvollstaendige Live-Payloads ohne Verlauf ersetzen die sichtbare KNX-History nicht mehr.
- KNX-History-Aenderungen werden mit `KNX HISTORY action=...` protokolliert, um Append/Clear-Stellen eindeutig nachvollziehen zu koennen.
- Tests sichern ab, dass Polling ohne neue Telegramme, alte Timestamps und KNX-Statuswechsel den 15er-Verlauf nicht leeren.

## 33.4.45

- KNX-DPT-1-Schaltwerte werden im zentralen RX-Decode-Ergebnis als Integer `1`/`0` mit `display_value` `1`/`0` gefuehrt, nicht mehr als Boolean oder `EIN`/`AUS`.
- KNX->MQTT normalisiert DPT-1-Payloads vor dem Publish auf `1`/`0`, auch im schnellen Objektmanager-Routingpfad.
- KNX-Monitor-Eintraege erhalten eindeutige Event-IDs; der Verlauf bleibt ein serverseitiger `deque(maxlen=15)`-Ringpuffer getrennt vom aktuellen Zustand je Gruppenadresse.
- Der KNX Explorer behaelt vorhandene History im Frontend, falls ein Live-Event keinen `log`-Snapshot enthaelt.

## 33.4.44

- KNX-RX misst den Live-Pfad jetzt mit `KNX PERF ...` Logs fuer RX, Decode, Explorer, Queue, Live, Routing und MQTT-Publish.
- Der xknx-Callback fuehrt keine KNX->MQTT/KNX->Loxone-Netzwerkweiterleitung mehr direkt aus, sondern legt ein Event in einen eigenen KNX-Routing-Worker.
- Beim Listener-Start wird ein RAM-Index fuer KNX-Gruppenadressen aus Objektmanager und Legacy-Mappings aufgebaut, damit der Callback keine Mapping-Dateien laden muss.
- DPT-Werte wie `unbekannt`, `unknown`, `auto` oder `-` gelten nicht mehr als konfigurierter DPT und blockieren den xknx-Binary-Fallback nicht.

## 33.4.43

- Der KNX-DPT-Lookup normalisiert Gruppenadressen jetzt auch fuer Objektindex und Live-Match, damit Varianten wie `0/0/09` und `0 / 0 / 9` dieselbe GA treffen.
- Eindeutige xknx-`DPTBinary`-Payloads werden ohne konfigurierten DPT als `payload_inferred` zu `EIN`/`AUS` decodiert; unbekannte Nicht-Binary-Payloads bleiben Raw.
- Der KNX-Explorer-State behaelt den typisierten `value` (`true`/`false`) und liefert `display_value`, `raw_value`, `decoded`, `dpt_source` sowie Trace-Logs fuer `0/0/9`.

## 33.4.42

- Die KNX-RX-Decodierung laeuft jetzt zentral ueber `decode_knx_value` und nutzt zuerst den von xknx gelieferten Payload-Wert.
- DPT `1.xxx` Short-APDU-Werte werden als Boolean decodiert; `False`, `0` und APDU `00` bleiben gueltig und erscheinen als `AUS` statt `Raw: 00`.
- Der KNX Explorer erhaelt zusaetzlich `display_value`, `raw_value`, `decoded`, `source_address`, `timestamp` und `receive_count`; GroupValueRead bleibt als `Leseanfrage` sichtbar.
- Der DPT fuer KNX-Gruppenadressen wird vor Legacy-Mappings aus dem Objekt-Endpunkt-Cache gelesen.

## 33.4.41

- Der KNX Explorer zeigt empfangene `GroupValueWrite`-Telegramme jetzt auch ohne bekannten DPT als Raw-Eintrag an.
- DPT `1.xxx` wird fuer Schaltwerte als `EIN`/`AUS` dargestellt; `False` bzw. `0` wird nicht mehr als leerer oder verwerfbarer Wert behandelt.
- KNX-Monitor-Eintraege enthalten jetzt Telegrammtyp und APDU-Hex, und der Verlauf zeigt Typ sowie APDU als eigene Spalten.

## 33.4.40

- Der KNX Listener registriert RX-Telegramme wieder ueber `xknx.telegram_queue.register_telegram_received_cb`, den zuvor funktionierenden xknx-Queue-Hook.
- Der alternative Konstruktor-Callback aus 33.4.38 wurde fuer RX wieder entfernt, damit empfangene Bus-Telegramme in der vorhandenen Runtime wieder ankommen.
- Die Explorer-Anzeige fuer RX-vor-OUT bleibt erhalten: Sendefehler ueberschreiben vorhandene Empfangseintraege nicht.

## 33.4.39

- Der KNX Explorer verwendet fuer `Objekt erstellen / verknuepfen` im eingebetteten Layout wieder denselben `mqtt2lox:navigateFrame`-Shell-Navigationspfad wie MQTT und UDP.
- Der Objektmanager wird beim KNX-Explorer-Create nun im Content-Frame mit aktivem `/objects_v33`-Menuepunkt geoeffnet.
- Die KNX-Prefill-Daten fuer Gruppenadresse, DPT, Quelle und Livewert bleiben unveraendert erhalten.

## 33.4.38

- Der KNX Listener registriert empfangene Bus-Telegramme wieder direkt ueber `XKNX(..., telegram_received_cb=...)`.
- OUT-/ERROR-Eintraege aus Objektmanager-Sends ueberschreiben einen vorhandenen RX-Eintrag derselben Gruppenadresse nicht mehr in der linken KNX-Explorer-Liste.
- Der KNX Explorer zeigt damit empfangene Telegramme wieder als Empfangsseite, waehrend Senden/Fehler weiterhin im Verlauf sichtbar bleiben.

## 33.4.37

- Objektmanager-KNX-Sends uebergeben den KNX-Explorer-Monitor-Callback jetzt an den gemeinsamen KNX-Sendepfad.
- Der KNX Explorer erhaelt bei ausgehenden Objekt-Routen sofort `OUT/PENDING` und bei fehlender Tunnelverbindung `OUT/ERROR` fuer die betroffene Gruppenadresse.
- KNX-Sendefehler bleiben damit nicht mehr nur im Live-Log sichtbar, sondern fuellen auch die Explorer-Liste und den Detailbereich.

## 33.4.36

- KNX-TX loggt die vorbereitete DPT-Nutzlast jetzt bereits vor dem Tunnel-/Runtime-Check als `KNX TX prepared`.
- Fehlende KNX-Tunnelverbindungen melden nun Status, Modus, Gateway, lokale IP und den letzten xknx-Fehler statt nur einer generischen Fehlermeldung.
- Der KNX Listener setzt seinen Runtime-Thread-State beim Stop/Fehler sauber zurueck und behaelt den letzten Tunnel-Fehler fuer die Senddiagnose.

## 33.4.35

- Der KNX Explorer nutzt fuer `Objekt erstellen / verknuepfen` jetzt den zentralen `/objects_v33/create_from_explorer`-Workflow.
- KNX-Explorer-Importe befuellen das neue Objekt mit Quelle `knx`, Gruppenadresse, DPT und optionalem Livewert statt Legacy-KNX-Mappings zu erzeugen.
- Der zentrale Objektmanager-Explorer-Import kennt KNX jetzt explizit als Quelle und speichert die KNX-Daten im KNX-Adapter des Objekts.

## 33.4.34

- KNX-TX-Logging zeigt jetzt zusaetzlich reine DPT-Payload-Bytes mit `payload_len` und `payload_hex`, getrennt vom APDU-Hex.
- Objektbasierte KNX-Ausgaenge sowie MQTT->KNX und UDP->KNX loggen den durchgereichten DPT vor dem eigentlichen Senden.
- DPT-9-Testdiagnose fuer `69.28` auf `9.001` liefert damit explizit `payload_len=2` und die zweibyte Nutzlast.

## 33.4.33

- KNX-Senden verwendet jetzt einen zentralen DPT-Encoder fuer `GroupValueWrite` und loggt GA, DPT, Rohwert, normalisierten Wert sowie Encoder.
- Fehlender DPT wird beim KNX-Senden nicht mehr still auf `1.001` gesetzt; der Versand wird mit `KNX send skipped: missing DPT for GA ...` abgebrochen.
- DPT `9.xxx` und `14.xxx` werden generisch ueber xknx-DPT-Float-Klassen kodiert, damit Werte wie `69.28` als echter KNX-Float gesendet werden.

## 33.4.32

- Sichtbare Expertenmapping-/Experteneinstellungsbereiche wurden aus MQTT Explorer, Loxone Explorer, UDP Explorer und KNX Explorer entfernt.
- MQTT-JSON-Key-Mapping-Dropdowns fuer Expertenziele werden im Explorer nicht mehr gerendert.
- Backend-Routen, Mapping-Funktionen, Datenstrukturen und bestehende Konfigurationen bleiben unveraendert.

## 33.4.31

- Der KNX Explorer nutzt jetzt die kompakte MQTT-/Loxone-Explorer-Struktur mit Header, Suche, Aktionen, linker Gruppenadressenliste und rechtem Detailbereich.
- Die vorherige Dashboard-/Card-Anmutung mit Statusbadge-Leiste wurde aus der KNX-Explorer-Seite entfernt.
- Objektanlage, GA-Kopie, Expertenmapping, Influx-Schalter und Verlauf bleiben erhalten, sind aber in den rechten Detailbereich verschoben.

## 33.4.30

- `KNX Monitor` ist in Sidebar, KNX-Hub und Seitenkopf als `KNX Explorer` benannt.
- Die KNX-Liveansicht nutzt jetzt dieselbe Grundstruktur wie die Explorer-Seiten: Kopfbereich, Toolbar, Statusbadges, Explorer-Liste links und Detailbereich rechts.
- KNX-Routen, Backend-Endpunkte, Listener, Telegrammverarbeitung und Influx-/Mapping-Aktionen bleiben unveraendert.

## 33.4.29

- Der Objektmanager-Filter arbeitet jetzt nur noch nach Objektquelle.
- Zieladapter, aktivierte Protokolle, Routen und Aktivstatus beeinflussen die Filterauswahl nicht mehr.
- Die sichtbaren Filterchips sind auf `Alle`, `MQTT`, `Loxone`, `UDP` und `KNX` reduziert.

## 33.4.28

- Die Sidebar zeigt fuer UDP nur noch den Eintrag `UDP Explorer`.
- `UDP Hub` und `UDP Monitor` wurden aus der Navigation entfernt; Backend-Routen und Funktionen bleiben unveraendert erreichbar.
- UDP-Monitoring, Einstellungen und Mapping-Links bleiben ueber den UDP Explorer gebuendelt.

## 33.4.27

- Die Live-API nutzt fuer Objekt-Livewerte jetzt explizit denselben Objekt-Service wie `app_core`, damit UDP-Updates und Live-Tab denselben Runtime-Store lesen.
- Die Live-API loggt pro Objekt `LIVE TAB DEBUG` mit Memory-State, Objektfeldern und Rueckgabe-Payload.
- UDP-Objektmatches loggen `UDP LIVE UPDATE DEBUG` mit Objekt-ID, Wert, Modus, Endpoint sowie before/after Memory-State.
- Das Live-State-Feld `source` wird fuer die API als Anzeigequelle wie `UDP` geliefert, waehrend interne Protokollfelder kleingeschrieben bleiben.

## 33.4.26

- Der Objekt-Service besitzt jetzt `update_object_live_value(...)` als zentralen Runtime-Livewert-Updater fuer einzelne Objekte.
- `record_live_value(...)` nutzt diesen Updater fuer MQTT, Loxone, KNX und UDP gemeinsam und setzt `value`, `last_value`, `live_value`, `timestamp`, `updated_at`, `endpoint`, `adapter` und `status=aktiv`.
- UDP-Livewerte fuellen damit Live-Tab und Objektkarte direkt nach dem UDP-Match, ohne Aenderung an Quelle oder Routing.

## 33.4.25

- UDP-Objektmatches schreiben den Livewert jetzt ueber denselben gemeinsamen `record_live_value`-Pfad wie MQTT, KNX und Loxone.
- UDP-JSON-Pakete ohne eigenes Topic pruefen zusaetzlich die JSON-Leaf-Pfade, damit Objekte wie `params/pm1:0/apower` den extrahierten Wert im Objekt-Live-State erhalten.
- Der UDP-Live-Matcher bevorzugt konfigurierte Topic- und JSON-Pfad-Quellen gegenueber reinem Listen-Port-Match, damit JSON-Pakete keine anderen UDP-Objekte auf demselben Port ueberschreiben.

## 33.4.24

- Objektkarten lesen Quelle jetzt konsequent aus der Routing-Konfiguration bzw. `display_source` und nicht mehr aus dem Live-State.
- UDP->MQTT und andere Zielrouten koennen die Source-Anzeige nicht mehr auf MQTT kippen.
- Objektkarten und Detailansicht bleiben nach Reload auf der konfigurierten Eingangsquelle.

## 33.4.23

- UDP->MQTT-Routings behalten die echte Eingangsquelle im Live-Cache und schreiben MQTT nur noch als Ziel in `last_target`/`target_protocol`/`output_protocol`.
- Der MQTT-Echo-Guard erkennt interne Objekt-Routings robuster auch bei topic-basierten Ruecklaeufen.
- Objektkarten lesen Quelle weiterhin zuerst aus dem echten Eingang statt aus MQTT-Zielinfos.

## 33.4.22

- Objektkarten verwenden nach Browser-Reload jetzt zuerst den echten Eingangs-Cache bzw. die konfigurierte Eingangsseite und fallen nicht mehr auf MQTT-Zielinformationen zurueck.
- Die Objekt-API liefert dafuer `input_protocol`, `route_source`, `route_sources` und `route_targets` explizit mit.
- Die Objektliste behaelt beim Refresh ihre Scrollposition.

## 33.4.21

- Objektkarten und Live-API zeigen die echte Eingangsquelle jetzt auch nach einem Neustart aus dem konfigurierten Input statt aus Routing-Badges oder Zielprotokollen.
- Der Objekt-Live-Status traegt dazu live, source_protocol, last_source, input_protocol, route_sources und route_targets konsistent mit.
- Die Objektliste behaelt beim Refresh ihre Scrollposition besser bei.

## 33.4.20

- UDP-Eingaenge schreiben jetzt live_value, last_value, source_protocol, last_source und last_update direkt in den Objekt-Live-Cache, bevor die Weiterleitung startet.
- UDP Topic:Wert und UDP JSON zeigen damit in der Objektkarte wieder Wert und Quelle UDP, ohne dass die Weiterleitung die Quelle auf MQTT umbiegt.
- Versionsstand auf `33.4.20` gesetzt.

## 33.4.19

- Objektkarten und Live-Tab zeigen die Quelle jetzt strikt aus dem Live-Cache an und fallen nicht mehr auf Routing-Badges oder das erste Mapping zurueck.
- Wenn kein Livewert vorliegt, bleibt die Quelle bewusst `unbekannt`, statt implizit MQTT anzuzeigen.
- Versionsstand auf `33.4.19` gesetzt.

## 33.4.18

- UDP Topic:Wert wird im Live-Matcher nicht mehr wie JSON behandelt; JSON-Extraktion laeuft nur noch bei echtem JSON-Eingang und JSON-Objekt-Konfiguration.
- UDP-Objektanlage uebernimmt `source_json_path` nur noch fuer JSON-Objekte, damit Topic:Wert kein JSON-Path-Erbe mehr mitbringt.
- Versionsstand auf `33.4.18` gesetzt.

## 33.4.17

- UDP-Livewerte tragen jetzt ihre echte Eingangsquelle in der Live-Map mit, damit Objektkarten und Live-Tab nicht mehr aus Routing-Badges eine falsche Quelle ableiten.
- UDP Topic:Wert bleibt im Live-Match stabil und nutzt denselben Wertpfad fuer Anzeige und Weiterleitung.
- Versionsstand auf `33.4.17` gesetzt.

## 33.4.16

- UDP-JSON-Objekte verwenden jetzt den vollstaendigen JSON-Pfad als Live-Extraktionsquelle und geben den extrahierten Leaf-Wert an den Object-Router weiter.
- Der Router sendet bei UDP JSON nicht mehr den Platzhalter `JSON`, sondern den per JSON-Pfad gefundenen Wert; fehlende Pfade werden mit einer Warnung protokolliert.
- Versionsstand auf `33.4.16` gesetzt.

## 33.4.15

- UDP-Monitor-Eintraege werden im Normalizer wieder auf JSON-Text zurueckgesetzt, wenn `payload_raw` als `[object Object]` ankommt und JSON-Daten vorhanden sind.
- Der UDP-Explorer verwendet fuer Rohpayloads jetzt einen robusten Serializer mit JSON-Fallback, damit Rohpayload und Copy-Flow nicht mehr auf `[object Object]` fallen.
- Versionsstand auf `33.4.15` gesetzt.

## 33.4.14

- Der UDP-Explorer zeigt Rohpayloads jetzt konsistent als Text an, auch wenn der Monitor ein Objekt in `payload_raw` liefert.
- Die Detailansicht und der Copy-/Objekt-Flow verwenden dafuer dieselbe Payload-Textfunktion, damit nicht mehr `[object Object]` auftaucht.
- Versionsstand auf `33.4.14` gesetzt.

## 33.4.13

- Der UDP-Explorer behandelt `payload_raw` jetzt auch dann als JSON, wenn der Monitor bereits ein Objekt statt eines Rohstrings liefert.
- Die JSON-Key-Ansicht kann damit wieder direkt auf die vorhandene Struktur zugreifen, statt an `[object Object]` hängenzubleiben.
- Versionsstand auf `33.4.13` gesetzt.

## 33.4.12

- UDP-Monitor-Eintraege werden beim Normalisieren jetzt auch dann wieder als echter Rohtext behandelt, wenn `payload_raw` als Objekt statt als String ankommt.
- Damit kann der UDP Explorer JSON wieder als Text erkennen und die JSON-Keys korrekt anzeigen, statt nur `[object Object]` zu sehen.
- Versionsstand auf `33.4.12` gesetzt.

## 33.4.11

- Der UDP-Listener loggt jetzt direkt nach dem Empfang Rohbytes, Text-Repräsentation und geparste Details, damit JSON-Diagnosen bis zur Monitor-Kette sauber nachvollziehbar sind.
- Der UDP-Explorer zeigt zusaetzliche Payload-Debugfelder fuer Rohpayload, Repr, Laenge und erstes Zeichen, damit falsch dekodierte Eingaben sofort sichtbar werden.
- Versionsstand auf `33.4.11` gesetzt.

## 33.4.10

- JSON-UDP-Payloads gewinnen jetzt im Backend immer gegen vorherige `mode=Wert`-Zustaende, wenn `payload_raw` gueltiges JSON enthaelt.
- Der UDP-Listener loggt Rohtext und Details direkt nach dem Parsen, damit falsche Payload-Zustaende sofort sichtbar sind.
- Versionsstand auf `33.4.10` gesetzt.

## 33.4.9

- JSON-UDP-Payloads ohne Topic werden jetzt im Monitor stabil als JSON-Eintraege mit Leaf-Werten gefuehrt.
- `json_data` und `json_leaf_values` werden beim Normalisieren und Aggregieren zwangsweise aufgebaut, damit der UDP Explorer rechts die Keys anzeigen kann.
- Versionsstand auf `33.4.9` gesetzt.

## 33.4.6

- Die UDP-JSON-Erkennung ist jetzt toleranter und parst auch eingebettete oder anders formatierte JSON-Payloads wie im MQTT Explorer.
- Der UDP Explorer nutzt fuer JSON wieder den gemeinsamen Parse-Pfad fuer Rohpayload, `json_data` und daraus abgeleitete Leaf-Werte.
- Versionsstand auf `33.4.6` gesetzt.

## 33.4.5

- Der UDP Explorer orientiert sich jetzt noch enger am MQTT Discover Mode: links ein echter Baum, rechts die Topic-Detailansicht und der Expertenbereich bleibt eingeklappt.
- JSON-Keys und Verlauf sind in der rechten Detailansicht sichtbar, waehrend die linke Seite kompakt bleibt.
- Die Update-Logik bleibt stabil: bekannte UDP-Quellen werden nur aktualisiert, nicht neu angehaengt.

## 33.4.4

- Der UDP Explorer orientiert sich optisch und in der Bedienung enger am MQTT Discover Mode: Baum links, Detailansicht rechts, Expertenbereich einklappbar.
- Die linke Live-Liste bleibt kompakt und die Auswahl bleibt beim Update stabil.
- Empfangs- und Listen-Port-Details sind in den Expertenbereich gewandert, damit die Standardansicht ruhiger wirkt.

## 33.4.3

- Der UDP Explorer wurde optisch in eine kompakte Explorer-Ansicht umgebaut: links Live-Quellen, rechts Detailkarte mit Objektanlage.
- Die linke Liste bleibt klein und stabil, waehrend JSON-, Topic- und Wert-Details nur noch rechts im ausgewählten Eintrag angezeigt werden.
- Die UDP-Einstellungen sind nun nach unten verlagert und stören den Explorer nicht mehr im Hauptbereich.

## 33.4.2

- Der UDP Explorer arbeitet jetzt als Live-Explorer mit stabilen Quellen-Eintraegen statt als endlos wachsender Paket-Log.
- Wiederholte UDP-Pakete aktualisieren denselben Eintrag inklusive Zaehler, letzter Werte und JSON-Baum, sodass Auswahl und Scrollen erhalten bleiben.
- Die Explorer-Ansicht nutzt weiterhin denselben UDP-Listener wie der produktive Eingang und bleibt nur Beobachter.

## 33.4.1

- Der UDP-Bereich hat jetzt einen eigenen UDP Explorer in der Seitenleiste, der denselben Listener wie der produktive UDP-Eingang nutzt.
- Der UDP Explorer zeigt eingehende Pakete mit Filter, JSON-Ansicht und Objektanlage direkt aus RX-Daten an.
- UDP-Listener und Objektanlage bleiben an dieselbe Routing- und Runtime-Schiene angeschlossen, ohne einen zweiten Socket einzufuehren.

## 33.4.0

- UDP wird jetzt auch als Eingangsquelle sauber in die protokollneutrale Object-Routing-Schiene aufgenommen und kann JSON-Payloads mit Topic/Wert direkt zerlegen.
- Der UDP-Input loggt den geparsten Topic-/Wert-Satz jetzt vor dem Routing, damit Quellen- und Zuordnungsfehler schneller sichtbar werden.
- Der Objektmanager-Dialog "+ Neu" oeffnet jetzt ein leeres Formular mit Quellenwahl fuer LOXONE, MQTT, UDP und KNX; ausserdem gibt es einen neuen UDP-Monitor fuer eingehende Pakete.
- UDP-Objekte koennen im Objektmanager direkt als Quelle angelegt werden und der UDP-Input speichert RX-Metadaten fuer Monitor und Objekt-Match.

## 33.3.89

- Externe MQTT-Broker bekommen jetzt eine entlastete Queue-Verarbeitung mit Rate-Limit fuer Queue-voll-Meldungen, plus Diagnosewerte fuer Queue, Drops, Verarbeitung und Worker-Status.
- Der Gateway-Stop stoßt nun MQTT, UDP und KNX wirklich an, statt nur den UI-Status zu setzen; laufende Inputs werden nach Stop ignoriert.

## 33.3.88

- Externe MQTT-Broker laufen jetzt pro Broker mit eigenem Client, Queue-Worker und Auto-Reconnect mit Backoff weiter, statt nach einem Abbruch stehenzubleiben.
- Im MQTT-Hub zeigt die neue Statusuebersicht Verbunden/Getrennt, letzte Connect-/Disconnect-Zeit, Reconnect-Aktivitaet und Subscription-Zahl pro Broker an.

## 33.3.87

- Die Loxone-Zielroute wird im Objektmanager jetzt auch dann als aktiv ausgewertet, wenn die Loxone-Verbindung aus der lokalen Config direkt gelesen wird.
- Haupt-Routen und linke Infokachel zeigen Loxone-Ziele wieder sauber an, wenn Zielhaken, Ziel-UUID und Gateway-Konfiguration vorhanden sind.

## 33.3.84

- Im Loxone-Tab des Objektmanagers gibt es jetzt einen Haken fuer die Loxone-Zielroute; die Loxone-Quelle bleibt getrennt und MQTT/UDP/KNX -> Loxone nutzt das Ziel nur bei aktivem Zielhaken.
- Ein deaktiviertes Loxone-Ziel bleibt gespeichert, wird aber im Routing-Status als nicht konfiguriert angezeigt.

## 33.3.83

- Im Loxone-Tab des Objektmanagers gibt es jetzt eine Zielauswahl mit Suche und Filter fuer Name, Raum, Kategorie und Typ.
- Loxone-Quellfelder und Loxone-Zielfelder werden getrennt gespeichert; MQTT/UDP/KNX -> Loxone nutzt jetzt `target_uuid` statt der Quell-UUID.
- Die Routing-Ansicht zeigt Loxone-Ziele als Namen mit Raum und Kategorie, und der Objektmanager kann Loxone-Ziele aus der Explorer-Struktur uebernehmen.

## 33.3.82

- Der gemeinsame Object-Router ruft den bestehenden UDP-Sender wieder mit der korrekten Signatur auf.
- Die UDP-Ausgabe aus dem Objektmanager bleibt damit im neuen Routingpfad lauffaehig.

## 33.3.81

- Der gemeinsame Object-Router blockiert Legacy-Fallbacks nun nur noch, wenn wirklich mindestens ein Ziel erfolgreich gesendet hat.
- UDP-Ausgabe aus dem Objektmanager bleibt damit auch dann wieder lauffaehig, wenn ein Objekt-Match zwar erkannt, aber nicht komplett verarbeitet wurde.

## 33.3.80

- Objektmanager-Routing laeuft jetzt ueber eine gemeinsame Zielschleife fuer Loxone, MQTT, UDP, KNX und Influx.
- MQTT-, UDP- und KNX-Eingaenge nutzen denselben Objekt-Router, damit die Quelle nicht mehr in Zieladapter-States verrutscht.

## 33.3.79

- Der KNX-Monitor schreibt ausgehende Telegramme nicht mehr in den Live-Cache, damit die Quelle nicht auf KNX umspringt.
- Nur echte KNX-RX-Ereignisse aktualisieren weiterhin die Live-Quelle.

## 33.3.78

- Ein geloeschtes UDP Topic wird beim Speichern wieder auf `<Objektname>/value` zurueckgesetzt.
- Die Default-Logik fuer UDP liegt wieder zentral im object_service und greift bei Create und Update gleich.

## 33.3.77

- Neue UDP-Adapter bekommen beim ersten Speichern wieder das Default-Topic `<Objektname>/value`, wenn kein eigenes Topic gesetzt wurde.
- Bereits vorhandene UDP-Adapter behalten ein bewusst geleertes Topic beim Bearbeiten leer.

## 33.3.76

- Der UDP-Adapter wird beim Speichern nicht mehr automatisch wieder aktiviert, wenn Zielwerte gesetzt sind.
- Ein leer gespeichertes UDP Topic bleibt beim Bearbeiten jetzt leer statt erneut mit einem Default ueberschrieben zu werden.

## 33.3.75

- MQTT->UDP verwendet jetzt fuer normale MQTT-Objekte den frischen MQTT-Payload statt eines moeglich stale Live-Cache-Werts.
- MQTT-Objekte mit JSON-Key behalten weiterhin den extrahierten Wert aus dem Live-Match.

## 33.3.74

- Der MQTT->UDP-Aufruf nutzt jetzt wieder die Wrapper-Signatur korrekt; `add_log_entry` wird nicht mehr als `object_id` fehlinterpretiert.
- Dadurch verschwindet der Fehler `send_mqtt2udp() got multiple values for argument 'object_id'` beim objektbasierten UDP-Dispatch.

## 33.3.73

- Der MQTT->UDP-Objektrouter nutzt jetzt wieder die lokalen Core-Adapter-Pruefungen statt nicht vorhandener Helper im object_service.
- Dadurch bricht der MQTT-Callback nicht mehr intern ab, bevor der UDP-Sender erreicht wird.

## 33.3.72

- Der UDP-Adapter im Objektmanager wird beim Speichern mit echten Zielwerten jetzt automatisch aktiviert, damit konfigurierte Routen nicht still als inaktiv gespeichert bleiben.
- Damit reicht ein gespeicherter UDP-Tab mit Ziel-IP, Ziel-Port oder UDP-Topic aus, um den Router auf aktiv zu bringen.

## 33.3.71

- Die Objekt-Statuslogik orientiert sich jetzt an echten Quelle-Ziel-Paaren statt an der reinen Anzahl vollstaendiger Endpunkte.
- Dadurch wird ein Objekt nur dann als aktiv angesehen, wenn mindestens eine saubere Routing-Kombination vorhanden ist.

## 33.3.70

- Der MQTT-Routenloader fuer Objektmanager-Routing nutzt jetzt die lokale UDP-Pruefung und loggt, warum eine Route vor dem Versand verworfen wird.
- Damit wird sichtbar, ob MQTT->UDP an der Quelle, am Topic-Abgleich oder an fehlenden Zielparametern haengt.

## 33.3.69

- Der MQTT->UDP-Objektrouter loggt jetzt den Eintritt, die verfuegbaren Routen und die Abbruchgruende vor dem UDP-Sender, damit der fehlende Dispatch klar sichtbar wird.
- MQTT-Eingaenge werden fuer das Routing weiter akzeptiert; der neue Log zeigt, ob der Router die Route wirklich erreicht oder vorher gefiltert wird.

## 33.3.68

- MQTT als Eingangsquelle wird im Objektmanager jetzt nicht mehr fälschlich wie ein reiner Ausgang behandelt; MQTT-Objekte mit `in` oder `both` werden fuer den Eingangs-Dispatch akzeptiert.
- Die linke Objektkachel liest den aktuellen Livezustand nun zuerst aus dem Runtime-Cache, damit die Herkunft nicht durch alte Monitorwerte ueberschrieben wird.
- MQTT->UDP bekommt zusaetzliche Diagnose-Logs mit vorbereiteten Zielparametern, damit fehlende UDP-Sends schneller sichtbar sind.

## 33.3.67

- MQTT→UDP im Objektmanager schickt jetzt direkt ueber den bestehenden UDP-Sendepfad wie Loxone→UDP und nutzt den aus dem JSON-Key extrahierten Wert.
- Der MQTT-UDP-Zweig loggt jetzt deutlicher, wenn Zielhost oder Port fehlen, damit aktive Routen klarer von inaktiven getrennt werden.
- Versionsstand auf `33.3.67` gesetzt.

## 33.3.66

- MQTT->UDP nutzt jetzt beim Objektmanager denselben bestehenden UDP-Ausgang wie Loxone->UDP und sendet den aus dem JSON-Key extrahierten Objektwert.
- MQTT-UDP-Dispatch loggt jetzt klar MQTT-Eingang, objektbasierten UDP-Dispatch und den eigentlichen UDP-Sendepfad.
- Versionsstand auf `33.3.66` gesetzt.

## 33.3.65

- MQTT→UDP im Objektmanager loggt jetzt MQTT-Eingang, objektbasierten UDP-Dispatch sowie UDP-Start/OK/Fehler klarer nach.
- UDP-Routen erscheinen nur noch als aktiv, wenn Zielhost und Port wirklich gesetzt sind; MQTT JSON-Key-Objekte gehen sauber in den objektbasierten Sendepfad.
- Versionsstand auf `33.3.65` gesetzt.

## 33.3.64

- Der MQTT-Hub kann JSON-Key-Zeilen jetzt direkt in den Objektmanager schicken; `+ Objekt` pro Key uebergibt Topic, JSON-Key, erkannte Daten und den MQTT-Quellkontext.
- MQTT-Objekte mit JSON-Key speichern den Key im MQTT-Adapter und werden im Live-Match sowie in der Routenanzeige als Topic plus JSON-Key gefuehrt.
- Versionsstand auf `33.3.64` gesetzt.

## 33.3.63

- Der KNX-Testcenter-Fehler `name 'datetime' is not defined` ist beseitigt und der Zeitstempel faellt bei Problemen sauber auf `-` zurueck.
- Die KNX-Testcenter-Buttons sind jetzt getrennt verdrahtet: Senden, Wiederholen und Monitor leeren loesen keine versehentlichen Submit-Aktionen mehr aus.
- Nach `Monitor leeren` erscheint im Diagnosefeld jetzt klar `Status: Monitor geleert`.
- Versionsstand auf `33.3.63` gesetzt.

## 33.3.62

- Der KNX-Testcenter-Backendpfad ist jetzt komplett per try/except abgesichert und liefert bei Fehlern immer JSON statt HTML-500.
- `Auto` wird im KNX-Testcenter vor dem Senden auf einen konkreten DPT aufgeloest; die JSON-Diagnose fuehrt `in_monitor` sauber mit.
- Versionsstand auf `33.3.62` gesetzt.

## 33.3.61

- Der KNX-Testcenter-Submit laeuft jetzt per JSON-Fetch statt als HTML-Redirect und zeigt Fehler direkt in der Diagnose an.
- Der KNX-Hub ordnet zuerst Uebersicht und Kacheln an, danach erst KNX Testcenter und Diagnose.
- Das Testcenter behandelt `Auto` intern als konkreten DPT und nutzt weiterhin denselben KNX-Sendepfad wie der Objektmanager.
- Versionsstand auf `33.3.61` gesetzt.

## 33.3.60

- Der KNX-Hub zeigt jetzt einen eigenen KNX-Testbereich mit Gruppenadresse, DPT, Wert, Wiederholen und Monitor-Leeren.
- Der KNX-Testbereich nutzt exakt denselben Sendepfad wie der Objektmanager und schreibt eine kopierbare Diagnose mit APDU und Status.
- Neue Test-POST-Routen speichern den letzten Versuch in der Runtime, damit `Letzten Test wiederholen` ohne erneutes Ausfüllen funktioniert.
- Versionsstand auf `33.3.60` gesetzt.

## 33.3.59

- Der KNX-Monitor trennt RX und OUT jetzt klar: externe Telegramme erscheinen als `RX`, eigene Gateway-Sends als `OUT` mit Status `OK`, `PENDING` oder `ERROR`.
- Der KNX-Filter im Monitor wurde auf `RX`/`OUT` umgestellt, damit eigene Sendungen nicht mehr als RX-Echo einsortiert werden.
- Die KNX-DPT-Auswahl bleibt konkret und zeigt keine generische `DPT 9.xxx`-Sammeloption.
- Versionsstand auf `33.3.59` gesetzt.

## 33.3.58

- Der KNX-Sendepfad sendet jetzt explizit `GroupValueWrite`-Telegramme mit kodiertem APDU-Payload statt eines indirekten Device-Writes.
- Der KNX-Sender loggt jetzt GA, DPT, Wert und die kodierte APDU vor dem Queueing sowie den erfolgreichen Queue-/Join-Durchlauf.
- Der KNX-Monitor bekommt ausgehende Telegramme erst nach erfolgreichem Write als `OUT_OK`; der Payload-Fall `DPT 9.001` ist als Test- und Fallbackpfad weiter vorbereitet.
- Versionsstand auf `33.3.58` gesetzt.

## 33.3.57

- Der KNX-Sendepfad loggt jetzt vor und nach dem echten xknx-Write sowie bei Fehlern den konkreten Exception-Typ.
- Der KNX-Monitor trennt ausgehende Eintraege nun sichtbar in `OUT_PENDING`, `OUT_OK` und `OUT_ERROR`; der Status wird erst nach erfolgreichem Sendebefehl gesetzt.
- Der KNX-Tab weist zusaetzlich auf DPT 9.xxx als Alternative hin, wenn Ziele 14.xxx nicht erwarten.
- Versionsstand auf `33.3.57` gesetzt.

## 33.3.56

- Der KNX-Sendepfad importiert jetzt garantiert `app.core` statt des Top-Level-Moduls `core`.
- Der KNX-Listener und der KNX-Sender loggen jetzt denselben Runtime-Identitaetskontext, damit Doppel-Imports sichtbar werden.
- Das App-Paket fuegt sein Verzeichnis nicht mehr als Top-Level-Suchpfad hinzu, damit `app.core` nicht versehentlich als `core` geladen wird.
- Versionsstand auf `33.3.56` gesetzt.

## 33.3.54

- Der KNX-Ausgang schreibt jetzt echte Telegramme fuer aktive Objektmanager-Routen mit passender Gruppenadresse und DPT.
- Der KNX-Monitor markiert ausgehende Objektmanager-Telegramme als `WRITE`, damit Senden und Empfang klar unterscheidbar bleiben.
- Der KNX-Tab bietet jetzt eine DPT-Auswahlliste und speichert den gewaehlten DPT pro Objekt.
- Versionsstand auf `33.3.54` gesetzt.

## 33.3.53

- KNX ist im Objektmanager jetzt als weiterer Ausgang fuer Loxone, MQTT und UDP verdrahtet.
- Die Routing-Vorschau und der Runtime-Dispatch erzeugen nun auch LOXONE -> KNX und MQTT -> KNX bzw. UDP -> KNX, wenn die KNX-Konfiguration vorhanden ist.
- Versionsstand auf `33.3.53` gesetzt.

## 33.3.52

- Im Objektmanager zeigen Detailkopf und Objektkarte links jetzt nur noch ein Status-Badge pro Objekt.
- Das doppelte Routing-Status-Badge wurde aus der Objektansicht entfernt.
- Routing-Statusspalten in den Tabellen bleiben unveraendert erhalten.
- Versionsstand auf `33.3.52` gesetzt.

## 33.3.51

- Der Routing-Tab zeigt jetzt getrennte Haupt-Routen und direkte Rueck-Routen.
- Haupt-Routen folgen der aktiven Objekt-Quelle, Rueck-Routen zeigen nur direkt konfigurierte Rueckwege zur aktuellen Quelle.
- Influx bleibt nur Ziel, nicht Rueck-Quelle.
- Versionsstand auf `33.3.51` gesetzt.

## 33.3.50

- Der Routing-Tab baut seine Eintraege jetzt aus der Objektkonfiguration mit allen aktivierten Quellen und Zielen auf und zeigt keine Selbst- oder Legacy-Routen mehr an.
- Influx-Adressen im Routing-Tab zeigen jetzt `Measurement / Field / Topic`.
- Versionsstand auf `33.3.50` gesetzt.

## 33.3.49

- Die Livewert-Quelle im Objektmanager bleibt jetzt die echte Eingangsquelle, z. B. `loxone`, auch wenn der Wert nach MQTT, UDP oder Influx weitergeleitet wird.
- Geroutete Zieladapter werden separat als `last_target_adapter(s)` im Runtime-Live-Cache erfasst.
- MQTT-Echos eigener Objektmanager-Publishes ueberschreiben frische Loxone-Livewerte nicht mehr als Quelle `mqtt`.
- Livewert-Logging enthaelt `object_id`, `incoming_source`, `stored_source`, `target_adapter`, Wert und `ignored_echo`.
- Versionsstand auf `33.3.49` gesetzt.

## 33.3.48

- Der Objektmanager-Influx-Adapter speichert jetzt Measurement, Field und Topic pro Objekt.
- Leere Influx-Felder werden beim Speichern auf Defaults gesetzt: Measurement aus bereinigtem Objektname, Field `value`, Topic `<object.name>/value`.
- Influx schreibt das konfigurierte Topic als Tag `topic`; optionale Tags `object_id`, `source`, `unit` bleiben erhalten.
- Influx-Routing loggt jetzt `object_id`, Wert, Measurement, Field, Topic, Bucket und Ergebnis.
- Versionsstand auf `33.3.48` gesetzt.

## 33.3.47

- Influx kann im Objektmanager als Zieladapter aktiviert werden, ohne Legacy-Topic-Mappings zu erzeugen.
- Loxone-Livewerte werden bei aktivem Influx-Ziel direkt nach Influx geschrieben; Measurement, Field, Bucket und optionale Tags kommen aus dem Objektadapter.
- Influx-Werte werden numerisch geschrieben, wenn moeglich; Bool-Werte werden als 0/1 geschrieben, Text nur bei Datentyp `text`/`string`.
- Influx-Routing loggt `object_id`, Wert, Measurement, Field, Bucket und Ergebnis.
- Versionsstand auf `33.3.47` gesetzt.

## 33.3.46

- Neue Objekte erhalten beim Anlegen automatisch ein passives UDP Default Topic nach dem Muster `<Objektname>/value`.
- Leere UDP-Topic-Felder werden beim Speichern wieder auf `<Objektname>/value` gesetzt, statt dauerhaft leer gespeichert zu werden.
- Der UDP Payload-Modus steuert den Versand: `topic_value` sendet `<udp_topic>:<value>`, `value_only` sendet nur `<value>` und `json` sendet Topic plus Wert als JSON.
- Versionsstand auf `33.3.46` gesetzt.

## 33.3.45

- UDP Custom Topics im Objektmanager koennen vom alten Legacy-`format`-Fallback getrennt gespeichert werden.
- Das UDP-Adapterformular schreibt keinen alten `format`-Wert mehr als Hidden-Fallback zurueck.
- Legacy-`format`-Werte werden nur noch beim Laden alter Objekte einmalig als `udp_topic` interpretiert, nicht beim Speichern leerer Felder wiederhergestellt.
- Der Adapter-Merge im `object_service` verwirft leere Strings nicht mehr, damit der UDP-Speicherpfad leere Formularwerte erkennen und ab 33.3.46 wieder auf den Default setzen kann.
- Versionsstand auf `33.3.45` gesetzt.

## 33.3.44

- Der Objektmanager-UDP-Adapter speichert jetzt ein eigenes `udp_topic` und einen `payload_mode` direkt am Objekt.
- Loxone->UDP nutzt beim Senden das konfigurierte Objektmanager-UDP-Topic; ohne Topic wird nur der Wert gesendet.
- UDP-Zielrouten benoetigen nur noch Ziel-IP und Ziel-Port; der Textpraefix ist optional.
- Das UDP-Adapterformular zeigt das Feld `UDP Topic` mit Hilfetext und Payload-Modus.
- Versionsstand auf `33.3.44` gesetzt.

## 33.3.43

- Objektmanager-Routen werden nicht mehr in die Legacy-Loader fuer `MQTT -> Loxone`, `MQTT -> UDP` und `UDP -> MQTT` gemischt.
- Legacy-Seiten, Dashboard-Kacheln, globale Suche und Konfliktpruefung zaehlen/zeigen fuer diese Bereiche nur noch echte Legacy-Mapping-Dateien.
- MQTT-Publishes aus dem Objektmanager-Routing werden mit Runtime-Origin (`object_id`, `original_source`, `target_adapter`) markiert und im MQTT-Eingang als Echo uebersprungen.
- Loxone-Livewerte behalten dadurch im Objektmanager ihre Quelle `loxone`, auch wenn daraus MQTT- oder UDP-Zielsendungen entstehen.
- Versionsstand auf `33.3.43` gesetzt.

## 33.3.42

- Loxone->UDP sendet den Wert jetzt nur noch einmal pro Zielpaket; die MQTT-Loopback-Sperre greift jetzt auch fuer MQTT->UDP-Weiterleitungen aus dem Loxone-Publishpfad.
- UDP-Payloads senden ohne Topic jetzt nur noch den nackten Wert statt ein leeres Prefix.
- Das UDP-Logging schreibt pro Paket eine detaillierte INFO-Zeile mit `object_id`, `source`, `value`, `udp_target`, `payload`, `target_host` und `target_port`.
- Im MQTT->UDP-Mapping wurde das UI-Label von `Format` auf `UDP-Topic` umbenannt.
- Versionsstand auf `33.3.42` gesetzt.

## 33.3.41

- Loxone->UDP sendet pro Wert nur noch einmal pro Zielroute; MQTT-Loopbacks aus dem Loxone-Publishpfad werden kurzzeitig erkannt und als Duplikat uebersprungen.
- UDP-Logging erfasst jetzt `object_id`, `value`, `udp_target`, `used_format` und `skipped_duplicate`.
- Versionsstand auf `33.3.41` gesetzt.

## 33.3.40

- Loxone-Livewerte werden jetzt nach der Objektzuordnung auch an aktive Zieladapter weitergereicht.
- Prioritaet ist dabei MQTT vor UDP; KNX wird nur als vorbereitete Route erkannt und noch nicht gesendet.
- Der Loxone-Publishpfad loggt jetzt `object_id`, `value`, `target` und `result` fuer erfolgreiche oder uebersprungene Zielsendungen.
- Versionsstand auf `33.3.40` gesetzt.

## 33.3.39

- Der temporäre Single-Object-Fallback fuer Loxone-Livewerte wurde entfernt.
- `record_live_value()` loggt fehlende Loxone-Zuordnungen nun auf INFO/WARNING statt stiller Fallback-Zuordnung.
- Versionsstand auf `33.3.39` gesetzt.

## 33.3.38

- `/api/objects/live` zieht nun Loxone-Livewerte aus `core.display_values` und `core.last_values` nach und synchronisiert sie wieder in den Objekt-Live-Cache.
- Der Sync berücksichtigt bei Loxone zusätzlich `custom_name` aus der Topic-Config, damit echte Livewerte nicht mehr als `value:null` im Objektmanager landen.
- Versionsstand auf `33.3.38` gesetzt.

## 33.3.37

- Loxone-Livewerte matchen jetzt auch auf `object.name`, `loxone.name` und die Alias-Felder `io`, `io_address`, `loxone_io`, `uuid` und `loxone_uuid`.
- Wenn kein Treffer gefunden wird, loggt `record_live_value()` nun eine Debug-Sicht mit den relevanten Objektfeldern.
- Bei genau einem Objekt kann ein Loxone-Livewert als temporärer Fallback auf dieses Objekt gelegt werden.
- Versionsstand auf `33.3.37` gesetzt.

## 33.3.36

- Loxone-Livewerte matchen jetzt robuster ueber UUID, IO-Adresse und Objektname und loggen Debug-Hinweise, wenn kein Treffer gefunden wird.
- Der Live-Endpoint-Index wird nach Objekt-CRUD direkt neu aufgebaut, damit frische Objekte sofort fuer Live-Zuordnungen verfuegbar sind.
- Versionsstand auf `33.3.36` gesetzt.

## 33.3.35

- Objektmanager zeigt Live-Werte jetzt mit erkannter Quelle und erkanntem Endpunkt in Karten und Live-Tab an.
- Live-Wert-Zuordnung nutzt den vorbereiteten In-Memory-Index fuer Loxone UUID/IO-Adresse und MQTT Topic, ohne `objects.json` pro Wert zu scannen.
- `GET /api/objects/live` und `GET /api/objects/<id>/live` liefern jetzt auch `source_address` und `recognized_endpoint`.
- Versionsstand auf `33.3.35` gesetzt.

## 33.3.34

- object_service nutzt jetzt keine Lock-Inversion mehr: Datei- und Cache-Zugriffe sind entkoppelt, CRUD ruft nicht mehr unter `OBJECTS_FILE_LOCK` wieder `list_objects()` auf.
- Live-Wert-Erfassung arbeitet jetzt mit einem vorbereiteten In-Memory-Endpoint-Index statt pro Wert die komplette Objektliste zu scannen.
- Objekt-Cache, Endpoint-Index und Route-Cache werden gemeinsam invalidiert, damit Bridge-Callbacks und CRUD sich nicht gegenseitig blockieren.
- Versionsstand auf `33.3.34` gesetzt.

## 33.3.32

- Delete entkoppelt jetzt den Reload noch deutlicher: `objects.json` wird geschrieben, Cache invalidiert und der Route-Reload nur asynchron angestossen.
- Delete-Requests loggen `delete_start`, `write_objects_done`, `cache_invalidated`, `reload_requested` und `delete_response_sent`.
- `reload_object_routes()` loggt nun Start, Dauer und Fehler separat, damit Reload-Blockaden schneller sichtbar werden.
- Versionsstand auf `33.3.32` gesetzt.

## 33.3.31

- Objekt-Routen werden jetzt ueber einen In-Memory-Cache erzeugt und nicht bei jedem Zugriff neu aus `config/objects.json` berechnet.
- CRUD-Reloads laufen asynchron, damit der Flask-Thread nicht auf Route-Neuberechnung warten muss.
- Loxone->MQTT-Routencheck bleibt cachebasiert, Skip-Logs bleiben debug-only und das UI-Log wird nicht mehr mit Skip-Meldungen geflutet.
- Versionsstand auf `33.3.31` gesetzt.

## 33.3.30

- Loxone->MQTT Skip-Meldungen laufen nicht mehr ueber das normale Live-Log; im Debug-Fall werden sie pro UUID nur noch rate-limited geloggt.
- Die Loxone->MQTT-Routensuche nutzt jetzt einen In-Memory-Index statt pro Wert die komplette Objektliste zu durchsuchen.
- `config/objects.json`-Lesen fuer den Routing-Check wird damit aus dem Loxone-Hot-Path entfernt; Live-Werte werden weiter aktualisiert.
- Versionsstand auf `33.3.30` gesetzt.

## 33.3.29

- `config/objects.json` wird beim Objekt-CRUD jetzt ueber einen zentralen Schreiblock und eindeutige Temp-Dateien geschrieben.
- Atomisches Schreiben versucht `os.replace()` mehrfach erneut, damit Windows-Dateisperren nicht sofort zu einem 500 fuehren.
- API-Routen geben bei gesperrter Objektdatei einen sauberen `423`-Hinweis statt eines generischen Serverfehlers zurueck.
- Versionsstand auf `33.3.29` gesetzt.

## 33.3.27

- CRUD-State im Objektmanager weiter abgesichert: Objekt-Runtime-State wird nach Create/Update/Delete komplett verworfen, damit geladene Live-/Cache-Reste keinen Folge-CRUD blockieren.
- Loxone-Create loggt jetzt vor dem Fehlerpfad zusaetzlich `request.args`, `request.form`, JSON-Payload und die konkrete Ursache im exakten Debug-Format.
- Create/Import-Logging erfasst den Request-Snapshot mit Form- und JSON-Daten sowie den aktuellen Objektbestand vor dem Duplicate-Check.
- Versionsstand auf `33.3.27` gesetzt.

## 33.3.26

- Jinja2-kompatible JavaScript-Strings im Objektmanager auf `tojson` umgestellt.
- `e('js')` im Objektmanager-Template entfernt, damit der Seite kein Template-500 mehr erzeugt.
- Versionsstand auf `33.3.26` gesetzt.

## 33.3.24

- Objekt-CRUD loest keinen Bridge-Neustart mehr aus.
- `reload_object_routes()` berechnet die Objekt-Routen neu, laesst die laufende Bridge aber aktiv.
- Flask wird beim Direktstart explizit ohne Reloader gestartet, damit `objects.json` keine Dev-Restarts triggert.
- Delete setzt die Objektansicht nach dem Loeschen auf keine Auswahl mehr und loggt IDs vor/nach dem Vorgang.
- Versionsstand auf `33.3.24` gesetzt.

## 33.3.25

- Objektwahl im Objektmanager laedt den rechten Bereich jetzt per API/Fragment statt per Full-Page-Navigation.
- Delete verwendet die vorher gemerkte `selectedObjectId`, loescht idempotent und setzt danach die Auswahl sauber auf leer.
- Objektliste wird nach Delete per API neu aufgebaut, ohne den kompletten Content-Bereich neu zu laden.
- Versionsstand auf `33.3.25` gesetzt.

## 33.3.21

- Objekt-Loeschen nach interner UUID-Umstellung repariert.
- Delete-Button uebergibt die interne MP-Gateway Objekt-UUID aus `object.uuid`/`object.id`.
- `delete_object()` entfernt Objekte nur noch anhand der gespeicherten `id` in `config/objects.json`; Name, Key, Slug und Legacy-IDs werden nicht mehr als Delete-Identitaet verwendet.
- Delete-Route loggt `DELETE REQUEST uuid=... object found=... deleted=...`.
- Nach Delete wird ohne 500 auf `/objects_v33` redirectet und die Objektliste neu geladen.
- Versionsstand auf `33.3.21` gesetzt.

## 33.3.20

- Loxone-Explorer-Objektanlage stabilisiert.
- Fehlermeldung `Objekt konnte nicht erstellt werden...` wird jetzt mit Request-Daten, ausgewaehlter UUID, Name, IO-Adresse, Explorer/Source und konkretem `reason` geloggt.
- Loxone-Create prueft nur die erforderliche Loxone-UUID als Mindestfeld; Name, IO-Adresse, Control-Type, Raum und Einheit bleiben tolerant optional.
- Route-Reload-Fehler nach erfolgreichem Speichern erzeugen keinen Create-Abbruch mehr, sondern werden nur geloggt.
- Erfolgreiche Anlage redirectet weiter auf `/objects_v33?selected=<object_id>&tab=loxone`.
- Versionsstand auf `33.3.20` gesetzt.

## 33.3.19

- Objektmanager um neuen Tab `Live` erweitert.
- Live-Werte werden runtime-only im Prozesscache gefuehrt und nicht in `config/objects.json` gespeichert.
- Objektliste zeigt pro Objekt aktuellen Wert und Quelle, aktualisiert per `/api/objects/live` ohne Seiten-Reload.
- Neue Live-APIs ergaenzt: `GET /api/objects/live` und `GET /api/objects/<id>/live`.
- Runtime-Ereignisse aus Loxone, MQTT, KNX und UDP koennen Live-Werte anhand der Objekt-Endpunkte zuordnen.
- Versionsstand auf `33.3.19` gesetzt.

## 33.3.18

- Interne MP-Gateway Objekt-UUIDs auf echte stabile `obj_<uuid4hex>`-IDs umgestellt.
- Neue Objekte leiten ihre Objekt-UUID nicht mehr aus Name, Key, Topic, Loxone-UUID oder anderen Adapterdaten ab.
- Bestehende Slug-IDs in `config/objects.json` werden beim Laden einmalig migriert und als interne `legacy_ids` fuer alte Links/Referenzen erhalten.
- Objektmanager-Kopf zeigt die Identitaet als `MP-Gateway Objekt-UUID`; Loxone-UUID bleibt ausschliesslich im Loxone-Tab.
- Objekt-Update und -Delete akzeptieren weiterhin alte Slug-Referenzen, speichern aber nur die stabile interne Objekt-ID.
- Versionsstand auf `33.3.18` gesetzt.

## 33.3.17

- Loxone-Explorer-JavaScript-Escape in `tm2CssEscape()` repariert.
- Fragiles Regex-Literal im Python-gerenderten Script durch robuste `replaceAll`-Fallback-Variante ersetzt.
- `/topics2` rendert wieder gueltiges JavaScript, damit `tm2Reload(false)` ausgefuehrt werden kann.
- Keine Backend- oder Importlogik geaendert.
- Versionsstand auf `33.3.17` gesetzt.

## 33.3.16

- Loxone-Explorer-Create nutzt beim Klick einen frischen Snapshot aus `tm2Topics` statt eine moeglicherweise veraltete `tm2Selected`-Objektreferenz.
- Debug-Log vor `create_from_explorer` um `selectedRow`, `selectedUuid`, `selectedObject`, Ziel-URL und Request-Parameter erweitert.
- Tree-Zeilen tragen `data-topic`, damit die aktuell markierte Row vor dem Create eindeutig geloggt werden kann.
- Create-Button-State wird bei Browser-Page-Restore zurueckgesetzt, damit keine alte In-Progress-/Button-Referenz erhalten bleibt.
- Keine Backend-Aenderung am Import.
- Versionsstand auf `33.3.16` gesetzt.

## 33.3.15

- Direkt vor der Create-Fehlermeldung explizite Error-Logs ergaenzt: `CREATE OBJECT FAILED`, `request.args`, `request.form`, JSON-Payload und `reason`.
- Keine Aenderung an Create-Logik, Importlogik, Redirects oder Bedingungen.
- Versionsstand auf `33.3.15` gesetzt.

## 33.3.14

- Debug-Logging fuer Loxone-Explorer-Create ergaenzt, ohne Backend-Importlogik zu aendern.
- Frontend loggt vor der Navigation Embedded-Status, aktuelle URL, ausgewaehlte UUID, Name, Topic/IO, Objekt und Ziel-URL.
- `/objects_v33/create_from_explorer` loggt Request-URL, Referrer, Query-Args, ausgewaehlte Werte, erzeugtes Payload und Notice-Ursprung.
- Die Meldung `Objekt konnte nicht erstellt werden. Bitte Auswahl pruefen und erneut versuchen.` wird mit Generator-Funktion und Datei/Zeile geloggt.
- Versionsstand auf `33.3.14` gesetzt.

## 33.3.13

- Legacy-Auto-Publish von Loxone-State-Updates nach MQTT gestoppt.
- `publish_value()` aktualisiert weiterhin Anzeige-/Explorer-Werte, publisht aber nur noch bei aktiver Objektmanager-Route `Loxone -> MQTT`.
- Objekt-Routengenerator um aktive `loxone2mqtt`-Routen aus vollständigen Loxone- und MQTT-Endpunkten erweitert.
- Runtime-Gate prueft aktives Objekt, aktivierte Loxone-/MQTT-Adapter, vollstaendige Endpunkte und passende Loxone-UUID/IO-Adresse.
- Loxone-Erfassung bleibt aktiv; ungefragtes MQTT-Publishing ohne Objekt-Route wird uebersprungen und gedrosselt geloggt.
- Versionsstand auf `33.3.13` gesetzt.

## 33.3.12

- Eingebetteten Loxone-Explorer-Create an den separaten Fenster-Flow angeglichen.
- `tm2CreateObjectSelected()` ruft `/objects_v33/create_from_explorer` nun auch im IFrame per direktem `window.location.href` auf.
- Die Loxone-Create-Sondernavigation ueber `postMessage` und Shell-Frame-Rewrite wird fuer diesen Button nicht mehr verwendet.
- Backend-Importlogik bleibt unveraendert.
- Versionsstand auf `33.3.12` gesetzt.

## 33.3.11

- Objektmanager-V33-Loeschen robust gemacht: Delete akzeptiert `id`, `uuid` oder `key` und bleibt bei fehlendem oder bereits geloeschtem Objekt ohne 500.
- Delete-Route faengt Such-, Schreib- und Route-Reload-Fehler ab, loggt sie und leitet immer sauber auf `/objects_v33` ohne `selected` zurueck.
- Objektliste wird nach dem Loeschen neu geladen; ein geloeschtes Objekt wird rechts nicht mehr als Auswahl uebergeben.
- Loesch-Button postet nur bei vorhandener Objekt-ID, deaktiviert sich beim ersten Submit und ignoriert Mehrfachklicks.
- Delete-Logging fuer `object_id`, `found`, `deleted`, `redirect` und `error` ergaenzt.
- Versionsstand auf `33.3.11` gesetzt.

## 33.3.10

- Loxone-Explorer-Button gegen Mehrfachklick gesichert; nach dem ersten Klick wird er deaktiviert und zeigt `Erstelle...`.
- `/objects_v33/create_from_explorer` fuer Loxone idempotent gemacht: gleiche Loxone-UUID oeffnet das vorhandene Objekt statt ein zweites zu erstellen.
- Explorer-Create-Fehler werden abgefangen, geloggt und per Objektmanager-Redirect mit Hinweis behandelt statt als Internal Server Error zu enden.
- Erfolgreiche Loxone-Explorer-Creates leiten stabil auf `/objects_v33?selected=<object_id>&tab=loxone` weiter.
- Import-Logging fuer `source`, `uuid`, `name`, `object_id` und `action=created/existing/error` ergaenzt.
- Versionsstand auf `33.3.10` gesetzt.

## 33.3.9

- Eingebettete Explorer-Objektanlage ueber eine `postMessage`-Bruecke zur Shell gefuehrt.
- Die Shell setzt bei Explorer-Create den `contentFrame` gezielt auf den Objektmanager V33 und markiert den Sidebar-Link.
- Cache-Busting fuer eingebettete Objektmanager-Navigation ergaenzt und nach dem Create-Redirect beibehalten.
- Direkte Explorer-Fenster behalten den bestehenden Redirect unveraendert bei.
- Versionsstand auf `33.3.9` gesetzt.

## 33.3.8

- Sidebar-Versionsanzeige dynamisiert: `app_version` wird beim Rendern aus der zentralen `VERSION`-Datei gelesen.
- App-Context-Processor stellt `app_name`, `app_subtitle`, `app_legacy_name` und die aktuelle `app_version` fuer Templates bereit.
- Versionsstand auf `33.3.8` gesetzt.

## 33.3.7

- `APP_VERSION` wird aus der zentralen `VERSION`-Datei gelesen; hart codierte alte Versionswerte in `app/engine/port.py` entfallen.
- Alter toter JavaScript-Renderer in `templates/objects_v33/list.html` entfernt, damit nur noch die serverseitige Objektmanager-V33-Pipeline aktiv ist.
- `/objects_v33/new` oeffnet fuer manuelle Neuanlage kein ungespeichertes Detailobjekt mehr; Explorer-Parameter werden weiterhin nach `/objects_v33/create_from_explorer` umgeleitet.
- Object Service erkennt alle kanonischen top-level Protokollbloecke beim Speichern und normalisiert sie in das zentrale Objektmodell.
- `object_registry.py` und `data/objects_v33.json` als deprecated markiert; produktive V33-Objekte bleiben in `config/objects.json`.
- Versionsstand auf `33.3.7` gesetzt.

## 33.3.6

- Objekt-Speicherform fuer V33 final auf Stammdaten plus top-level Protokollbloecke konsolidiert, z.B. `object.loxone`.
- Neue Loxone-Explorer-Objekte schreiben Loxone-Daten direkt nach `loxone` statt in eine zusaetzliche `adapters`-Speicherstruktur.
- Alte `adapters`-Eintraege bleiben lesbar und werden beim Speichern in die kanonische Protokollblock-Form migriert.
- Adapter-Speichern schreibt den bearbeiteten Protokollblock direkt auf `object.<protocol>`.
- Versionsstand auf `33.3.6` gesetzt.

## 33.3.5

- Objektmodell fuer Objektmanager V33 konsolidiert: neue Objekte schreiben Protokolldaten nur noch kanonisch in Protokollbloecke.
- Legacy-Felder wie `source_type`, `source_address`, `target_type`, `loxone_topic`, `mqtt_topic`, `knx_ga`, `udp_topic` und top-level `loxone` werden beim Lesen migriert, aber nicht mehr neu in `config/objects.json` geschrieben.
- Loxone-Explorer-Create speichert den Loxone-Endpunkt als Loxone-Protokollblock mit `enabled`, `direction`, `datatype`, `uuid`, `io_address`, `control_type`, `visu_name`, `room` und `unit`.
- Objektliste und Detailansicht laden nach Explorer-Create aus derselben gespeicherten Service-Quelle; der clientseitige `/api/objects`-Listenersatz wurde entfernt.
- Adapter werden intern weiter als Liste nutzbar gemacht, aber in `objects.json` nicht als zweite Struktur gespeichert.
- Versionsstand auf `33.3.5` gesetzt.

## 33.3.4

- Loxone-Explorer-Create nachgezogen: Loxone-Adapter wird mit Aktiv, Richtung, Datentyp, UUID, IO-Adresse, Control-Typ, Visu-Name, Raum und Einheit befuellt.
- Key-Erzeugung fuer neue Explorer-Objekte nutzt Klarnamen mit Unterstrichen, z.B. `gesamtleistungw_value`, und uebernimmt keine UUID als Allgemein-Key.
- Loxone-Create akzeptiert zusaetzliche Parameter-Aliase fuer UUID, IO-Adresse, Name/Pfad, Control-Type, Visu-Name, Raum und Einheit.
- Explorer-JavaScript uebergibt die Datenpunkt-UUID bevorzugt als Loxone-UUID und den letzten Wert zur Datentyp-Erkennung.
- Nach Explorer-Create bleibt die Weiterleitung auf das neu erstellte Objekt mit aktivem Loxone-Tab erhalten.
- Versionsstand auf `33.3.4` gesetzt.

## 33.3.3

- Loxone-Explorer-Objektanlage robust nachgezogen.
- Loxone-Endpunkt wird beim Explorer-Create immer als aktivierter `loxone`-Adapter gespeichert.
- Alte `/objects_v33/new`-Vorbelegungen mit Loxone-Parametern fuellen nun ebenfalls den Loxone-Tab statt Allgemein-Quelle/Ziel.
- Leere Legacy-Quelle erzeugt keinen aktivierten MQTT-Fallback-Adapter mehr.
- Loxone Explorer uebergibt bevorzugt die Control-UUID als UUID und den State-/IO-Pfad als IO-Adresse.
- Status bleibt bei nur einem vollstaendigen Loxone-Endpunkt `unvollstaendig`; Routing wird erst mit zweitem vollstaendigem Endpunkt aktiv.
- Versionsstand auf `33.3.3` gesetzt.

## 33.3.2

- Loxone Explorer kann Objekte direkt im Objektmanager V33 erstellen.
- Explorer-Create speichert ausschliesslich Klardaten im Allgemein-Bereich: Name, Key, Datentyp, Kategorie, Raum, Einheit, Beschreibung und Aktiv.
- Technische Loxone-Daten werden nur im Loxone-Adapter gespeichert: UUID, IO-Adresse, Control-Typ, Visu-Name, Raum und Einheit.
- Nach dem Erstellen oeffnet der Objektmanager automatisch den Loxone-Tab des neuen Objekts.
- Loxone-Tab um Felder fuer IO-Adresse, Control-Typ, Visu-Name, Raum und Einheit erweitert.
- `/objects_v33/new` nutzt technische Vorbelegungen als Adapterdaten statt als Allgemein-Quelle/-Ziel.
- Versionsstand auf `33.3.2` gesetzt.

## 33.3.1

- Objektmanager V33 auf objektzentrierte Anschluss-Architektur umgestellt.
- Allgemein-Tab enthaelt nur noch Objekt-Stammdaten: Name, Key, Datentyp, Kategorie, Raum, Einheit, Icon, Skalierung, Beschreibung und Aktiv.
- Quelle, Quelladresse, Ziel, Zieladresse und Influx-Aktivierung aus dem Allgemein-Tab entfernt.
- Objektstatus wird nicht mehr aus Allgemein-Feldern berechnet, sondern aus vollstaendigen aktiven Protokoll-Endpunkten.
- Routing-Tab zeigt erzeugte Adapter-Routen, Status und fehlende Endpunkte fuer unvollstaendige Objekte.
- Route-Generator erzeugt aktive Runtime-Routen aus Protokoll-Endpunkten fuer bestehende Mapping-Strukturen, inklusive KNX-/UDP-Richtungen.
- Adapter-Speichern schreibt keine Quelle-/Ziel-Felder mehr in das Objekt zurueck.
- Versionsstand auf `33.3.1` gesetzt.

## 33.3.0

- Objektbasierte aktive Routen fuer den ersten Runtime-Durchstich vorbereitet.
- `build_routes_from_objects()` erzeugt aus aktivierten Objekten virtuelle Routen in bestehenden Runtime-Strukturen.
- MQTT-Objekte werden zuerst angebunden: `mqtt -> loxone`, `mqtt -> knx`, `mqtt -> udp` und `mqtt -> influx` werden in vorhandene Loader-Formate uebersetzt.
- Bestehende Mapping-Dateien werden nicht als neue Parallelstruktur ersetzt; objektgenerierte Routen werden beim Laden zu `mqtt2lox`, `mqtt2udp`, `mqtt2knx` und `topic_config` gemerged.
- Nach Objekt-Speichern, Loeschen, Toggle und Adapter-Speichern werden Objektrouten neu berechnet; eine laufende Bridge wird neu geladen, eine gestoppte Bridge bleibt gestoppt.
- Objektmanager zeigt Route-Status-Badges: `aktiv`, `deaktiviert`, `unvollständig`, `fehler`.
- Logging fuer Objektrouten ergaenzt: Gesamtzahl, aktive Routen, uebersprungene Objekte und Fehler je Objekt.
- KNX/Loxone/UDP bleiben als Zieltypen vorbereitet; vollstaendige Nicht-MQTT-Quellen folgen spaeter.
- Versionsstand auf `33.3.0` gesetzt.

## 33.9.0

- Objektmanager-Core fuer MP-Gateway V33 eingefuehrt.
- Neues zentrales Objektmodell `GatewayObject` unter `app/models/object_model.py` ergaenzt.
- Neuer Service `app/services/object_service.py` speichert Objekte in `config/objects.json` und stellt CRUD-, Toggle- und Serialisierungsfunktionen bereit.
- Neue API-Routen ergaenzt: `GET/POST /api/objects`, `GET/PUT/DELETE /api/objects/<id>` und `POST /api/objects/<id>/toggle`.
- `/objects_v33` liest und schreibt nun ueber den neuen Object Service.
- Objektformular speichert Kernfelder wie Quelle, Quelladresse, Ziel, Datentyp, Einheit, Aktiv-Status und Influx-Status.
- MQTT Topic Manager/Explorer verlinkt `Objekt erstellen` auf den neuen Objektmanager mit MQTT-Quelle und Topic-Vorbefuellung.
- Bestehendes Layout bleibt erhalten; keine Runtime-Mapping-Erzeugung und keine Adapter-/Runtime-Anbindung.
- Versionsstand auf `33.9.0` gesetzt.

## 33.2.8a

- UI-Feinschliff fuer den Objektmanager V33.
- Linke Objektliste und rechter Editorbereich nutzen nun denselben Arbeitsflaechen-Hintergrund.
- Sidebar bleibt unveraendert dunkel.
- Objektkarten, Panels, Buttons und Protokoll-Badges bleiben unveraendert.
- Keine Runtime-Aenderung, keine Objektlogik-Aenderung und keine Adapterlogik-Aenderung.
- Versionsstand auf `33.2.8a` gesetzt.

## 33.2.8

- Objektmanager-V33-Hauptbereich optisch an Dashboard-/Standardseiten angeglichen.
- `/objects_v33` nutzt nun fuer Body, Hauptflaeche und Detailpanel den Standard-Grundhintergrund.
- Sidebar, Objektkarten-Farben und Protokoll-Badges bleiben unveraendert.
- Keine Runtime-Aenderung, keine Objektlogik-Aenderung und keine Adapterlogik-Aenderung.
- Versionsstand auf `33.2.8` gesetzt.

## 33.2.7g

- Externe Sidebar-Buttons wieder generisch aus der Sidebar-Button-Konfiguration gerendert.
- Unter `Externe Dienste` werden nur aktive Config-Eintraege angezeigt; Name, URL, Reihenfolge und `new_tab` kommen aus der Config.
- `new_tab=true` oeffnet externe Links mit `target="_blank"` und `rel="noopener noreferrer"`.
- `new_tab=false` oeffnet Links im Shell-Betrieb wieder im rechten Content-Bereich.
- Hart codierte externe Eintraege fuer InfluxDB/Grafana entfernt; neue aktive Config-Eintraege erscheinen automatisch.
- `Influx Explorer` bleibt unveraendert als interne MP-Gateway-Seite auf `/influx_explorer`.
- Keine Runtime-Aenderung, keine Objektmanager-Logik-Aenderung, keine Adapterlogik-Aenderung und keine Routen-Aenderung.
- Versionsstand auf `33.2.7g` gesetzt.

## 33.2.7c

- Sidebar-Link-Korrektur fuer externe Dienste.
- `Influx Explorer` bleibt im MP-Gateway-Menue intern auf `/influx_explorer`.
- `InfluxDB` unter `Externe Dienste` nutzt nun die externe URL aus der Sidebar-Konfiguration und zeigt keinen falschen internen Fallback mehr.
- `Grafana` unter `Externe Dienste` nutzt nun die externe URL aus der Sidebar-Konfiguration.
- Fehlt eine externe URL, wird der Eintrag deaktiviert angezeigt.
- Keine Runtime-Aenderung, keine Objektlogik-Aenderung, keine Adapterlogik-Aenderung und keine Routen-Aenderung.
- Versionsstand auf `33.2.7c` gesetzt.

## 33.2.7a

- Sidebar-Feinschliff ohne Routing- oder Runtime-Aenderung.
- Sichtbare Gruppenueberschrift `MP-Gateway` aus der Sidebar entfernt.
- Alter Objektmanager-Link aus der Sidebar entfernt; sichtbar bleibt nur `Objektmanager V33`.
- Bereich `Externe Dienste` auf `InfluxDB` und `Grafana` bereinigt.
- Keine Layoutaenderungen darueber hinaus, keine Objektlogik- oder Adapterlogik-Aenderung.
- Versionsstand auf `33.2.7a` gesetzt.

## 33.2.7

- Sidebar weiter bereinigt und in die Gruppen `MP-Gateway` und `Externe Dienste` gegliedert.
- MP-Gateway-Gruppe enthaelt Dashboard, MQTT Monitor, MQTT Hub, Loxone Monitor, Objektmanager, Objektmanager V33, KNX, KNX Monitor, Suche, Konfig pruefen, Influx Explorer und Einstellungen.
- Externe Dienste enthalten InfluxDB und Grafana klar getrennt von der internen Navigation.
- Neues Layout-Fundament vorbereitet: `templates/layout/base.html` und `templates/layout/page_header.html`.
- `/objects_v33` nutzt die neue Base-Struktur, bleibt funktional aber unveraendert.
- Keine Routen umgestellt, kein Redirect eingefuehrt, kein alter Objektmanager entfernt.
- Keine Runtime-Aenderung, keine Registry-Logik-Aenderung, keine Objektlogik-Aenderung, keine Adapterlogik-Aenderung und keine Mapping-Erzeugung.
- Versionsstand auf `33.2.7` gesetzt.

## 33.2.6

- Sidebar als gemeinsame MP-Gateway-Komponente nach `templates/shared/sidebar.html` ausgelagert.
- Zentrale Sidebar-Styles in `static/css/sidebar.css` ergaenzt und in Shell- sowie Standardlayout eingebunden.
- Shell-Navigation vereinheitlicht: Dashboard, MQTT Monitor, Loxone Monitor, MQTT Hub, Objektmanager, Objektmanager V33, KNX, KNX Monitor, Suche, Konfig pruefen, InfluxDB, Grafana und Einstellungen nutzen dieselbe Komponente.
- Aktiver Menuepunkt wird automatisch ueber die gemeinsame Klasse hervorgehoben und nutzt den gruenen linken Akzent.
- Header, App-Name, Untertitel, Status, Abstaende, Schriftgroessen, Buttonhoehen und Sidebar-Breite vereinheitlicht.
- Keine Runtime-Aenderung, keine Registry-Logik-Aenderung, keine Routing-Logik-Aenderung und keine Mapping-Erzeugung.
- Versionsstand auf `33.2.6` gesetzt.

## 33.2.5

- Objektmanager V33 weiter auf die festgelegte MP-Gateway-Designlinie gebracht.
- Filterchips bereinigt: `Alle`, `Aktiv`, `MQTT`, `Loxone`, `UDP`, `KNX`, `Influx`.
- Protokoll-Badges sind nun kraeftiger: MQTT blau, Loxone gruen, UDP violett, KNX orange, Influx tuerkis/blau.
- Inaktive Adapter-Badges bleiben grau und gedimmt.
- Ausgewaehlte Objektkarte deutlicher mit Rahmen, hellerem Hintergrund und dezentem Glow hervorgehoben.
- Sidebar-Active-State optisch geschaerft, ohne Navigation oder Routen zu aendern.
- Neue Doku `docs/UI_GUIDELINES.md` angelegt.
- Keine Runtime-Aenderung, keine Registry-Logik-Aenderung, keine Adapterlogik-Aenderung und keine Mapping-Erzeugung.
- Versionsstand auf `33.2.5` gesetzt.

## 33.2.4

- Objektmanager V33 optisch weiter an das Industrial-Dark-Referenzlayout angepasst.
- Linke Objektliste mit klareren Initialen, staerkerer Auswahlmarkierung, besseren Abstaenden und ruhigerer Zeilenhoehe ueberarbeitet.
- Jede Objektkarte zeigt nun immer alle Protokoll-Badges: MQTT, Loxone, UDP, KNX und Influx.
- Aktive Protokolle werden farbig hervorgehoben, inaktive Protokolle grau gedimmt.
- Projektfarbschema bleibt erhalten; Protokollfarben wurden dezent integriert.
- Keine Runtime-Aenderung, keine Registry-Logik-Aenderung, keine Adapterlogik-Aenderung und keine Mapping-Erzeugung.
- Versionsstand auf `33.2.4` gesetzt.

## 33.2.3

- Objektmanager V33 in der Sidebar verlinkt.
- Neuer Sidebar-Eintrag `Objektmanager V33` zeigt auf `/objects_v33`.
- `/objects_v33` optisch an das Industrial-Dark-Layout angepasst: Objektliste links, Detail-/Editorbereich rechts.
- Linke Spalte mit Suchfeld, Neu laden, Health Check, Filterchips und Objektkarten ergaenzt.
- Rechte Spalte mit Objektkopf, Aktionsbuttons und Tabs fuer Allgemein, MQTT, Loxone, UDP, KNX, Influx und Routing ergaenzt.
- Adapter-Editoren liegen nun in ihren jeweiligen Tabs; Routing-Vorschau liegt im Routing-Tab.
- Bestehender Objektmanager-Eintrag `/objects` bleibt unveraendert.
- Keine Runtime-Aenderung, keine Registry-Logik-Aenderung, keine Adapterlogik-Aenderung und keine V32-Objects-Routen geaendert.
- Versionsstand auf `33.2.3` gesetzt.

## 33.2.2

- Routing-Vorschau fuer den Objektmanager V33 ergaenzt.
- Neuer passiver Service `app/services/object_routing_preview.py` mit `build_object_routing_preview(object_def)`.
- `/objects_v33/edit/<uuid>` zeigt moegliche spaetere Verbindungen aktiver Adapter mit Quelle, Ziel, Richtung und Status `Vorschau`.
- Inaktive Adapter werden nicht beruecksichtigt; Influx wird nur als Ziel angezeigt.
- Keine Runtime-Anbindung, keine echten Mapping-Dateien geschrieben und keine V32-Objects-Aenderung.
- Versionsstand auf `33.2.2` gesetzt.

## 33.2.1

- Branding-Vorbereitung fuer MP-Gateway ergaenzt.
- Zentrale Konstanten `APP_NAME`, `APP_SUBTITLE` und `APP_LEGACY_NAME` in `app/branding.py` eingefuehrt.
- Sichtbare Shell-Titel und Header auf `MP-Gateway` und `Das Multiprotokoll-Gateway` umgestellt.
- `MQTT2Lox` bleibt vorerst technischer Projekt-/Repo-Name; Paket-, Ordner-, Routen- und Config-Namen bleiben unveraendert.
- Keine Runtime-Aenderung und keine Mapping-Erzeugung.
- Versionsstand auf `33.2.1` gesetzt.

## 33.2.0

- Adapter erhalten eigene Editor-Komponenten unter `app/templates/objects_v33/adapters/`.
- MQTT, UDP, KNX, Loxone und Influx besitzen eigene passive Editor-Bausteine fuer protokollspezifische Grundeinstellungen.
- Der Objekteditor bindet die Adapter dynamisch ein; allgemeine Objektdaten bleiben in einem getrennten Formular.
- `object_adapter_engine.py` verwaltet Laden, Serialisieren und Speichern der Adapterdaten aus den Editor-Formularen.
- Keine Runtime-Anbindung, keine Mapping-Erzeugung und keine bestehenden Mapping-Dateien geaendert.
- Versionsstand auf `33.2.0` gesetzt.

## 33.1.2

- Adapterverwaltung im neuen Objektmanager V33 integriert.
- `/objects_v33` zeigt bei der Objektbearbeitung alle bekannten Adapter: MQTT, UDP, KNX, Loxone und Influx.
- Adapter werden als schlichte Cards/Chips mit aktiv/inaktiv, Richtung, Datentyp und Kurzstatus angezeigt.
- Adapter koennen aktiviert, deaktiviert und ueber Platzhalterdialoge bearbeitet werden.
- Adapterdaten werden aus `object_registry.py` gelesen und ueber `object_adapter_engine.py` als Adapterinstanzen verwaltet.
- Keine Runtime-Anbindung, keine Mapping-Erzeugung, keine V32-Objects-Aenderung und keine bestehenden Mapping-Dateien geaendert.
- Versionsstand auf `33.1.2` gesetzt.

## 33.1.1

- Stabile interne Objekt-UUID fuer Objektmanager V33 ergaenzt.
- `ObjectDefinition` kompatibel um `uuid` und `key` erweitert: `uuid` ist die feste interne ID, `key` der technische lesbare Schluessel, `name` der frei aenderbare Anzeigename.
- `object_registry.py` ergaenzt bestehende V33-Eintraege ohne `uuid`/`key` beim Laden automatisch.
- `/objects_v33` bearbeitet und loescht Objekte nun ueber `uuid`.
- Keine Runtime-Logik, keine V32-Objects-Route und keine bestehenden Mapping-Dateien geaendert.
- Versionsstand auf `33.1.1` gesetzt.

## 33.1.0

- Parallelen Objektmanager V33 gestartet.
- Neuer Blueprint `app/routes/objects_v33.py` mit Route `/objects_v33`.
- Neue Templates unter `templates/objects_v33/` fuer Objektliste und Bearbeitung.
- Erste V33-Oberflaeche mit Suche, Neues Objekt, Bearbeiten und Loeschen ohne Adapterbearbeitung.
- Datenquelle ist die passive `object_registry.py`; bestehender Objektmanager, Runtime, UI, Routen und Mapping-Dateien bleiben unveraendert.
- Versionsstand auf `33.1.0` gesetzt.

## 33.0.3

- Einheitliche passive Adapter-Schnittstelle vorbereitet: `app/services/object_adapter_engine.py`.
- Basisklassen `BaseAdapter`, `MQTTAdapter`, `LoxoneAdapter`, `UDPAdapter`, `KNXAdapter` und `InfluxAdapter` mit `validate()`, `serialize()`, `deserialize()`, `enabled`, `direction` und `datatype` angelegt.
- `app/services/object_registry.py` kann neue Adapterobjekte speichern und laden.
- Keine Kommunikation, keine Runtime-Logik, keine UI, keine Routen und keine bestehenden Mapping-Dateien geaendert.
- Versionsstand auf `33.0.3` gesetzt.

## 33.0.2

- Passive V33-Objekt-Registry vorbereitet: `app/services/object_registry.py`.
- Registry-Funktionen fuer Laden, Speichern, Auflisten, Abrufen, Upsert, Loeschen und Validieren von `ObjectDefinition` vorbereitet.
- Speicherziel fuer spaetere V33-Objekte ist `data/objects_v33.json`; fehlende Datei liefert eine leere Liste.
- Bestehende Objektmanager-Logik, Runtime, UI, Routen, Configs und Mapping-Dateien bleiben unveraendert.
- Versionsstand auf `33.0.2` gesetzt.

## 33.0.1

- Adaptermodell V33 dokumentiert: `docs/OBJECT_ADAPTER_MODEL.md`.
- MQTT-, Loxone-, UDP-, KNX- und Influx-Adapterfelder mit gemeinsamen Feldern `enabled`, `direction`, `datatype`, `readonly` und `writeonly` beschrieben.
- Keine Runtime-Logik, keine UI, keine Routen und keine Config-Dateien geaendert.
- Versionsstand auf `33.0.1` gesetzt.

## 33.0.0

- Start der V33-Entwicklung mit Fokus auf Objektmanager 2.0.
- Neue Planungsdokumentation `docs/OBJECT_MANAGER_V33_PLAN.md` angelegt.
- Neues passives Service-Grundgeruest `app/services/object_model.py` mit `ObjectDefinition`, `ObjectAdapter`, `ObjectFlags` und Validierungshelfern angelegt.
- Bestehende Runtime-Logik, Routen, UI, Config-Dateien und Mapping-Dateien bleiben unveraendert.
- Versionsstand auf `33.0.0` gesetzt.

## 32.7.1

- Aufraeumen nach Legacy Removal: der leere `legacy/`-Ordner und der alte `legacy/__pycache__/`-Rest wurden entfernt.
- Alte Architektur-/Blueprint-/Runtime-Plan-Dokumente auf den aktuellen `app/core.py`-Stand aktualisiert.
- `templates/CHANGELOG_v32_1_0.txt` auf die neue Startkette angepasst.
- Keine App-Logik und keine UI geaendert.
- Versionsstand auf `32.7.1` gesetzt.

## 32.7.0

- Legacy Removal Phase J final umgesetzt: der bisherige App-Kern liegt jetzt in `app/core.py`.
- Der alte Legacy-Dateipfad wurde aus dem aktiven Projekt entfernt.
- `app/main.py` startet ausschliesslich ueber `from app import create_app`.
- `app/__init__.py` ist die zentrale App Factory und registriert RuntimeContext, App-Core und Blueprints.
- Der Importlib-Dateilader wurde aus `app/engine/port.py` entfernt; dort bleiben Startup-/Dependency-Checks und Versionsinformationen.
- Interne Blueprint-Delegation verwendet jetzt `app_core` statt eines Legacy-Extension-Keys.
- Versionsstand auf `32.7.0` gesetzt.

## 32.6.8

- Legacy Removal Phase H umgesetzt: System- und Runtime-Routen als System-Blueprint registriert.
- `app/routes/system.py` registriert Bridge Start/Stop, Loxone-/MQTT-Test und interne Broker-Routen.
- `app/engine/bridge.py` enthaelt die ausgelagerten Bridge-Start/Stop-Helfer.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- Die eigentliche Bridge-Logik (`bridge_async`, `bridge_runner`), MQTT-Logik, RuntimeContext und UI bleiben unveraendert.
- Versionsstand auf `32.6.8` gesetzt.

## 32.6.7

- Legacy Removal Phase G Teil 2 umgesetzt: KNX Monitor, KNX Monitor Config und Listener-Start als KNX-Blueprint-Routen registriert.
- `app/routes/knx.py` registriert jetzt zusaetzlich `/knx_monitor`, `/knx_monitor_data`, `/knx_monitor/influx`, `/knx_monitor/influx_type`, `/knx_monitor/influx_topic` und `/knx_listener_start`.
- Die migrierten KNX-Monitor-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- KNX Listener, xknx-nahe Logik, AsyncIO-/Thread-Logik, RuntimeContext, Eventnamen und JSON-Strukturen bleiben unveraendert.
- Versionsstand auf `32.6.7` gesetzt.

## 32.6.6

- Legacy Removal Phase G Teil 1 umgesetzt: KNX-Seiten und KNX-Mapping-Routen als Blueprint registriert.
- `app/routes/knx.py` registriert KNX Hub, KNX Settings, MQTT->KNX, UDP->KNX, KNX->MQTT und KNX->Loxone.
- Die migrierten KNX-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- KNX Monitor, KNX Listener, xknx-nahe Logik, RuntimeContext und Thread-Logik bleiben unveraendert im Legacy-Core.
- URLs, UI, JSON-Datenstrukturen und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.6.6` gesetzt.

## 32.6.5

- Legacy Removal Phase F umgesetzt: alle Server-Sent-Events als Events-Blueprint registriert.
- `app/routes/events.py` registriert Status-SSE, Live-Log-SSE, Live-Log-Full-SSE, MQTT-Monitor-SSE und KNX-Monitor-SSE.
- `app/utils/sse.py` enthaelt den ausgelagerten generischen SSE-Helper mit unveraendertem Keepalive-, Error- und EventSource-Verhalten.
- Die Event-Routen verwenden weiterhin die bestehenden Payload-Funktionen und Runtime-State-Quellen.
- Die entsprechenden `@app.route`-Registrierungen und der alte SSE-Helper wurden aus `app/core.py` entfernt.
- Eventnamen, JSON-Payloads, Keepalive-Verhalten, RuntimeContext und Thread-Logik bleiben unveraendert.
- Versionsstand auf `32.6.5` gesetzt.

## 32.6.4

- Legacy Removal Phase E umgesetzt: API-, Such- und Konflikt-Routen als Blueprint registriert.
- `app/routes/api.py` registriert globale Suche, Suchseite, Konfliktpruefung und Konfliktseite.
- Die migrierten API-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- Domain-nahe Data-/JSON-Routen bleiben bei ihren Blueprints oder im geplanten Domain-/Event-/System-Bereich.
- URLs, UI, JSON-Strukturen, Suchlogik, Konfliktlogik und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.6.4` gesetzt.

## 32.6.3

- Legacy Removal Phase D Teil 4 umgesetzt: kompletter Influx-Bereich als Blueprint registriert.
- `app/routes/influx.py` registriert Influx-Test, Influx Explorer, einzelnes Loeschen und Mehrfach-Loeschen.
- Die migrierten Influx-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- URLs, UI, JSON-Strukturen, Services, Influx-Logik und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.6.3` gesetzt.

## 32.6.2

- Legacy Removal Phase D Teil 3 umgesetzt: kompletter Loxone-Bereich als Blueprint registriert.
- `app/routes/loxone.py` registriert MQTT->Loxone, Speichern, Test und Live-Daten.
- Die migrierten Loxone-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- URLs, UI, Services, RuntimeContext und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.6.2` gesetzt.

## 32.6.1

- Legacy Removal Phase D Teil 2 umgesetzt: kompletter UDP-Bereich als Blueprint registriert.
- `app/routes/udp.py` registriert MQTT->UDP, UDP->MQTT, UDP Input, UDP Presets und UDP Discovery.
- Die migrierten UDP-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- URLs, UI, Services, RuntimeContext und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.6.1` gesetzt.

## 32.6.0

- Legacy Removal Phase D Teil 1 umgesetzt: kompletter MQTT-Bereich als Blueprint registriert.
- `app/routes/mqtt.py` registriert MQTT Hub, MQTT Monitor, Monitor-JSON-/Config-Routen, Topic Explorer, Topic Manager, Brokerverwaltung und Broker-Test.
- Die migrierten MQTT-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- URLs, HTML, JavaScript, Services, RuntimeContext und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.6.0` gesetzt.

## 32.5.1

- Legacy Removal Phase C umgesetzt: Config-, Backup- und Object-Routen als eigene Blueprints registriert.
- `app/routes/config.py` registriert Einstellungen, Core-/MQTT-/Influx-Speichern, Sidebar-Link-Speichern und Plugin-Speichern.
- `app/routes/backup.py` registriert Backup und Restore.
- `app/routes/objects.py` registriert Objektmanager, Objektbearbeitung, Mapping-Sync, Mapping-Rebuild, Speichern und Loeschen.
- Die migrierten Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- URLs, HTML-Ausgaben, Runtime-Logik und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.5.1` gesetzt.

## 32.5.0

- Legacy Removal Phase B umgesetzt: Dashboard als erster echter Blueprint registriert.
- `app/routes/dashboard.py` registriert jetzt die Routen `/`, `/dashboard_embed`, `/shell_status`, `/live_log`, `/live_log_page`, `/live_log_data`, `/clear_log` und `/clear_monitor`.
- Die Dashboard-Routen delegieren waehrend der Migration unveraendert auf die bestehenden Legacy-Handler.
- Die entsprechenden `@app.route`-Registrierungen wurden aus `app/core.py` entfernt.
- URLs, Rueckgabedaten, UI, RuntimeContext und Benutzerverhalten bleiben unveraendert.
- Versionsstand auf `32.5.0` gesetzt.

## 32.4.9

- Phase A aus `LEGACY_REMOVAL_PLAN.md` umgesetzt.
- `app/routes/` mit Blueprint-Platzhaltermodulen vorbereitet.
- `app/extensions.py` mit RuntimeContext-Zugriffshilfe angelegt.
- `app/__init__.py` als vorsichtige App-Factory-Vorbereitung angelegt.
- `app/main.py` startet weiterhin unveraendert ueber `app/engine/port.py` und `create_app()`.
- Keine Routen aus `app/core.py` verschoben, keine Logik geaendert, keine UI geaendert.
- Versionsstand auf `32.4.9` gesetzt.

## 32.4.8

- Legacy Removal Plan erstellt.
- Neue Datei `LEGACY_REMOVAL_PLAN.md` dokumentiert die aktuelle Startstruktur, verbleibende Aufgaben von `app/core.py`, Routen-/Helper-Gruppen, Zielstruktur und Migrationsphasen A bis J.
- Exit-Kriterien fuer die spaetere Entfernung von `app/core.py` definiert.
- Keine Routen verschoben, keine Logik geaendert, keine UI geaendert.
- Versionsstand auf `32.4.8` gesetzt.

## 32.4.7

- Alte KNX-Global-State-Reste aus `app/core.py` bereinigt.
- Entfernt wurden die alten Legacy-Globals fuer KNX Monitor-Log, KNX Monitor-Werte, KNX LastSeen-Dicts und Listener-Thread.
- KNX Monitor, LastSeen, Listener-Verwaltung und KNX-SSE-Versionierung verwenden nun ausschliesslich `runtime_context.knx`.
- Listener-Logik, xknx, UI und SSE-Route bleiben unveraendert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.7` gesetzt.

## 32.4.6

- KNX RuntimeContext Phase E umgesetzt.
- `KNXState` enthaelt jetzt `monitor_version`.
- `sse_versions["knx"]` wurde durch `runtime_context.knx.monitor_version` ersetzt.
- `bump_sse("knx")` erhoeht jetzt die KNX-Monitor-Version im RuntimeContext.
- KNX-SSE liest die Version fuer `version_name == "knx"` aus `runtime_context.knx.monitor_version`.
- Andere SSE-Versionen (`log`, `mqtt`, `status`) bleiben im bestehenden `sse_versions`-Dict.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.6` gesetzt.

## 32.4.5

- KNX RuntimeContext Phase D1 umgesetzt.
- `KNXState` enthaelt jetzt Listener-Verwaltung: `listener_thread`, `listener_running`, `start_requested` und `stop_requested`.
- Wrapper fuer KNX-Listener-Verwaltung in `app/core.py` ergaenzt.
- `ensure_knx_listener_started` nutzt fuer Thread-Referenz und Running-State jetzt `runtime_context.knx`.
- Alte globale Variable `knx_listener_thread` entfernt.
- `_knx_listener_async`, `telegram_received_cb`, xknx, asyncio, `send_knx_value`, `add_knx_monitor_entry`, Monitor und SSE bleiben unveraendert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.5` gesetzt.

## 32.4.4

- KNX RuntimeContext Phase C umgesetzt.
- `KNXState` enthaelt jetzt zusaetzlich `monitor_log` als `deque(maxlen=15)`.
- Wrapper fuer KNX-Monitor-Log in `app/core.py` ergaenzt.
- `add_knx_monitor_entry` schreibt `knx_monitor_log` weiterhin wie bisher und spiegelt zusaetzlich nach `runtime_context.knx.monitor_log`.
- KNX Monitor Payload liest Log-Eintraege bevorzugt aus `runtime_context.knx`.
- `knx_listener_thread`, xknx, asyncio, `ensure_knx_listener_started`, `knx_listener_runner`, `sse_versions["knx"]` und `/events/knx_monitor` bleiben unveraendert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.4` gesetzt.

## 32.4.3

- KNX RuntimeContext Phase B umgesetzt.
- `KNXState` enthaelt jetzt zusaetzlich `monitor_values`.
- Wrapper fuer KNX-Monitor-Werte in `app/core.py` ergaenzt.
- `add_knx_monitor_entry` schreibt `knx_monitor_values` weiterhin wie bisher und spiegelt zusaetzlich nach `runtime_context.knx.monitor_values`.
- KNX Hub und KNX Monitor Payload lesen Monitor-Werte bevorzugt aus `runtime_context.knx`.
- `knx_monitor_log`, `knx_listener_thread`, SSE-Versionierung, Eventstream-Route und xknx Listener bleiben unveraendert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.3` gesetzt.

## 32.4.2

- KNX RuntimeContext Phase A umgesetzt.
- `KNXState` enthaelt jetzt `mqtt2knx_last_seen`, `knx2mqtt_last_seen`, `knx2lox_last_seen` und `lock`.
- KNX-LastSeen-Wrapper in `app/core.py` ergaenzt.
- KNX-Service schreibt LastSeen-Daten optional zusaetzlich in `runtime_context.knx`.
- KNX-Routen fuer MQTT->KNX, KNX->MQTT und KNX->Loxone lesen bevorzugt aus `runtime_context.knx` mit Fallback auf alte Dicts.
- `udp2knx_last_seen` bleibt weiterhin in `runtime_context.udp`.
- Monitor-Log, Monitor-Werte, Listener-Thread, SSE und xknx bleiben unveraendert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.2` gesetzt.

## 32.4.1

- KNX Runtime Migration Plan erstellt.
- Neue Datei `KNX_RUNTIME_MIGRATION_PLAN.md` mit KNX-States, Lesern/Schreibern, Routen, Services, Thread-/Async-/SSE-Risiken und empfohlener Migrationsreihenfolge.
- Besonders betrachtet: KNX Listener, Monitor, xknx Callback, MQTT->KNX, UDP->KNX, KNX->MQTT und KNX->Loxone.
- Keine KNX-State-Migration, keine Logikaenderungen, keine UI-Aenderungen, keine Service-Aenderungen.
- Versionsstand auf `32.4.1` gesetzt.

## 32.4.0

- BrokerState vollstaendig in den RuntimeContext migriert.
- `BrokerState` enthaelt jetzt `process`, `running`, `status`, `start_requested`, `stop_requested`, `restart_requested` und `lock`.
- Interner-Broker-Status, Start und Stop lesen/schreiben nun `runtime_context.broker`.
- Alte globale Variable `internal_broker_process` entfernt.
- Keine Bridge-, MQTT-, UDP- oder KNX-States geaendert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.4.0` gesetzt.

## 32.3.9

- UDP-Laufzeitdaten schrittweise in den RuntimeContext migriert.
- `UDPState` enthaelt jetzt MQTT->UDP, UDP->MQTT, UDP->KNX, UDP-Input, Discovery-State, Discovery-Flag und Lock.
- Legacy-Wrapper fuer UDP-Last-Seen-Lesen, Schreiben und Leeren ergaenzt.
- UDP-Service schreibt Last-Seen-Daten optional zusaetzlich in `runtime_context.udp`.
- UDP-Seiten und UDP-Datenrouten lesen bevorzugt aus `runtime_context.udp` mit Fallback auf bestehende parallele Globals.
- Alte UDP-Globals bleiben parallel bestehen.
- Keine MQTT-, KNX-, Bridge- oder Broker-States geaendert.
- Keine UI- oder UDP-Logik-Aenderungen.
- Versionsstand auf `32.3.9` gesetzt.

## 32.3.8

- MQTT-Monitor-State schrittweise in den RuntimeContext vorbereitet.
- `MQTTState` enthaelt jetzt `mqtt_monitor_values`, `mqtt_clients`, `mqtt_client`, `monitor_version` und `lock`.
- Legacy-Wrapper fuer MQTT-Monitor-Lesen, Schreiben und Leeren ergaenzt.
- MQTT-Callback schreibt Monitorwerte zusaetzlich in `runtime_context.mqtt`.
- MQTT Monitor, MQTT Hub, `/monitor_data` und MQTT-Monitor-SSE lesen bevorzugt aus `runtime_context.mqtt`.
- Alte MQTT-Globals bleiben parallel bestehen.
- Keine KNX-, UDP-, Bridge- oder Broker-States migriert.
- Keine UI- oder MQTT-Broker-Logik geaendert.
- Versionsstand auf `32.3.8` gesetzt.

## 32.3.7

- Bridge-State vollstaendig in `runtime_context.bridge` migriert.
- `BridgeState` enthaelt jetzt `running`, `status`, `stop_requested` und `thread`.
- Alte globale Variablen `bridge_running`, `bridge_status`, `bridge_stop_requested` und `bridge_thread` entfernt.
- Bridge Start/Stop, Status-SSE, Dashboard-Status und Layout-Status lesen/schreiben nun den RuntimeContext.
- Keine MQTT-, UDP-, KNX- oder Broker-States migriert.
- Keine UI-Aenderungen.
- Versionsstand auf `32.3.7` gesetzt.

## 32.3.5

- LiveLog-State im RuntimeContext-Grundgeruest vorbereitet.
- `LiveLogState` enthaelt jetzt `entries`, `lock` und `version`.
- Factory `create_runtime_context()` ergaenzt und in `app/core.py` eine globale RuntimeContext-Instanz erzeugt.
- Bestehendes Legacy-`live_log` bleibt aktiv; `add_log_entry` spiegelt neue Eintraege zusaetzlich in `runtime_context.live_log`.
- Keine Bridge-, MQTT-, KNX-, UDP- oder Broker-States veraendert.
- Keine UI-Aenderungen und keine Routen-Aenderungen.
- Versionsstand auf `32.3.5` gesetzt.

## 32.3.4

- Grundgeruest fuer den zukuenftigen RuntimeContext unter `app/runtime/` erstellt.
- Leere Dataclass-Platzhalter fuer Bridge, Live-Log, MQTT, KNX, UDP und Broker angelegt.
- `RuntimeContext` als reine Struktur in `app/runtime/context.py` definiert.
- Noch keine Instanz erzeugt, nichts importiert und keine Laufzeitdaten verschoben.
- Keine Logikaenderungen, keine UI-Aenderungen und keine Service-Aenderungen.
- Versionsstand auf `32.3.4` gesetzt.

## 32.3.3

- RuntimeContext-Plan fuer globale Variablen und Laufzeit-States in `app/core.py` erstellt.
- Neue Datei `RUNTIME_CONTEXT_PLAN.md` mit Zweck, Lese-/Schreibstellen, betroffenen Routen, Services, Thread-/SSE-Risiko und Zielbereich.
- Listen, Dicts, Locks, Threads, Eventstream-Versionen sowie Start/Stop-Flags gesondert markiert.
- Keine Dateien verschoben, keine Funktionen verschoben, keine Logikänderungen und keine UI-Änderungen.
- Versionsstand auf `32.3.3` gesetzt.

## 32.3.2

- Blueprint-Migrationsplan fuer alle 117 Flask-Routen in `app/core.py` erstellt.
- Neue Datei `BLUEPRINT_PLAN.md` mit Ziel-Blueprint, Methode, aktueller Funktion, Abhaengigkeiten, Risiko, Markierungen und empfohlener Reihenfolge.
- SSE-, JSON-, Write- und globale-State-Routen gesondert markiert.
- Keine Routen verschoben, keine Logikänderungen und keine UI-Änderungen.
- Versionsstand auf `32.3.2` gesetzt.

## 32.3.1

- Architektur-Review nach der ersten Modularisierung aktualisiert und vertieft.
- `ARCHITECTURE_REVIEW.md` neu strukturiert mit Datei-Bewertung, Routen-Kandidaten, Import-/State-Befunden und Zielstruktur.
- Keine Dateien verschoben, keine Funktionen verschoben, keine Logikänderungen und keine UI-Änderungen.
- Versionsstand auf `32.3.1` gesetzt.

## 32.3.0

- Architektur-Review nach der ersten Modularisierungsrunde erstellt.
- Neuer Bericht `ARCHITECTURE_REVIEW.md` mit aktueller Struktur, Problemen, Prioritäten, Aufwand und Empfehlungen.
- Keine Funktionsverschiebungen, keine Logikänderungen und keine UI-Änderungen.
- Versionsstand auf `32.3.0` gesetzt.

## 32.2.9

- Template-/HTML-Hilfsfunktionen nach `app/services/template.py` ausgelagert.
- Legacy-Core importiert den neuen Template-Service als `template_service`; bestehende Render-Routen und große `render_template_string`-Blöcke bleiben unverändert.
- Eingebetteter Seitenrahmen, Layout-Renderer, Datalist-Builder und Select-Builder nutzen nun den Template-Service.
- Keine UI-, Text-, Logik- oder Feature-Änderungen.
- Versionsstand auf `32.2.9` gesetzt.

## 32.2.8

- Backup-Dateisuche sowie Backup-/Restore-Zip-Logik nach `app/services/backup.py` ausgelagert.
- Legacy-Core importiert den neuen Backup-Service als `backup_service` und behält die bestehenden `/backup`- und `/restore`-Routen unverändert.
- Backup-Pfade, Backup-Ordner und Restore-Zielprüfung bleiben unverändert.
- Keine UI-, Logik- oder Feature-Änderungen.
- Versionsstand auf `32.2.8` gesetzt.

## 32.2.7

- Runtime-/Status-/Live-Log- und interner-Broker-Hilfsfunktionen nach `app/services/runtime.py` ausgelagert.
- Legacy-Core importiert den neuen Runtime-Service als `runtime_service` und übergibt Live-Log, Status-State, Config-Loader und Broker-Prozess gezielt als Parameter.
- Bestehende Status-, Live-Log- und Broker-Routen bleiben unverändert.
- Keine UI-, Logik- oder Feature-Änderungen.
- Versionsstand auf `32.2.7` gesetzt.

## 32.2.6

- Influx-Schreib-, Formatierungs- und Explorer-Hilfsfunktionen aus `app/core.py` nach `app/services/influx.py` ausgelagert.
- Legacy-Core importiert den neuen Influx-Service als `influx_service` und übergibt Config-Loader, Topic-Loader und Logger gezielt als Parameter.
- Influx Settings, Influx Explorer UI und bestehende Routen bleiben unverändert im Legacy-Core.
- Keine UI-, Logik- oder Feature-Änderungen.
- Versionsstand auf `32.2.6` gesetzt.

## 32.2.5

- KNX-Hilfs- und Bridge-Funktionen nach `app/services/knx.py` ausgelagert.
- KNX Listener, Monitor-Listen, Monitor-Payload und Monitor-Routen bleiben in `app/core.py`.
- KNX TX-Monitor-Eintraege laufen ueber den uebergebenen `add_knx_monitor_entry`-Callback weiter in die zentrale Legacy-Liste.
- KNX RX-Monitor-Eintraege werden weiterhin direkt im Legacy-Listener geschrieben.
- Keine UI- oder Feature-Aenderungen.
- Versionsstand auf `32.2.5` gesetzt.

## 32.2.4

- Loxone-Hilfsfunktionen aus `app/core.py` nach `app/services/loxone.py` ausgelagert.
- Legacy-Core importiert den neuen Loxone-Service als `loxone_service` und übergibt benötigte Legacy-Abhängigkeiten gezielt als Parameter.
- Keine Logik-, UI- oder Feature-Aenderungen.
- Versionsstand auf `32.2.4` gesetzt.

## 32.2.3

- Object-/Objektmanager-Hilfsfunktionen aus `app/core.py` nach `app/services/object.py` ausgelagert.
- Legacy-Core importiert den neuen Object-Service als `object_service` und ruft die verschobenen Funktionen mit Modulpräfix auf.
- Keine Logik-, UI- oder Feature-Aenderungen.
- Versionsstand auf `32.2.3` gesetzt.

## 32.0.0

- Technische Versionspraefixe aus Python-Dateinamen und Imports entfernt.
- Startkette auf `app/engine/port.py` und `app/core.py` umgestellt.
- Service-Module ohne Versionspraefix angebunden: `config.py`, `mqtt.py`, `udp.py`.
- Sichtbare Versionsanzeige auf `32.0.0` gesetzt.
- Keine UI-, Logik- oder Feature-Aenderungen.

## 32.2.2

- UTF-8-Auslieferung der Flask-App fuer HTML und JSON abgesichert.
- Mojibake-/Umlautfehler im Port korrigiert, unter anderem `MQTT → UDP`, `MQTT → KNX` und `Noch keine Logeinträge.`.
- `render_template_string`-HTML-Bloecke auf defekte Sonderzeichen geprueft und repariert.
- Keine Logik- oder UI-Aenderungen.
- Versionsstand auf `32.2.2` gesetzt.

## 32.2.1

- UDP Listener, UDP-Sendefunktionen, MQTT->UDP, UDP->MQTT, UDP-Presets und UDP-Testhilfen in `app/services/udp.py` gekapselt.
- Legacy-Core verwendet den neuen UDP-Service weiter ueber die bestehenden Funktionsnamen und URLs.
- Live-State fuer `mqtt2udp_last_seen`, `udp2mqtt_last_seen` und `udp_input_last_seen` liegt nun im Service und bleibt fuer die alten Seiten verfuegbar.
- Keine UI-Aenderungen und keine Config-Dateinamen geaendert.
- Versionsstand auf `32.2.1` angehoben.

## 32.2.0

- MQTT-Verbindungsaufbau, Brokerliste, MQTT-Monitor-State und MQTT-Testverbindung in `app/services/mqtt.py` gekapselt.
- Legacy-Core verwendet den neuen Service weiter mit dem bestehenden Routing-Callback.
- MQTT-Monitor-Werte bleiben unter dem alten Namen `mqtt_monitor_values` verfuegbar.
- Keine UI-Aenderungen und keine Config-Dateinamen geaendert.
- Versionsstand auf `32.2.0` angehoben.

## 32.1.0

- Config-/JSON-Dateifunktionen aus dem Port in `app/services/config.py` ausgelagert.
- Legacy-Core importiert und nutzt die v32-Service-Funktionen weiter unter den alten Funktionsnamen.
- Keine UI-Aenderungen und keine Objektmanager-Logikaenderungen.
- Versionsstand auf `32.1.0` angehoben.

## 32.0.1

- `loxwebsocket`, `paho-mqtt` und `requests` werden im Port optional abgefangen.
- Fehlen optionale Bibliotheken, startet die Anwendung trotzdem vollstaendig.
- Bridge-/Shell-Status zeigt bei fehlendem Loxone-Modul: `Loxone: Bibliothek nicht installiert`.
- Startpruefung ergaenzt: Python, Flask, MQTT, Loxone, Requests sowie optionale KNX/Influx-Module.
- `requirements.txt` fuer den Port ergaenzt.

## 32.0.0-port

- Legacy-Anwendung als funktionale Basis in die v32-Projektstruktur geladen.
- Config-, Mapping-, Monitor-, Backup-, MQTT-, UDP-, KNX-, Loxone-, Influx- und Objektmanager-Logik bleibt erhalten.
- v32 Startpunkt `app/main.py` delegiert an den Legacy-Core.
- Persistente Pfade werden auf `config/`, `data/` und `backups/` im v32-Projekt gesetzt.





