"""OpenCCU / CCU-Jack basis integration."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from datetime import datetime

from flask import Blueprint, current_app, jsonify, redirect, request

bp = Blueprint("openccu", __name__)


def _core():
    return current_app.extensions["app_core"]


def _cfg():
    config = _core().load_config()
    return config.get("openccu", {})


def _esc(value):
    return _core().escape(str(value or ""))


def _checked(value):
    return "checked" if value else ""


def _settings_content(notice: str = ""):
    cfg = _cfg()
    return f"""
{notice}
<form method="post" action="/openccu/save">
  <div class="card compact-card">
    <h1>OpenCCU / CCU-Jack</h1>
    <p class="small">Grundkonfiguration für OpenCCU, RaspberryMatic und CCU-Jack. Die XML-API liefert Geräte- und Kanalnamen; CCU-Jack MQTT liefert die Livewerte.</p>
  </div>
  <div class="card">
    <h2 class="section-title">OpenCCU Verbindung</h2>
    <label><input type="checkbox" name="enabled" {_checked(cfg.get('enabled'))}> Integration aktivieren</label>
    <label>OpenCCU Host / IP</label>
    <input name="host" value="{_esc(cfg.get('host'))}" placeholder="z. B. 192.168.1.50">
    <label>HTTP-Port</label>
    <input name="http_port" value="{_esc(cfg.get('http_port', 80))}">
    <label><input type="checkbox" name="https" {_checked(cfg.get('https'))}> HTTPS verwenden</label>
    <label>API-Benutzer optional</label>
    <input name="api_user" value="{_esc(cfg.get('api_user'))}">
    <label>API-Passwort optional</label>
    <input name="api_password" type="password" value="{_esc(cfg.get('api_password'))}">
  </div>
  <div class="card">
    <h2 class="section-title">CCU-Jack MQTT</h2>
    <label>MQTT Host</label>
    <input name="mqtt_host" value="{_esc(cfg.get('mqtt_host') or cfg.get('host'))}" placeholder="meist identisch mit OpenCCU Host">
    <label>MQTT-Port</label>
    <input name="mqtt_port" value="{_esc(cfg.get('mqtt_port', 1883))}">
    <label>MQTT-Benutzer optional</label>
    <input name="mqtt_user" value="{_esc(cfg.get('mqtt_user'))}">
    <label>MQTT-Passwort optional</label>
    <input name="mqtt_password" type="password" value="{_esc(cfg.get('mqtt_password'))}">
    <label>Topic-Präfix</label>
    <input name="topic_prefix" value="{_esc(cfg.get('topic_prefix', 'device/status/#'))}" placeholder="device/status/#">
    <label><input type="checkbox" name="mqtt_tls" {_checked(cfg.get('mqtt_tls'))}> MQTT TLS verwenden</label>
    <div class="button-row" style="margin-top:14px;">
      <button type="submit">Speichern</button>
      <button type="submit" formaction="/openccu/test" formmethod="post">Verbindung testen</button>
      <a class="button-link" href="/openccu_explorer">OpenCCU Explorer öffnen</a>
    </div>
  </div>
