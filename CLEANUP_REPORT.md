# Cleanup Report

Version: 32.0.1

## Grundlage

Die aktive Anwendung startet ueber:

- `app/main.py`
- `app/engine/port.py`
- `app/core.py`

Die geloeschten Dateien wurden nicht mehr von dieser Startkette importiert oder registriert. Die Legacy-Anwendung rendert ihre Oberflaeche ueber `render_template_string`; die alten v32-Jinja-Templates und v32-Static-Assets wurden daher nicht mehr verwendet.

## Geloeschte alte v32-Dateien

- `app/routes/api.py`
- `app/routes/pages.py`
- `app/routes/legacy.py`
- `app/engine/mapper.py`
- `app/engine/router.py`
- `app/engine/runtime.py`
- `app/services/influx_service.py`
- `app/services/knx_service.py`
- `app/services/loxone_service.py`
- `app/services/mqtt.py`
- `app/services/object_service.py`
- `app/services/udp.py`
- `app/services/runtime_service.py`
- `app/models/object_model.py`
- `app/utils/logger.py`

## Geloeschte alte UI-Dateien

- `templates/base.html`
- `templates/dashboard.html`
- `templates/influx.html`
- `templates/knx.html`
- `templates/mqtt.html`
- `templates/objects.html`
- `templates/settings.html`
- `templates/sidebar.html`
- `static/css/app.css`
- `static/css/theme.css`
- `static/js/app.js`

## Geloeschte generierte Dateien

Alle vorhandenen `__pycache__/*.pyc` Dateien wurden entfernt. Diese Dateien sind generierte Python-Cache-Dateien und werden bei Bedarf automatisch neu erstellt. Fuer die technische Pruefung wurden sie kurz neu erzeugt und danach erneut entfernt.

## Behalten

- `app/main.py`
- `app/engine/port.py`
- `app/services/config.py`
- `app/core.py`
- `config/*.json`
- `requirements.txt`
- `templates/CHANGELOG_v32_0_1.txt`

## Hinweis

Die leeren Ordner unter `app/routes`, `app/models`, `app/utils`, `static` oder `templates` koennen im Dateisystem noch existieren. Sie enthalten aber keine geloeschten Altdateien mehr.
