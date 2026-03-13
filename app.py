import os
import json
import subprocess
import time
from flask import Flask, Response, redirect, request

app = Flask(__name__)

BASE_URL = os.environ.get('MY_APP_URL', 'https://mi-puente-youtube.onrender.com')
CANALES_FILE = 'canales_yt.json'

# ── Cache yt-dlp (2 horas) ───────────────────────────────────────────────────
_yt_cache = {}
YT_CACHE_TTL = 7200

def get_yt_stream(youtube_id):
    ahora = time.time()
    if youtube_id in _yt_cache:
        url_cache, ts = _yt_cache[youtube_id]
        if ahora - ts < YT_CACHE_TTL:
            return url_cache
    try:
        result = subprocess.run(
            ['yt-dlp', '--no-warnings', '--quiet',
             '-f', 'best[ext=mp4]/best', '-g',
             f'https://www.youtube.com/watch?v={youtube_id}'],
            capture_output=True, text=True, timeout=30
        )
        url = result.stdout.strip().split('\n')[0]
        if url and url.startswith('http'):
            _yt_cache[youtube_id] = (url, ahora)
            return url
    except Exception as e:
        print(f'[yt-dlp] Error {youtube_id}: {e}')
    return None

def cargar_canales():
    if not os.path.exists(CANALES_FILE):
        return []
    with open(CANALES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# ── Rutas ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    canales = cargar_canales()
    return (
        f"<h2>📺 Canales Latinos YouTube</h2>"
        f"<p>Canales disponibles: <b>{len(canales)}</b></p>"
        f"<ul>"
        f"<li><a href='/canales.m3u'>/canales.m3u</a> — Lista para VLC/OTT/TiviMate</li>"
        f"<li><a href='/lista'>/lista</a> — Ver todos los canales</li>"
        f"</ul>"
    )

@app.route('/canales.m3u')
def canales_m3u():
    """
    Genera el m3u con todos los canales.
    Canales DAI (dai.google.com) → URL directa.
    Canales YouTube (youtube_id) → /ytlive/<id> que extrae con yt-dlp.
    Filtros opcionales: ?pais=MX ?grupo=Noticias ?buscar=azteca
    """
    pais   = request.args.get('pais',   '').upper()
    grupo  = request.args.get('grupo',  '').lower()
    buscar = request.args.get('buscar', '').lower()

    canales = cargar_canales()

    if pais:
        canales = [c for c in canales if c.get('pais', '').upper() == pais]
    if grupo:
        canales = [c for c in canales if grupo in c.get('grupo', '').lower()]
    if buscar:
        canales = [c for c in canales if buscar in c.get('nombre', '').lower()]

    m3u = "#EXTM3U\r\n"

    for canal in canales:
        nombre     = canal.get('nombre', 'Canal').replace('"', "'")
        logo       = canal.get('logo',   '')
        grupo_     = canal.get('grupo',  'Latino')
        pais_      = canal.get('pais',   '')
        stream     = canal.get('stream', '')
        youtube_id = canal.get('youtube_id', '')

        # Canales YouTube sin DAI → proxy yt-dlp
        if youtube_id:
            stream = f"{BASE_URL}/ytlive/{youtube_id}#.m3u8"

        if not stream:
            continue

        m3u += (
            f'#EXTINF:-1 '
            f'tvg-logo="{logo}" '
            f'tvg-country="{pais_}" '
            f'group-title="{grupo_}", '
            f'{nombre}\r\n'
            f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36\r\n'
            f'{stream}\r\n'
        )

    return Response(m3u, mimetype='application/x-mpegurl')


@app.route('/ytlive/<youtube_id>')
def ytlive(youtube_id):
    """
    Extrae URL del live de YouTube con yt-dlp y redirige.
    Cacheado por 2 horas.
    """
    youtube_id = youtube_id.rstrip('#').strip()
    url = get_yt_stream(youtube_id)
    if not url:
        return f"No se pudo extraer stream para {youtube_id}", 502
    return redirect(url)


@app.route('/lista')
def lista():
    """Lista HTML de todos los canales disponibles."""
    canales = cargar_canales()
    filas = ""
    for c in canales:
        nombre = c.get('nombre', '')
        pais   = c.get('pais', '')
        grupo  = c.get('grupo', '')
        tipo   = 'YouTube (yt-dlp)' if c.get('youtube_id') else 'DAI / Directo'
        filas += f"<tr><td>{nombre}</td><td>{pais}</td><td>{grupo}</td><td>{tipo}</td></tr>"

    return f"""
    <html><head><meta charset='utf-8'>
    <style>body{{font-family:sans-serif;padding:20px}}
    table{{border-collapse:collapse;width:100%}}
    th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
    th{{background:#333;color:white}}</style></head>
    <body>
    <h2>📺 Canales Latinos ({len(canales)})</h2>
    <table><tr><th>Canal</th><th>País</th><th>Grupo</th><th>Tipo</th></tr>
    {filas}
    </table>
    </body></html>
    """


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
