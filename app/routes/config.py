"""Config routes.

These routes delegate to the app core handlers during the migration.
"""

from flask import Blueprint, current_app, redirect, request
from markupsafe import escape

from app.services.system_admin import set_ssh_root_password, ssh_root_password_status


bp = Blueprint("config", __name__)


def _core():
    return current_app.extensions["app_core"]


@bp.route("/settings")
def settings_page():
    return _core().settings_page()


@bp.route("/settings_embed")
def settings_embed():
    return _core().settings_embed()


@bp.route("/core_settings_embed")
def core_settings_embed():
    return _core().core_settings_embed()


@bp.route("/mqtt_settings_embed")
def mqtt_settings_embed():
    return _core().mqtt_settings_embed()


@bp.route("/influx_settings_embed")
def influx_settings_embed():
    return _core().influx_settings_embed()


@bp.route("/save", methods=["POST"])
def save():
    return _core().save()


@bp.route("/save_core", methods=["POST"])
def save_core():
    return _core().save_core()


@bp.route("/save_mqtt", methods=["POST"])
def save_mqtt():
    return _core().save_mqtt()


@bp.route("/save_influx", methods=["POST"])
def save_influx():
    return _core().save_influx()


@bp.route("/sidebar_links/save", methods=["POST"])
def sidebar_links_save():
    return _core().sidebar_links_save()


def _system_settings_content(notice: str = ""):
    status = ssh_root_password_status()
    available = bool(status.get("available"))
    enabled = bool(status.get("enabled"))
    password_set = bool(status.get("password_set"))
    state = "aktiv" if enabled else "aus"
    if not available:
        state = "nicht verfügbar"
    password_note = (
        "Für root ist ein Passwort gesetzt."
        if password_set
        else "Für root ist noch kein Passwort gesetzt. Das erledigst du im LXC einmal mit <code>passwd root</code>."
    )
    disabled = "" if available else "disabled"
    checked = "checked" if enabled else ""
    warning = ""
    if enabled:
        warning = '<div class="notice warning"><b>Sicherheit:</b> Root-Login per Passwort ist aktiv. Nur in einem vertrauenswürdigen internen Netz verwenden.</div>'
    return f"""
{notice}
{warning}
<div class="card">
  <h2 class="section-title">Debian / LXC-System</h2>
  <p class="small">Diese Funktionen sind nur bei der offiziellen Debian-13-LXC-Installation verfügbar.</p>
  <table>
    <tr><th>Funktion</th><th>Status</th><th>Hinweis</th></tr>
    <tr><td>Root-Login per SSH-Passwort</td><td><b>{escape(state)}</b></td><td>{password_note}</td></tr>
  </table>
</div>
<form method="post" action="/system_settings/ssh-root-password" onsubmit="return confirmSshRootPassword(this)">
  <div class="card">
    <h2 class="section-title">SSH-Zugriff</h2>
    <label class="switch-row">
      <input type="checkbox" name="enabled" value="1" {checked} {disabled}>
      <span>Root-Login per SSH-Passwort erlauben</span>
    </label>
    <p class="small">Beim Ausschalten wird der Passwortzugriff für root gesperrt. SSH-Schlüssel bleiben weiterhin erlaubt.</p>
    <input type="hidden" name="confirm_enable" value="">
    <div class="button-row" style="margin-top:14px;"><button type="submit" {disabled}>Übernehmen</button></div>
  </div>
</form>
<script>
function confirmSshRootPassword(form) {{
  const enabled = form.querySelector('input[name="enabled"]').checked;
  if (!enabled) return confirm('Root-Login per SSH-Passwort wirklich deaktivieren? SSH-Schlüssel bleiben erlaubt.');
  const ok = confirm('ACHTUNG: Root-Login per Passwort erhöht das Angriffsrisiko. Nur im vertrauenswürdigen internen Netz aktivieren. Fortfahren?');
  if (ok) form.querySelector('input[name="confirm_enable"]').value = 'YES';
  return ok;
}}
</script>
"""


@bp.get("/system_settings_embed")
def system_settings_embed():
    return _core().embedded_page("Debian / LXC-System", _system_settings_content())


@bp.post("/system_settings/ssh-root-password")
def system_settings_ssh_root_password():
    enabled = request.form.get("enabled") == "1"
    if enabled and request.form.get("confirm_enable") != "YES":
        notice = '<div class="notice error">Aktivierung wurde nicht bestätigt.</div>'
        return _core().embedded_page("Debian / LXC-System", _system_settings_content(notice)), 400
    result = set_ssh_root_password(enabled)
    css = "success" if result.get("ok") else "error"
    message = escape(str(result.get("message") or "Aktion abgeschlossen"))
    notice = f'<div class="notice {css}">{message}</div>'
    code = 200 if result.get("ok") else 500
    return _core().embedded_page("Debian / LXC-System", _system_settings_content(notice)), code


@bp.route("/plugins")
def plugins_page():
    return _core().plugins_page()


@bp.route("/plugins/save", methods=["POST"])
def save_plugins():
    return _core().save_plugins()
