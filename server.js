const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

// ── CONFIGURACIÓN DE URL ─────────────────────────────────────────────────────
const BASE_URL = process.env.RENDER_EXTERNAL_URL || 'https://mi-puente-youtube.onrender.com';

// ── LISTA DE CANALES ─────────────────────────────────────────────────────────
const CANALES = [
  { nombre: 'TN - Todo Noticias', pais: 'AR', grupo: 'Argentina', logo: 'https://graph.facebook.com/todonoticias/picture?width=200&height=200', dai: '5OEEtA9FR-yrvhNE5K8PQQ' },
  { nombre: 'Azteca 7',           pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/aztecasiete/picture?width=200&height=200',   dai: 'YHoOj51dSKCvBQOBG2OvLQ' },
  { nombre: 'a mas',              pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/amastv/picture?width=200&height=200',        dai: 'SJysMl45QMSwjo0TodSk1Q' },
  { nombre: 'DW Espanol',         pais: 'DE', grupo: 'Internacional', logo: 'https://graph.facebook.com/dw.espanol/picture?width=200&height=200', stream: 'https://dwamdstream104.akamaized.net/hls/live/2015530/dwstream104/stream04/streamPlaylist.m3u8' },
  { nombre: 'NHK World',          pais: 'JP', grupo: 'Internacional', logo: 'https://graph.facebook.com/NHKWorldTV/picture?width=200&height=200', stream: 'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index_1M.m3u8' },
];

// ── HELPERS ──────────────────────────────────────────────────────────────────
function streamUrl(canal) {
  if (canal.dai) return `${BASE_URL}/dai/${canal.dai}.m3u8`;
  return canal.stream;
}

// ── RUTAS ────────────────────────────────────────────────────────────────────

// Ping para cron-job
app.get('/ping', (req, res) => res.send('OK'));

// Home
app.get('/', (req, res) => {
  res.send(`
    <body style="background:#0f0f0f; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
      <h1 style="color:#e50914;">📺 Canales Latinos</h1>
      <div style="margin-top:20px;">
        <a href="/player" style="display:inline-block; background:#e50914; color:white; padding:12px 24px; text-decoration:none; border-radius:5px; margin:10px;">🎬 Reproductor Web</a>
        <a href="/canales.m3u" style="display:inline-block; background:#333; color:white; padding:12px 24px; text-decoration:none; border-radius:5px; margin:10px;">📋 Descargar M3U</a>
      </div>
    </body>
  `);
});

// JSON de Canales
app.get('/canales.json', (req, res) => {
  const data = CANALES.map(c => ({ ...c, stream: streamUrl(c) }));
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json(data);
});

// Lista M3U
app.get('/canales.m3u', (req, res) => {
  let m3u = '#EXTM3U\n';
  CANALES.forEach(c => {
    const url = streamUrl(c);
    m3u += `#EXTINF:-1 tvg-logo="${c.logo}" tvg-country="${c.pais}" group-title="${c.grupo}", ${c.nombre}\n`;
    m3u += `#EXTVLCOPT:http-user-agent=${UA}\n${url}\n`;
  });
  res.setHeader('Content-Type', 'application/x-mpegurl');
  res.send(m3u);
});

// Proxy DAI
app.use('/dai/:daiId', (req, res, next) => {
  const daiId = req.params.daiId.replace('.m3u8', '');
  createProxyMiddleware({
    target: 'https://dai.google.com',
    changeOrigin: true,
    pathRewrite: () => `/linear/hls/event/${daiId}/master.m3u8`,
    on: {
      proxyRes: (pRes) => {
        pRes.headers['Access-Control-Allow-Origin'] = '*';
        delete pRes.headers['content-security-policy'];
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reproductor Canales</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/hls.js/1.4.10/hls.min.js"></script>
    <style>
        body { margin: 0; background: #000; color: #fff; font-family: sans-serif; display: flex; height: 100vh; overflow: hidden; }
        #sidebar { width: 300px; background: #141414; border-right: 1px solid #333; overflow-y: auto; }
        .canal { padding: 15px; cursor: pointer; border-bottom: 1px solid #222; display: flex; align-items: center; }
        .canal:hover { background: #222; }
        .canal img { width: 45px; height: 45px; margin-right: 12px; border-radius: 4px; }
        #main { flex: 1; display: flex; flex-direction: column; }
        video { width: 100%; height: 100%; background: #000; }
        h2 { padding: 20px; font-size: 18px; color: #e50914; margin: 0; }
    </style>
</head>
<body>
    <div id="sidebar">
        <h2>Canales Disponibles</h2>
        <div id="lista"></div>
    </div>
    <div id="main">
        <video id="video" controls autoplay></video>
    </div>
    <script>
        const video = document.getElementById('video');
        let hls = null;

        async function cargar() {
            const res = await fetch('/canales.json');
            const canales = await res.json();
            const lista = document.getElementById('lista');
            canales.forEach(c => {
                const item = document.createElement('div');
                item.className = 'canal';
                item.innerHTML = \`<img src="\${c.logo}"> <span>\${c.nombre}</span>\`;
                item.onclick = () => play(c.stream);
                lista.appendChild(item);
            });
        }

        function play(url) {
            if (hls) { hls.destroy(); }
            if (Hls.isSupported()) {
                hls = new Hls();
                hls.loadSource(url);
                hls.attachMedia(video);
                hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = url;
                video.play();
            }
        }
        cargar();
    </script>
</body>
</html>`);
});

// Puerto
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('Servidor ONLINE en puerto ' + PORT));
