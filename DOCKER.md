# MP-Gateway 34.0.2 – Docker mit einem Daten-Volume

Die komplette Anwendung liegt nach dem ersten Start in einem einzigen Docker-Volume:

```text
/var/lib/docker/volumes/mpgateway_data/_data/
├── app/
├── templates/
├── static/
├── config/
├── data/
├── backups/
├── logs/
├── requirements.txt
└── VERSION
```

Das Image enthält eine Ausgangskopie. Beim ersten Start wird sie einmalig in das leere Volume kopiert. Bei späteren Starts wird das Volume nicht überschrieben.

## Installation

```bash
unzip MP-Gateway_34.0.2.zip
cd MP-Gateway
docker compose up -d --build
```

Weboberfläche:

```text
http://IP-DES-DOCKER-HOSTS:8099
```

Status und Protokoll:

```bash
docker compose ps
docker compose logs -f mp-gateway
```

Volume prüfen:

```bash
docker volume inspect mpgateway_data
ls -la /var/lib/docker/volumes/mpgateway_data/_data
```

## Vorhandene alte Daten übernehmen

Container zunächst stoppen:

```bash
docker compose down
```

Danach nur die benötigten Ordner aus dem alten Volume kopieren, beispielsweise:

```bash
cp -a /var/lib/docker/volumes/mqtt2lox_data/_data/config/. /var/lib/docker/volumes/mpgateway_data/_data/config/
cp -a /var/lib/docker/volumes/mqtt2lox_data/_data/data/. /var/lib/docker/volumes/mpgateway_data/_data/data/
cp -a /var/lib/docker/volumes/mqtt2lox_data/_data/backups/. /var/lib/docker/volumes/mpgateway_data/_data/backups/
```

Anschließend:

```bash
docker compose up -d
```

Wichtig: Nicht die alte `app.py` oder alte Programmordner über die neue Version kopieren. Für die Übernahme reichen normalerweise `config`, `data` und `backups`.

## Backup des kompletten Volumes

```bash
docker run --rm \
  -v mpgateway_data:/data:ro \
  -v "$PWD":/backup \
  alpine \
  tar czf /backup/mpgateway-volume-backup.tar.gz -C /data .
```
