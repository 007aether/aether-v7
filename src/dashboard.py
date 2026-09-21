"""AETHER v7 — Web Dashboard"""
from flask import Flask, jsonify, render_template_string
from .config import DASHBOARD_PORT
from .db import connect_memory, connect_earnings
from .utils import ts_human

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>AETHER v7</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
body{font-family:system-ui,Tahoma,sans-serif;background:#0a0e1a;color:#00ffaa;
     margin:0;padding:20px;min-height:100vh}
h1{text-align:center;letter-spacing:6px;color:#00ffaa;text-shadow:0 0 20px #00ffaa88}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
      gap:16px;max-width:1400px;margin:0 auto}
.card{background:rgba(0,255,170,.05);border:1px solid #00ffaa44;
      border-radius:10px;padding:18px;box-shadow:0 0 20px #00ffaa22}
.card h2{margin:0 0 10px;font-size:12px;color:#00ffaa99;
         letter-spacing:2px;text-transform:uppercase}
.val{font-size:32px;font-weight:bold;color:#00ffaa}
.small{font-size:11px;color:#00ffaa88;margin-top:6px}
.row{display:flex;justify-content:space-between;padding:5px 0;
     border-bottom:1px solid #00ffaa11;font-size:13px}
.ok{color:#00ff88}.ko{color:#ff4466}
.footer{text-align:center;margin-top:24px;color:#00ffaa55;font-size:11px}
</style></head>
<body>
<h1>⚡ AETHER v7 ⚡</h1>
<div class="grid" id="grid">Loading...</div>
<div class="footer">Auto-refresh 5s · <span id="ts"></span></div>
<script>
async function load(){
  const r=await fetch('/api/status');const d=await r.json();
  const g=document.getElementById('grid');
  const card=(t,v,s='')=>`<div class="card"><h2>${t}</h2><div class="val">${v}</div><div class="small">${s}</div></div>`;
  let h='';
  h+=card('Cycles',d.cycles,'autonomous');
  h+=card('Events',d.events,'logged');
  h+=card('Skills',d.skills,'learned');
  h+=card('Memory',d.memory,'entries');
  h+=card('Earnings',`$${d.total_earnings.toFixed(2)}`,'total');
  h+=card('DePIN',d.depin_running,'running');
  h+=card('Tap Bots',d.tap_ready,'ready');
  let c='<div class="card"><h2>Last Cycles</h2>';
  for(const r of d.last_cycles){
    c+=`<div class="row"><span>${(r.decision||'').substring(0,50)}</span>
        <span class="${r.success?'ok':'ko'}">${r.success?'✓':'✗'}</span></div>`;
  }
  c+='</div>';h+=c;
  g.innerHTML=h;
  document.getElementById('ts').textContent=new Date().toLocaleString();
}
load();setInterval(load,5000);
</script></body></html>"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/status")
def api():
    cm = connect_memory(); ce = connect_earnings()
    try:
        data = {
            "cycles": cm.execute("SELECT COUNT(*) FROM cycles").fetchone()[0],
            "events": cm.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "skills": cm.execute("SELECT COUNT(*) FROM skills").fetchone()[0],
            "memory": cm.execute("SELECT COUNT(*) FROM memory").fetchone()[0],
            "total_earnings": cm and ce.execute(
                "SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0],
            "depin_running": ce.execute(
                "SELECT COUNT(*) FROM depin_status WHERE status='running'").fetchone()[0],
            "tap_ready": ce.execute(
                "SELECT COUNT(*) FROM tap_status WHERE status='ready'").fetchone()[0],
            "last_cycles": [
                {"decision": r[0], "success": bool(r[1])}
                for r in cm.execute(
                    "SELECT decision, success FROM cycles ORDER BY id DESC LIMIT 6"
                ).fetchall()
            ],
            "ts": ts_human(),
        }
    finally:
        cm.close(); ce.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False)
