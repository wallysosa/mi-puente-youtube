const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36';

// ── Lista de canales DAI ─────────────────────────────────────────────────────
const CANALES = [
  { nombre: 'TN - Todo Noticias', pais: 'AR', grupo: 'Argentina', logo: 'https://graph.facebook.com/todonoticias/picture?width=200&height=200',  dai: '5OEEtA9FR-yrvhNE5K8PQQ' },
  { nombre: 'Azteca 7',           pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/aztecasiete/picture?width=200&height=200',   dai: 'YHoOj51dSKCvBQOBG2OvLQ' },
  { nombre: 'a mas',              pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/amastv/picture?width=200&height=200',         dai: 'SJysMl45QMSwjo0TodSk1Q' },
  { nombre: 'DW Espanol',         pais: 'DE', grupo: 'Internacional', logo: 'https://graph.facebook.com/dw.espanol/picture?width=200&height=200', stream: 'https://dwamdstream104.akamaized.net/hls/live/2015530/dwstream104/stream04/streamPlaylist.m3u8' },
  { nombre: 'NHK World',          pais: 'JP', grupo: 'Internacional', logo: 'https://graph.facebook.com/NHKWorldTV/picture?width=200&height=200', stream: 'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index_1M.m3u8' },
];

const BASE_URL = process.env.MY_APP_URL || 'https://mi-puente-youtube.onrender.com';

// ── Helpers ──────────────────────────────────────────────────────────────────
function daiUrl(daiId) {
  return `https://dai.google.com/linear/hls/event/${daiId}/master.m3u8`;
}

function streamUrl(canal) {
  if (canal.dai) return `${BASE_URL}/dai/${canal.dai}`;
  return canal.stream;
}

// ── Rutas ────────────────────────────────────────────────────────────────────

// Ping para cron-job (mantener despierto)
app.get('/ping', (req, res) => res.send('OK'));

// Home
app.get('/', (req, res) => {
  res.send(`
    <h2>📺 Canales Latinos</h2>
    <ul>
      <li><a href="/player">🎬 Reproductor Web</a></li>
      <li><a href="/canales.m3u">📋 Lista M3U para VLC/OTT</a></li>
      <li><a href="/canales.json">📄 JSON</a></li>
      <li><a href="/ping">🏓 Ping</a></li>
    </ul>
  `);
});

// JSON con lista de canales
app.get('/canales.json', (req, res) => {
  const data = CANALES.map(c => ({
    nombre: c.nombre,
    pais:   c.pais,
    grupo:  c.grupo,
    logo:   c.logo,
    stream: streamUrl(c)
  }));
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json(data);
});

// M3U para VLC/OTT/TiviMate
app.get('/canales.m3u', (req, res) => {
  let m3u = '#EXTM3U\n';
  for (const c of CANALES) {
    const url = streamUrl(c);
    if (!url) continue;
    m3u += `#EXTINF:-1 tvg-logo="${c.logo}" tvg-country="${c.pais}" group-title="${c.grupo}", ${c.nombre}\n`;
    m3u += `#EXTVLCOPT:http-user-agent=${UA}\n`;
    m3u += `${url}\n`;
  }
  res.setHeader('Content-Type', 'application/x-mpegurl');
  res.send(m3u);
});

// Proxy DAI — renueva la URL automáticamente
app.use('/dai/:daiId', (req, res, next) => {
  const daiId  = req.params.daiId.replace('#', '').replace('.m3u8', '');
  const target = daiUrl(daiId);

  createProxyMiddleware({
    target:       'https://dai.google.com',
    changeOrigin: true,
    followRedirects: true,
    pathRewrite:  () => `/linear/hls/event/${daiId}/master.m3u8`,
    on: {
      proxyRes: (proxyRes) => {
        proxyRes.headers['access-control-allow-origin'] = '*';
      },
      error: (err, req, res) => {
        res.status(502).send(`Error proxy DAI: ${err.message}`);
      }
    }
  })(req, res, next);
});

// Reproductor HTML
app.get('/player', (req, res) => {
  res.send(`<!DOCTYPE html>
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
  .canal:hover, .canal.activo { background: #2a2a2a; border-left: 3px solid #e50914; }
  .canal img { width: 40px; height: 40px; object-fit: contain; margin-right: 10px; border-radius: 5px; background: #333; }
  .canal-nombre { font-size: 13px; font-weight: bold; }
  .canal-grupo  { font-size: 11px; color: #888; margin-top: 2px; }
  #main { flex: 1; display: flex; flex-direction: column; }
  video { flex: 1; width: 100%; background: #000; }
  #info-bar { padding: 10px 20px; background: #1a1a1a; display: flex; align-items: center; gap: 15px; border-top: 1px solid #333; }
  #canal-actual { font-size: 15px; font-weight: bold; flex: 1; }
  a.btn { background: #e50914; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-size: 13px; text-decoration: none; }
  a.btn:hover { background: #c0070f; }
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
  <div id="lista"></div>
</div>
<div id="main">
  <video id="video" controls autoplay></video>
  <div id="info-bar">
    <span id="canal-actual">← Seleccioná un canal</span>
    <a class="btn" href="/canales.m3u" download="canales.m3u">⬇ Descargar M3U</a>
  </div>
</div>
<script>
let hls = null, canales = [];

async function init() {
  const r = await fetch('/canales.json');
  canales = await r.json();
  const grupos = [...new Set(canales.map(c => c.grupo))];
  const sel = document.getElementById('select-grupo');
  grupos.forEach(g => { const o = document.createElement('option'); o.value = g; o.textContent = g; sel.appendChild(o); });
  render(canales);
}

function filtrarGrupo() {
  const g = document.getElementById('select-grupo').value;
  render(g ? canales.filter(c => c.grupo === g) : canales);
}

function render(lista) {
  const div = document.getElementById('lista');
  div.innerHTML = '';
  lista.forEach(c => {
    const el = document.createElement('div');
    el.className = 'canal';
    el.innerHTML = \`<img src="\${c.logo}" onerror="this.src=''" alt="">
      <div><div class="canal-nombre">\${c.nombre}</div><div class="canal-grupo">\${c.grupo} · \${c.pais}</div></div>\`;
    el.onclick = () => play(c, el);
    div.appendChild(el);
  });
}

function play(canal, el) {
  document.querySelectorAll('.canal').forEach(e => e.classList.remove('activo'));
  el.classList.add('activo');
  document.getElementById('canal-actual').textContent = '▶ ' + canal.nombre;
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

init();
</script>
</body>
</html>`);
});

// ── Iniciar servidor ─────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Servidor corriendo en puerto ${PORT}`));
