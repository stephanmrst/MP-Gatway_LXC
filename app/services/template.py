from markupsafe import escape


def build_datalist_html(datalist_id, options):
    html = f'<datalist id="{escape(str(datalist_id))}">\n'
    for item in options:
        html += f'    <option value="{escape(str(item))}">\n'
    html += '</datalist>\n'
    return html


def render_layout(
    render_template_string,
    app_layout,
    bridge_status,
    title,
    content,
    active="dashboard",
    subtitle="",
    message="",
    app_name="MP-Gateway",
    app_subtitle="Das Multiprotokoll-Gateway",
    app_legacy_name="MQTT2Lox",
    app_version="",
    iframe_shell=False,
    sidebar_links_html="",
):
    return render_template_string(
        app_layout,
        app_name=app_name,
        app_subtitle=app_subtitle,
        app_legacy_name=app_legacy_name,
        app_version=app_version,
        title=title,
        subtitle=subtitle,
        content=content,
        active=active,
        message=message,
        status=bridge_status,
        iframe_shell=iframe_shell,
        sidebar_links_html=sidebar_links_html,
    )


def embedded_page(title, content):
    return f"""
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(str(title))}</title>
<style>
:root {{
    --bg:#202830;
    --panel:#1b2229;
    --panel2:#222b34;
    --border:#303b45;
    --text:#f4f7fb;
    --muted:#aeb8c4;
    --blue:#5f686f;
    --blue2:#727d85;
    --red:#a94a4a;
    --green:#7CFF75;
}}
* {{ box-sizing:border-box; }}
body {{
    margin:0;
    padding:22px;
    background:var(--bg);
    color:var(--text);
    font-family:Arial, sans-serif;
}}
h1 {{ margin:0 0 18px; }}
.card {{
    background:var(--panel);
    border:1px solid var(--border);
    border-radius:8px;
    padding:18px;
    margin-bottom:16px;
}}

.knx-action-table {{
    border-collapse: separate !important;
    border-spacing: 10px 8px !important;
    margin: -8px 0 !important;
    background: transparent !important;
    width: auto !important;
}}

.knx-action-table td {{
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    vertical-align: middle !important;
}}

.knx-action-table a,
.knx-action-table button {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    white-space: nowrap !important;
    line-height: 1 !important;
    height: 28px !important;
    min-width: 88px !important;
    padding: 0 10px !important;
    box-sizing: border-box !important;
}}

td.actions,
th.actions,
.knx-monitor-table td.actions {{
    min-width: 230px !important;
    width: 230px !important;
    vertical-align: middle !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:14px; }}
.dashboard-grid {{ grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); }}
.system-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:4px 28px; }}
.compact-card {{ padding:10px 18px; margin-bottom:14px; }}
.compact-card .section-title {{ margin:0 0 8px; font-size:22px; }}
.compact-card .muted {{ line-height:1.1; }}
.compact-card b {{ line-height:1.05; }}
.dashboard-tile {{
    display:block;
    color:var(--text);
    text-decoration:none;
    min-height:116px;
    transition:.12s ease;
}}
.dashboard-tile:hover {{
    background:var(--panel2);
    border-color:#53606d;
    transform:translateY(-1px);
}}
.stat-value {{ font-size:24px; font-weight:800; margin-top:6px; }}
.muted {{ color:var(--muted); }}
.small {{ color:var(--muted); font-size:13px; }}
.ok {{ color:var(--green); }}
.bad {{ color:#ff8a8a; }}
button, .button-link, a.button-link {{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-height:32px;
    padding:0 14px;
    border:0;
    border-radius:4px;
    background:var(--blue);
    color:white;
    cursor:pointer;
    text-decoration:none;
    font-family:Arial, sans-serif;
    font-size:14px;
    font-weight:700;
}}
button:hover, .button-link:hover {{ background:var(--blue2); }}
.stop {{ background:var(--red); }}
.button-row {{ display:flex; gap:9px; flex-wrap:wrap; align-items:center; }}
input, select {{
    width:100%;
    padding:8px;
    border-radius:5px;
    border:1px solid #4a5663;
    background:#111820;
    color:white;
}}
input[type=checkbox] {{ width:auto; }}
label {{ display:block; margin-top:11px; margin-bottom:5px; }}
table {{ width:100%; border-collapse:collapse; background:#151c23; }}
th, td {{ border:1px solid var(--border); padding:7px; }}
th {{ background:#2a333d; }}
</style>
</head>
<body>
{content}
</body>
</html>
"""


def build_select_options(options, selected=""):
    selected = str(selected or "")
    html = ""
    for val, label in options:
        html += f'<option value="{escape(val)}" {"selected" if selected == val else ""}>{escape(label)}</option>'
    return html


def build_select_html(name, options, selected=""):
    return f'<select name="{escape(name)}">{build_select_options(options, selected)}</select>'
