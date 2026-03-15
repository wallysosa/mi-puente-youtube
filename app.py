import os
import json
import requests
from flask import Flask, Response, request

app = Flask(__name__)

GITHUB_USER  = os.environ.get('GITHUB_USER',  'wallysosa')
GITHUB_REPO  = os.environ.get('GITHUB_REPO',  'mi-puente-youtube')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
JSON_URL     = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/streams/canales.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"

def get_canales():
    hdrs = {}
    if GITHUB_TOKEN:
        hdrs['Authorization'] = f'token {GITHUB_TOKEN}'
    r = requests.get(JSON_URL, headers=hdrs, timeout=15)
    r.raise_for_status()
    return r.json()

@app.route('/')
def home():
    return '''<h2>📺 Canales Latinos</h2>
    <ul>
      <li><a href="/player">🎬 Reproductor Web</a></li>
      <li><a href="/canales.m3u">📋 Lista M3U (VLC/OTT/TiviMate)</a></li>
      <li><a href="/canales.json">📄 JSON</a></li>
    </ul>'''

@app.route('/canales.json')
def canales_json():
    try:
        canales = get_canales()
        return Response(json.dumps(canales, ensure_ascii=False, indent=2),
                        mimetype='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})
    except Exception as e:
        return f"Error: {e}", 502

@app.route('/canales.m3u')
def canales_m3u():
    try:
        canales = get_canales()
    except Exception as e:
        return f"Error: {e}", 502

    lineas = ["#EXTM3U"]
    for c in canales:
        if not c.get('stream'):
            continue
        lineas.append(f'#EXTINF:-1 tvg-logo="{c["logo"]}" tvg-country="{c["pais"]}" group-title="{c["grupo"]}", {c["nombre"]}')
        lineas.append(f'#EXTVLCOPT:http-user-agent={UA}')
        lineas.append(c['stream'])

    return Response("\n".join(lineas), mimetype='application/x-mpegurl')

@app.route('/player')
def player():
    return '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📺 Canales Latinos</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/hls.js/1.4.10/hls.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f0f; color: #fff; font-family: sans-serif; display: flex; height: 100vh; }
  #sidebar { width: 280px; background: #1a1a1a; overflow-y: auto; border-right: 1px solid #333; }
  #sidebar h2 { padding: 15px; background: #e50914; font-size: 16px; }
  .canal { display: flex; align-items: center; padding: 10px 15px; cursor: pointer; border-bottom: 1px solid #2a2a2a; transition: background 0.2s; }
  .canal:hover { background: #2a2a2a; }
  .canal.activo { background: #333; border-left: 3px solid #e50914; }
  .canal img { width: 40px; height: 40px; object-fit: contain; margin-right: 10px; border-radius: 5px; background: #333; }
  .canal-info { flex: 1; }
  .canal-nombre { font-size: 13px; font-weight: bold; }
  .canal-grupo { font-size: 11px; color: #888; margin-top: 2px; }
  .canal-estado { font-size: 10px; margin-top: 2px; }
  .estado-ok { color: #4caf50; }
  .estado-err { color: #f44336; }
  #main { flex: 1; display: flex; flex-direction: column; }
  #video-container { flex: 1; background: #000; position: relative; }
  video { width: 100%; height: 100%; }
  #info-bar { padding: 10px 20px; background: #1a1a1a; display: flex; align-items: center; gap: 15px; border-top: 1px solid #333; }
  #canal-actual { font-size: 15px; font-weight: bold; }
  #btn-m3u { background: #e50914; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-size: 13px; text-decoration: none; }
  #btn-m3u:hover { background: #c0070f; }
  #mensaje { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); text-align: center; color: #888; }
  #grupo-filter { padding: 10px 15px; }
  #grupo-filter select { width: 100%; padding: 6px; background: #333; color: #fff; border: 1px solid #444; border-radius: 4px; }
</style>
</head>
<body>
<div id="sidebar">
  <h2>📺 Canales Latinos</h2>
  <div id="grupo-filter">
    <select id="select-grupo" onchange="filtrarGrupo()">
      <option value="">Todos los grupos</option>
    </select>
  </div>
  <div id="lista-canales"></div>
</div>
<div id="main">
  <div id="video-container">
    <video id="video" controls autoplay></video>
    <div id="mensaje">← Seleccioná un canal</div>
  </div>
  <div id="info-bar">
    <span id="canal-actual">Ningún canal seleccionado</span>
    <a id="btn-m3u" href="/canales.m3u" download="canales.m3u">⬇ Descargar M3U</a>
  </div>
</div>
<script>
let hls = null;
let canales = [];

async function cargarCanales() {
  const lista = document.getElementById('lista-canales');
  lista.innerHTML = '<div style="padding:20px;color:#888">Cargando canales...</div>';
  try {
    const r = await fetch('/canales.json');
    canales = await r.json();
    poblarFiltro();
    renderCanales(canales);
  } catch(e) {
    lista.innerHTML = '<div style="padding:20px;color:#f44336">Error cargando canales</div>';
  }
}

function poblarFiltro() {
  const grupos = [...new Set(canales.map(c => c.grupo))];
  const sel = document.getElementById('select-grupo');
  grupos.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g; opt.textContent = g;
    sel.appendChild(opt);
  });
}

function filtrarGrupo() {
  const grupo = document.getElementById('select-grupo').value;
  const filtrados = grupo ? canales.filter(c => c.grupo === grupo) : canales;
  renderCanales(filtrados);
}

function renderCanales(lista) {
  const div = document.getElementById('lista-canales');
  div.innerHTML = '';
  lista.forEach((c, i) => {
    const el = document.createElement('div');
    el.className = 'canal';
    el.id = 'canal-' + i;
    const estado = c.stream
      ? '<span class="canal-estado estado-ok">● En vivo</span>'
      : '<span class="canal-estado estado-err">● Sin stream</span>';
    el.innerHTML = `
      <img src="${c.logo}" onerror="this.src=''" alt="${c.nombre}">
      <div class="canal-info">
        <div class="canal-nombre">${c.nombre}</div>
        <div class="canal-grupo">${c.grupo} · ${c.pais}</div>
        ${estado}
      </div>`;
    if (c.stream) el.onclick = () => reproducir(c, el);
    else el.style.opacity = '0.4';
    div.appendChild(el);
  });
}

function reproducir(canal, el) {
  document.querySelectorAll('.canal').forEach(e => e.classList.remove('activo'));
  el.classList.add('activo');
  document.getElementById('canal-actual').textContent = '▶ ' + canal.nombre;
  document.getElementById('mensaje').style.display = 'none';

  const video = document.getElementById('video');
  if (hls) { hls.destroy(); hls = null; }

  if (Hls.isSupported()) {
    hls = new Hls();
    hls.loadSource(canal.stream);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = canal.stream;
    video.play();
  }
}

cargarCanales();
</script>
</body>
</html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