</form>
"""


def _form_cfg():
    old = _cfg()
    def int_value(name, default):
        try:
            return int(request.form.get(name, default))
        except (TypeError, ValueError):
            return int(default)
    return {
        "enabled": "enabled" in request.form,
        "host": request.form.get("host", old.get("host", "")).strip(),
        "http_port": int_value("http_port", old.get("http_port", 80)),
        "https": "https" in request.form,
        "api_user": request.form.get("api_user", old.get("api_user", "")).strip(),
        "api_password": request.form.get("api_password", old.get("api_password", "")),
        "mqtt_host": request.form.get("mqtt_host", old.get("mqtt_host", "")).strip(),
        "mqtt_port": int_value("mqtt_port", old.get("mqtt_port", 1883)),
        "mqtt_user": request.form.get("mqtt_user", old.get("mqtt_user", "")).strip(),
        "mqtt_password": request.form.get("mqtt_password", old.get("mqtt_password", "")),
        "mqtt_tls": "mqtt_tls" in request.form,
        "topic_prefix": request.form.get("topic_prefix", old.get("topic_prefix", "device/status/#")).strip() or "device/status/#",
        "last_test": old.get("last_test", {}),
    }


@bp.get("/openccu_settings_embed")
def settings_embed():
    return _core().embedded_page("OpenCCU / CCU-Jack", _settings_content())


@bp.post("/openccu/save")
def save():
    config = _core().load_config()
    config["openccu"] = _form_cfg()
    _core().save_config(config)
    runtime = current_app.extensions.get("openccu_mqtt_runtime")
    if runtime is not None:
        runtime.reload(config["openccu"])
    _core().add_log_entry("OpenCCU / CCU-Jack Konfiguration gespeichert")
    return redirect("/openccu_settings_embed")


@bp.post("/openccu/test")
def test():
    cfg = _form_cfg()
    results = []
    host = cfg.get("host")
    if not host:
        results.append((False, "OpenCCU Host fehlt"))
    else:
        scheme = "https" if cfg.get("https") else "http"
        url = f"{scheme}://{host}:{cfg.get('http_port', 80)}/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MP-Gateway/34.6.9"})
            with urllib.request.urlopen(req, timeout=5) as response:
                results.append((True, f"OpenCCU HTTP erreichbar (Status {response.status})"))
        except urllib.error.HTTPError as exc:
            results.append((True, f"OpenCCU HTTP erreichbar (Status {exc.code})"))
        except Exception as exc:
            results.append((False, f"OpenCCU HTTP nicht erreichbar: {exc}"))

    mqtt_host = cfg.get("mqtt_host") or host
    try:
        if not mqtt_host:
            raise ValueError("MQTT Host fehlt")
        with socket.create_connection((mqtt_host, int(cfg.get("mqtt_port", 1883))), timeout=5):
            pass
        results.append((True, f"CCU-Jack MQTT-Port {cfg.get('mqtt_port', 1883)} erreichbar"))
    except Exception as exc:
        results.append((False, f"CCU-Jack MQTT nicht erreichbar: {exc}"))

    cfg["last_test"] = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "ok": all(ok for ok, _ in results),
        "results": [text for _, text in results],
    }
    config = _core().load_config()
    config["openccu"] = cfg
    _core().save_config(config)
    cls = "ok" if cfg["last_test"]["ok"] else "bad"
    lines = "<br>".join(("✅ " if ok else "❌ ") + _esc(text) for ok, text in results)
    notice = f'<div class="card {cls}">{lines}</div>'
    return _core().embedded_page("OpenCCU / CCU-Jack", _settings_content(notice))


def _runtime():
    return current_app.extensions.get("openccu_mqtt_runtime")


def _metadata():
    runtime = _runtime()
    if runtime is not None:
        return runtime.metadata
    return current_app.extensions.get("openccu_metadata_cache")


@bp.get("/api/openccu/discovery")
def discovery_data():
    runtime = _runtime()
    if runtime is not None:
        return jsonify(runtime.snapshot())

    metadata = _metadata()
    if metadata is not None:
        metadata.ensure_fresh()
        devices = metadata.snapshot_catalog()
        for device in devices:
            device.setdefault("live_datapoints", [])
            device.setdefault("online", False)
            device.setdefault("last_update", "")
        cfg = _cfg()
        return jsonify({
            "status": {"enabled": bool(cfg.get("enabled")), "connected": False, "state": "error",
                       "message": "MQTT-Laufzeit nicht verfügbar – XML-Geräte bleiben nutzbar",
                       "host": str(cfg.get("mqtt_host") or cfg.get("host") or ""),
                       "port": int(cfg.get("mqtt_port", 1883) or 1883),
                       "topic": str(cfg.get("topic_prefix") or "device/status/#"),
                       "received": 0, "unique_topics": 0, "last_message": ""},
            "metadata_status": metadata.snapshot_status(), "devices": devices, "entries": []})
    return jsonify({"status": {"state": "error", "message": "OpenCCU-Dienste nicht verfügbar"},
                    "metadata_status": {"state": "error", "message": "XML-Cache nicht verfügbar"},
                    "devices": [], "entries": []}), 503


@bp.post("/api/openccu/discovery/clear")
def discovery_clear():
    runtime = _runtime()
    if runtime is not None:
        runtime.clear()
    return jsonify({"success": True})


@bp.post("/api/openccu/reconnect")
def reconnect():
    runtime = _runtime()
    if runtime is None:
        return jsonify({"success": False, "error": "runtime_unavailable"}), 503
    runtime.reload()
    return jsonify({"success": True})


@bp.post("/api/openccu/metadata/refresh")
def metadata_refresh():
    metadata = _metadata()
    if metadata is None:
        return jsonify({"success": False, "error": "metadata_unavailable"}), 503
    started = metadata.refresh_async()
    return jsonify({"success": True, "started": started, "status": metadata.snapshot_status()})


@bp.get("/openccu_explorer")
def explorer():
    content = r"""
