FROM python:3.13-slim

LABEL org.opencontainers.image.title="MP-Gateway" \
      org.opencontainers.image.description="Multi-Protokoll-Gateway für KNX, MQTT, UDP, Loxone und InfluxDB" \
      org.opencontainers.image.version="34.4.6"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    MQTT2LOX_APP_ROOT=/mpgateway \
    MQTT2LOX_CONFIG_DIR=/mpgateway/config \
    MQTT2LOX_DATA_DIR=/mpgateway/data \
    MQTT2LOX_BACKUP_DIR=/mpgateway/backups

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates mosquitto mosquitto-clients \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/mpgateway-source
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . /opt/mpgateway-source
RUN chmod +x /opt/mpgateway-source/docker-entrypoint.sh \
    && sha256sum /opt/mpgateway-source/requirements.txt | awk '{print $1}' > /opt/mpgateway-source/.image-requirements.sha256

VOLUME ["/mpgateway"]
WORKDIR /mpgateway
EXPOSE 8099/tcp

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8099/startup_status', timeout=3).read()" || exit 1

ENTRYPOINT ["/opt/mpgateway-source/docker-entrypoint.sh"]
CMD ["python", "-u", "app/main.py"]
