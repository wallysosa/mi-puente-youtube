const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

// ── CONFIGURACIÓN DE URL ─────────────────────────────────────────────────────
const BASE_URL = process.env.RENDER_EXTERNAL_URL || 'https://mi-puente-youtube.onrender.com';

// ── LISTA DE CANALES ─────────────────────────────────────────────────────────
// Puedes añadir más canales siguiendo el formato: dai (Google) o ytId (YouTube)
const CANALES = [
  { nombre: 'TN - Todo Noticias', pais: 'AR', grupo: 'Argentina', logo: 'https://graph.facebook.com/todonoticias/picture?width=200&height=200', dai: '5OEEtA9FR-yrvhNE5K8PQQ' },
  { nombre: 'C5N',                pais: 'AR', grupo: 'Argentina', logo: 'https://upload.wikimedia.org/wikipedia/commons/6/6b/C5N_logo.svg', ytId: 'c5n' },
  { nombre: 'Azteca 7',           pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/aztecasiete/picture?width=200&height=200',   dai: 'YHoOj51dSKCvBQOBG2OvLQ' },
  { nombre: 'a mas',              pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/amastv/picture?width=200&height=200',        dai: 'SJysMl45QMSwjo0TodSk1Q' },
  { nombre: 'DW Espanol',         pais: 'DE', grupo: 'Internacional', logo: 'https://graph.facebook.com/dw.espanol/picture?width=200&height=200', stream: 'https://dwamdstream104.akamaized.net/hls/live/2015530/dwstream104/stream04/streamPlaylist.m3u8' },
  { nombre: 'NHK World',          pais: 'JP', grupo: 'Internacional', logo: 'https://graph.facebook.com/NHKWorldTV/picture?width=200&height=200', stream: 'https://nhkwlive-ojp.akamaized.net/hls/live/2003459/nhkwlive-ojp-en/index_1M.m3u8' }
];

// ── HELPERS ──────────────────────────────────────────────────────────────────
function getStreamUrl(canal) {
  if (canal.dai) return `${BASE_URL}/dai/${canal.dai}.m3u8`;
  if (canal.ytId) return `${BASE_URL}/youtube/${canal.ytId}`;
  return canal.stream;
}

// ── RUTAS ────────────────────────────────────────────────────────────────────

// Ping para Cron-Job (Mantiene el servidor despierto)
app.get('/ping', (req, res) => res.send('OK'));

// Redirección para YouTube Live (Extractor externo eficiente)
app.get('/youtube/:user', (req, res) => {
  const user = req.params.user;
  // Usamos un motor de redirección HLS para no consumir recursos en Render
  res.redirect(`https://yt-hls.vercel.app/api/hls/${user}.m3u8`);
});

// Proxy DAI (Google) — Renueva la sesión automáticamente
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
      },
      error: (err, req, res) => {
        res.status(502).send('Error de conexión con Google DAI');
      }
    }
  })(req, res, next);
});

// Generador de Lista M3U para VLC/Apps
app.get('/canales.m3u', (req, res) => {
  let m3u = '#EXTM3U\n';
  CANALES.forEach(c => {
    const url = getStreamUrl(c);
    m3u += `#EXTINF:-1 tvg-logo="${c.logo}" tvg-country="${c.pais}" group-title="${c.grupo}", ${c.nombre}\n`;
    m3u += `#EXTVLCOPT:http-user-agent=${UA}\n${url}\n`;
  });
  res.setHeader('Content-Type', 'application/x-mpegurl');
  res.send(m3u);
});

// JSON para el Reproductor Web
app.get('/canales.json', (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json(CANALES.map(c => ({ ...c, stream: getStreamUrl(c) })));
});

// Interfaz de Usuario (Home)
app.get('/', (req, res) => {
  res.send(`
    <body style="background:#000; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
      <h1 style="color:#e50914;">📺 Puente IPTV Activo</h1>
      <p>Servidor funcionando 24/7</p>
      <div style="margin-top:30px;">
        <a href="/player" style="background:#e50914; color:white; padding:15px 25px; text-decoration:none; border-radius:5px; font-weight:bold;">ABRIR REPRODUCTOR</a>
        <br><br><br>
        <code style="background:#222; padding:10px; border-radius:5px;">${BASE_URL}/canales.m3u</code>
      </div>
    </body>
  `);
});

// Reproductor Web Integrado
app.get('/player', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><title>Reproductor IPTV</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/hls.js/1.4.10/hls.min.js"></script>
        <style>
            body { margin: 0; background: #000; color: #fff; font-family: sans-serif; display: flex; height: 100vh; }
            #sidebar { width: 300px; background: #111; border-right: 1px solid #333; overflow-y: auto; }
            .canal { padding: 15px; cursor: pointer; border-bottom: 1px solid #222; display: flex; align-items: center; transition: 0.3s; }
            .canal:hover { background: #e50914; }
            .canal img { width: 40px; height: 40px; margin-right: 15px; border-radius: 5px; }
            video { flex: 1; background: #000; }
        </style>
    </head>
    <body>
        <div id="sidebar"> <h2 style="padding:20px;">Canales</h2> <div id="lista"></div> </div>
        <video id="video" controls autoplay></video>
        <script>
            const video = document.getElementById('video');
            let hls = null;
            async function init() {
                const r = await fetch('/canales.json');
                const canales = await r.json();
                const div = document.getElementById('lista');
                canales.forEach(c => {
                    const el = document.createElement('div');
                    el.className = 'canal';
                    el.innerHTML = '<img src="'+c.logo+'"> <b>'+c.nombre+'</b>';
                    el.onclick = () => {
                        if (hls) hls.destroy();
                        if (Hls.isSupported()) {
                            hls = new Hls(); hls.loadSource(c.stream); hls.attachMedia(video);
                        } else { video.src = c.stream; }
                    };
                    div.appendChild(el);
                });
            }
            init();
        </script>
    </body>
    </html>
  `);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('🚀 ONLINE en puerto ' + PORT));