<style>
.openccu-shell { height:calc(100vh - 118px); min-height:620px; display:flex; flex-direction:column; gap:14px; overflow:hidden; }
.openccu-toolbar { flex:0 0 auto; }
.openccu-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap; }
.openccu-statusline { display:flex; gap:18px; align-items:center; flex-wrap:wrap; margin-top:8px; }
.openccu-diagnostics { display:grid; grid-template-columns:repeat(5,minmax(120px,1fr)); gap:8px; margin-top:10px; }
.openccu-diag { border:1px solid var(--border-color,#3a414f); border-radius:7px; padding:7px 9px; background:rgba(127,127,127,.05); min-width:0; }
.openccu-diag-label { font-size:.72rem; opacity:.65; text-transform:uppercase; letter-spacing:.04em; }
.openccu-diag-value { margin-top:2px; font-size:.84rem; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.openccu-grid { min-height:0; flex:1 1 auto; display:grid; grid-template-columns:minmax(300px, 36%) minmax(0,1fr); gap:14px; overflow:hidden; }
.openccu-list-card, .openccu-detail-card { min-height:0; height:100%; overflow:hidden; display:flex; flex-direction:column; }
.openccu-list-head { flex:0 0 auto; }
.openccu-items { min-height:0; flex:1 1 auto; overflow-y:auto; overflow-x:hidden; margin:12px -4px 0; padding:0 4px 8px; }
.openccu-device { width:100%; text-align:left; border:1px solid var(--border-color,#3a414f); border-radius:9px; padding:11px 12px; margin:0 0 8px; background:var(--panel2,#1d212b); cursor:pointer; color:var(--text,#eef2ff); transition:.15s ease; }
.openccu-device:hover, .openccu-device.active { border-color:#2b8a3e; box-shadow:0 0 0 1px #2b8a3e inset; }
.openccu-device-row { display:flex; align-items:center; gap:9px; min-width:0; }
.openccu-device-title { font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.openccu-device-sub { margin:5px 0 0 19px; opacity:.68; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.openccu-led { width:10px; height:10px; border-radius:50%; flex:0 0 10px; background:#868e96; box-shadow:0 0 0 2px rgba(134,142,150,.18); }
.openccu-led.online { background:#2f9e44; box-shadow:0 0 0 2px rgba(47,158,68,.18); }
.openccu-led.offline { background:#e03131; box-shadow:0 0 0 2px rgba(224,49,49,.18); }
.openccu-detail-scroll { min-height:0; flex:1 1 auto; overflow-y:auto; overflow-x:hidden; padding-right:4px; }
.openccu-placeholder { min-height:420px; display:flex; align-items:center; justify-content:center; text-align:center; }
.openccu-kv { display:grid; grid-template-columns:145px minmax(0,1fr); gap:9px 16px; margin:14px 0 20px; }
.openccu-kv b { font-weight:700; }
.openccu-kv span { overflow-wrap:anywhere; }
.openccu-section { margin-top:22px; }
.openccu-channel { border:1px solid var(--border-color,#3a414f); border-radius:9px; margin:0 0 10px; overflow:hidden; }
.openccu-channel-head { padding:10px 12px; background:rgba(127,127,127,.08); display:flex; justify-content:space-between; gap:12px; align-items:center; }
.openccu-channel-title { font-weight:700; overflow-wrap:anywhere; }
.openccu-channel-meta { font-size:.82rem; opacity:.66; white-space:nowrap; }
.openccu-datapoints { padding:6px 10px 10px; }
.openccu-dp { display:grid; grid-template-columns:minmax(150px,1fr) minmax(90px,.6fr) auto; gap:10px; align-items:center; padding:9px 4px; border-bottom:1px solid rgba(127,127,127,.15); }
.openccu-dp:last-child { border-bottom:0; }
.openccu-dp-name { min-width:0; }
.openccu-dp-topic { opacity:.58; font-size:.78rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.openccu-dp-value { font-family:monospace; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; text-align:right; }
.openccu-actions { display:flex; gap:7px; justify-content:flex-end; flex-wrap:wrap; }
.openccu-actions button { padding:7px 10px; }
.status-dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:7px; background:#868e96; }
.status-dot.connected,.status-dot.ready { background:#2f9e44; } .status-dot.error { background:#e03131; } .status-dot.reconnecting,.status-dot.connecting,.status-dot.loading { background:#f08c00; }
@media(max-width:1100px) { .openccu-diagnostics { grid-template-columns:repeat(2,minmax(120px,1fr)); } }
@media(max-width:850px) { .openccu-shell { height:auto; overflow:visible; } .openccu-grid { grid-template-columns:1fr; overflow:visible; } .openccu-list-card { height:520px; } .openccu-detail-card { height:auto; min-height:520px; } }
</style>
<div class="openccu-shell">
  <div class="card compact-card openccu-toolbar">
    <div class="openccu-head">
      <div>
        <h1>OpenCCU Explorer</h1>
        <p class="small">Geräte und Kanäle aus der XML-API, Livewerte direkt über CCU-Jack MQTT.</p>
        <div class="openccu-statusline small">
          <span><span id="mqttDot" class="status-dot"></span><b id="mqttText">MQTT wird geprüft …</b></span>
          <span><span id="xmlDot" class="status-dot"></span><b id="xmlText">Geräte werden geladen …</b></span>
        </div>
        <div class="openccu-diagnostics">
          <div class="openccu-diag"><div class="openccu-diag-label">XML-API</div><div id="diagXml" class="openccu-diag-value">–</div></div>
          <div class="openccu-diag"><div class="openccu-diag-label">MQTT</div><div id="diagMqtt" class="openccu-diag-value">–</div></div>
          <div class="openccu-diag"><div class="openccu-diag-label">Geräte / Kanäle</div><div id="diagCatalog" class="openccu-diag-value">0 / 0</div></div>
          <div class="openccu-diag"><div class="openccu-diag-label">Topics</div><div id="diagTopics" class="openccu-diag-value">0</div></div>
          <div class="openccu-diag"><div class="openccu-diag-label">Letzte Nachricht</div><div id="diagLast" class="openccu-diag-value">–</div></div>
        </div>
      </div>
      <div class="button-row">
        <button type="button" id="refreshDevices">Geräte aktualisieren</button>
        <button type="button" id="reconnectMqtt">MQTT neu verbinden</button>
        <a class="button-link" href="/openccu_settings_embed">Verbindung konfigurieren</a>
      </div>
    </div>
  </div>
  <div class="openccu-grid">
    <div class="card openccu-list-card">
      <div class="openccu-list-head">
        <h2 class="section-title">Geräte</h2>
        <input id="deviceSearch" placeholder="Gerät suchen …" autocomplete="off">
      </div>
      <div id="deviceList" class="openccu-items"></div>
    </div>
    <div class="card openccu-detail-card">
      <div id="deviceDetail" class="openccu-detail-scroll">
        <div class="openccu-placeholder"><div><h2>Gerät auswählen</h2><p class="small">Rechts bleiben Gerätedetails, Kanäle und Live-Datenpunkte sichtbar.</p></div></div>
      </div>
    </div>
  </div>
</div>
<script>
(() => {
  const listEl = document.getElementById('deviceList');
  const detailEl = document.getElementById('deviceDetail');
  const searchEl = document.getElementById('deviceSearch');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let devices = [];
  let selectedAddress = '';
  let lastDetailSignature = '';

  const displayValue = value => typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '');
  const inferDatatype = entry => entry && entry.value_type === 'number' ? 'number' : entry && entry.value_type === 'bool' ? 'bool' : 'auto';
  const datapointLabels = {
    PRESENCE_DETECTION_STATE:'Presence', PRESENCE:'Presence', MOTION:'Bewegung',
    STATE:'Status', LOWBAT:'Batterie schwach', LOW_BAT:'Batterie schwach',
    TEMPERATURE:'Temperatur', ACTUAL_TEMPERATURE:'Temperatur', HUMIDITY:'Luftfeuchtigkeit',
    ILLUMINATION:'Helligkeit', BRIGHTNESS:'Helligkeit', CONTACT:'Kontakt', LEVEL:'Wert'
  };
  const datapointLabel = value => {
    const raw = String(value || '').trim();
    if (!raw) return '';
    const key = raw.toUpperCase();
    return datapointLabels[key] || raw.toLowerCase().replace(/(^|_)([a-z])/g, (_, __, ch) => (ch ? ' ' + ch.toUpperCase() : '')).trim();
  };
  const objectName = (device, entry) => [device.name, datapointLabel(entry.datapoint)].filter(Boolean).join(' · ');
  const navigate = url => {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({type:'mqtt2lox:navigateFrame', url, activeHref:'/objects_v33'}, window.location.origin);
    } else window.location.href = url;
  };
  const objectUrl = (device, entry, mode) => {
    const params = new URLSearchParams({
      explorer:'openccu', source:'openccu', source_type:'openccu', source_adapter:'mqtt', tab:'mqtt',
      name:objectName(device,entry), suggested_name:objectName(device,entry), topic:entry.topic,
      source_topic:entry.topic, datatype:inferDatatype(entry), value:displayValue(entry.value),
      openccu_device:device.address, openccu_channel:entry.channel_address, openccu_datapoint:entry.datapoint, origin_source:'openccu',
      explorer_action:mode || 'create'
    });
    return '/objects_v33/create_from_explorer?' + params.toString();
  };

  function renderList() {
    const q = searchEl.value.trim().toLowerCase();
    const visible = devices.filter(d => !q || [d.name,d.address,d.device_type,d.interface].join(' ').toLowerCase().includes(q));
    if (!visible.length) {
      listEl.innerHTML = '<div class="small" style="padding:18px 4px;">Keine passenden Geräte gefunden.</div>';
      return;
    }
    listEl.innerHTML = visible.map(d => `<button class="openccu-device ${d.address===selectedAddress?'active':''}" data-address="${esc(d.address)}"><div class="openccu-device-row"><span class="openccu-led ${d.online?'online':'offline'}"></span><span class="openccu-device-title">${esc(d.name || d.address)}</span></div><div class="openccu-device-sub small">${esc([d.device_type,d.address].filter(Boolean).join(' · '))}</div></button>`).join('');
    listEl.querySelectorAll('.openccu-device').forEach(btn => btn.addEventListener('click', () => {
      selectedAddress = btn.dataset.address;
      lastDetailSignature = '';
      renderList(); renderDetail();
    }));
  }

  function renderDetail() {
    const device = devices.find(d => d.address === selectedAddress);
    if (!device) {
      detailEl.innerHTML = '<div class="openccu-placeholder"><div><h2>Gerät auswählen</h2><p class="small">Rechts bleiben Gerätedetails, Kanäle und Live-Datenpunkte sichtbar.</p></div></div>';
      return;
    }
    const signature = JSON.stringify([device.address,device.online,device.last_update,(device.live_datapoints||[]).map(e=>[e.topic,e.value,e.updated_at])]);
    if (signature === lastDetailSignature) return;
    lastDetailSignature = signature;
    const live = device.live_datapoints || [];
    const liveByChannel = {};
    live.forEach(entry => (liveByChannel[entry.channel_address] ||= []).push(entry));
    const channels = device.channels || [];
    const channelHtml = channels.map(channel => {
      const points = liveByChannel[channel.address] || [];
      const pointHtml = points.length ? points.map(entry => `<div class="openccu-dp"><div class="openccu-dp-name"><b>${esc(entry.datapoint)}</b><div class="openccu-dp-topic">${esc(entry.topic)}</div></div><div class="openccu-dp-value">${esc(displayValue(entry.value))}</div><div class="openccu-actions"><button type="button" class="create-object" data-topic="${esc(entry.topic)}">Objekt erstellen</button></div></div>`).join('') : '<div class="small" style="padding:12px 4px;">Noch keine Live-Datenpunkte für diesen Kanal empfangen.</div>';
      return `<div class="openccu-channel"><div class="openccu-channel-head"><div class="openccu-channel-title">${esc(channel.name || channel.address)}</div><div class="openccu-channel-meta">${esc(channel.type || 'Kanal')} · ${esc(channel.address)}</div></div><div class="openccu-datapoints">${pointHtml}</div></div>`;
    }).join('');
    const orphan = live.filter(entry => !channels.some(ch => ch.address === entry.channel_address));
    const orphanHtml = orphan.length ? `<div class="openccu-channel"><div class="openccu-channel-head"><div class="openccu-channel-title">Weitere Live-Datenpunkte</div></div><div class="openccu-datapoints">${orphan.map(entry => `<div class="openccu-dp"><div class="openccu-dp-name"><b>${esc(entry.datapoint)}</b><div class="openccu-dp-topic">${esc(entry.topic)}</div></div><div class="openccu-dp-value">${esc(displayValue(entry.value))}</div><div class="openccu-actions"><button type="button" class="create-object" data-topic="${esc(entry.topic)}">Objekt erstellen</button></div></div>`).join('')}</div></div>` : '';
    detailEl.innerHTML = `<h2 class="section-title">${esc(device.name || device.address)}</h2><div class="openccu-kv"><b>Status</b><span>${device.online?'Online':'Offline'}</span><b>Seriennummer</b><span>${esc(device.address)}</span><b>Gerätetyp</b><span>${esc(device.device_type || '–')}</span><b>Interface</b><span>${esc(device.interface || '–')}</span><b>ISE-ID</b><span>${esc(device.ise_id || '–')}</span><b>Kanäle</b><span>${channels.length}</span><b>Letzter Livewert</b><span>${esc(device.last_update || '–')}</span></div><div class="openccu-section"><h3>Kanäle und Live-Datenpunkte</h3>${channelHtml || '<div class="small">Keine Kanäle in der XML-API gefunden.</div>'}${orphanHtml}</div>`;
    const entriesByTopic = Object.fromEntries(live.map(entry => [entry.topic, entry]));
    detailEl.querySelectorAll('.create-object').forEach(btn => btn.addEventListener('click', () => navigate(objectUrl(device, entriesByTopic[btn.dataset.topic], 'create'))));
  }

  async function refresh() {
    try {
      const response = await fetch('/api/openccu/discovery', {cache:'no-store'});
      const data = await response.json();
      devices = Array.isArray(data.devices) ? data.devices : [];
      const status = data.status || {};
      document.getElementById('mqttDot').className = 'status-dot ' + (status.state || '');
      document.getElementById('mqttText').textContent = status.message || 'MQTT-Status unbekannt';
      const meta = data.metadata_status || {};
      document.getElementById('xmlDot').className = 'status-dot ' + (meta.state || '');
      document.getElementById('xmlText').textContent = meta.last_error ? `${meta.message}: ${meta.last_error}` : (meta.message || `${devices.length} Geräte geladen`);
      document.getElementById('diagXml').textContent = meta.state === 'ready' ? 'erreichbar' : (meta.state || 'unbekannt');
      document.getElementById('diagMqtt').textContent = status.connected ? `${status.host || 'Broker'}:${status.port || 1883}` : (status.state || 'getrennt');
      document.getElementById('diagCatalog').textContent = `${meta.device_count ?? devices.length} / ${meta.channel_count ?? 0}`;
      document.getElementById('diagTopics').textContent = `${status.unique_topics || 0}`;
      document.getElementById('diagLast').textContent = status.last_message || 'noch keine';
      if (selectedAddress && !devices.some(d => d.address === selectedAddress)) selectedAddress = '';
      renderList(); renderDetail();
    } catch (error) {
      document.getElementById('mqttDot').className='status-dot error';
      document.getElementById('mqttText').textContent='Explorer-API nicht erreichbar';
    }
  }
  searchEl.addEventListener('input', renderList);
  document.getElementById('refreshDevices').addEventListener('click', async () => { await fetch('/api/openccu/metadata/refresh',{method:'POST'}); refresh(); });
  document.getElementById('reconnectMqtt').addEventListener('click', async () => { await fetch('/api/openccu/reconnect',{method:'POST'}); refresh(); });
  refresh(); setInterval(refresh,1000);
})();
</script>
"""
    return _core().embedded_page("OpenCCU Explorer", content)
