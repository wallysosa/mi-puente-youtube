// PARCHE PARA VERSIONES MODERNAS DE NODE
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const ytdl = require('@distube/ytdl-core');
const app = express();

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
const BASE_URL = process.env.RENDER_EXTERNAL_URL || 'https://mi-puente-youtube.onrender.com';

// ── LISTA DE CANALES ─────────────────────────────────────────────────────────
const CANALES = [
  { nombre: 'TN - Todo Noticias', pais: 'AR', grupo: 'Argentina', logo: 'https://graph.facebook.com/todonoticias/picture?width=200&height=200', dai: '5OEEtA9FR-yrvhNE5K8PQQ' },
  { nombre: 'C5N',                pais: 'AR', grupo: 'Argentina', logo: 'https://upload.wikimedia.org/wikipedia/commons/6/6b/C5N_logo.svg', ytId: 'c5n' },
  { nombre: 'Azteca 7',           pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/aztecasiete/picture?width=200&height=200',   dai: 'YHoOj51dSKCvBQOBG2OvLQ' },
  { nombre: 'a mas',              pais: 'MX', grupo: 'Mexico',    logo: 'https://graph.facebook.com/amastv/picture?width=200&height=200',        dai: 'SJysMl45QMSwjo0TodSk1Q' },
  { nombre: 'DW Espanol',         pais: 'DE', grupo: 'Internacional', logo: 'https://graph.facebook.com/dw.espanol/picture?width=200&height=200', stream: 'https://dwamdstream104.akamaized.net/hls/live/2015530/dwstream104/stream04/streamPlaylist.m3u8' }
];

// ── HELPERS ──────────────────────────────────────────────────────────────────
function getStreamUrl(canal) {
  if (canal.dai) return `${BASE_URL}/dai/${canal.dai}.m3u8`;
  if (canal.ytId) return `${BASE_URL}/youtube/${canal.ytId}`;
  return canal.stream;
}

// ── RUTAS ────────────────────────────────────────────────────────────────────

app.get('/ping', (req, res) => res.send('OK'));

// Extractor de YouTube (Ajustado para Node 20)
app.get('/youtube/:user', async (req, res) => {
  try {
    const url = `https://www.youtube.com/@${req.params.user}/live`;
    const info = await ytdl.getInfo(url);
    const format = ytdl.chooseFormat(info.formats, { quality: 'highest', filter: 'audioandvideo' });
    
    if (format && format.url) {
        res.redirect(format.url);
    } else {
        res.status(404).send('No se detectó el stream.');
    }
  } catch (error) {
    console.error('Error YouTube:', error.message);
    res.status(500).send('Error en la extracción.');
  }
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

// Lista M3U
app.get('/canales.m3u', (req, res) => {
  let m3u = '#EXTM3U\n';
  CANALES.forEach(c => {
    m3u += `#EXTINF:-1 tvg-logo="${c.logo}" tvg-country="${c.pais}" group-title="${c.grupo}", ${c.nombre}\n`;
    m3u += `#EXTVLCOPT:http-user-agent=${UA}\n${getStreamUrl(c)}\n`;
  });
  res.setHeader('Content-Type', 'application/x-mpegurl');
  res.send(m3u);
});

// JSON para Web Player
app.get('/canales.json', (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json(CANALES.map(c => ({ ...c, stream: getStreamUrl(c) })));
});

// Interfaz Visual
app.get('/', (req, res) => {
  res.send(`<body style="background:#000;color:white;text-align:center;font-family:sans-serif;padding-top:100px;">
    <h1 style="color:#e50914;">📺 Puente IPTV Activo</h1>
    <p>Node.js v20 - Sistema Estable</p>
    <code style="background:#222;padding:15px;display:inline-block;border-radius:8px;margin-top:20px;">${BASE_URL}/canales.m3u</code>
  </body>`);
});

const PORT = process.env.PORT || 10000; // Render prefiere el 10000 o process.env.PORT
app.listen(PORT, () => console.log('🚀 Servidor independiente en puerto ' + PORT));
