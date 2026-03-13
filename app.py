import os
import json
import subprocess
import time
import requests
from flask import Flask, Response, redirect, request

app = Flask(__name__)

BASE_URL    = os.environ.get('MY_APP_URL', 'https://mi-puente-youtube.onrender.com')
CANALES_FILE = 'canales_yt.json'

PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Referer":    "https://www.youtube.com/",
    "Origin":     "https://www.youtube.com",
}

# ── Cache yt-dlp (2 horas) ───────────────────────────────────────────────────
_yt_cache = {}
YT_CACHE_TTL = 7200

def get_yt_stream(youtube_id):
    ahora = time.time()
    if youtube_id in _yt_cache:
        url_cache, ts = _yt_cache[youtube_id]
        if ahora - ts < YT_CACHE_TTL:
            return url_cache
    # Aceptar URL completa o solo el ID
    if youtube_id.startswith('http'):
        yt_url = youtube_id
    else:
        yt_url = f'https://www.youtube.com/watch?v={youtube_id}'
    try:
        result = subprocess.run(
            ['yt-dlp', '--no-warnings', '--quiet',
             '-f', 'best[ext=mp4]/best', '-g', yt_url],
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
        youtube_id   = canal.get('youtube_id', '')
        youtube_live = canal.get('youtube_live', '')
        dai_id       = ''

        # Extraer event ID de URL DAI
        if stream and 'dai.google.com/linear/hls/event/' in stream:
            dai_id = stream.split('/event/')[1].split('/')[0]

        if dai_id:
            # DAI → proxy del servidor para renovar automáticamente
            url = f"{BASE_URL}/dai/{dai_id}#.m3u8"
        elif youtube_live:
            # URL @canal/live → yt-dlp
            yt_enc = requests.utils.quote(youtube_live, safe='')
            url = f"{BASE_URL}/ytlive/{yt_enc}#.m3u8"
        elif youtube_id:
            # YouTube ID → yt-dlp
            url = f"{BASE_URL}/ytlive/{youtube_id}#.m3u8"
        elif stream:
            # URL directa (akamaized, etc.)
            url = stream
        else:
            continue

        m3u += (
            f'#EXTINF:-1 '
            f'tvg-logo="{logo}" '
            f'tvg-country="{pais_}" '
            f'group-title="{grupo_}", '
            f'{nombre}\r\n'
            f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36\r\n'
            f'{url}\r\n'
        )

    return Response(m3u, mimetype='application/x-mpegurl')


@app.route('/dai/<dai_id>')
def dai_proxy(dai_id):
    """
    Proxy para canales DAI de Google.
    Descarga el master.m3u8 y reescribe todas las URLs internas
    para que pasen por el servidor — así VLC nunca recibe URLs que expiran.
    """
    dai_id = dai_id.rstrip('#').strip()
    master_url = f"https://dai.google.com/linear/hls/event/{dai_id}/master.m3u8"

    try:
        r = requests.get(master_url, headers=PROXY_HEADERS, timeout=15, allow_redirects=True)
        r.raise_for_status()
        real_url = r.url  # URL final después de redirecciones
        text     = r.text
    except Exception as e:
        return f"Error obteniendo DAI stream: {e}", 502

    # Base para resolver URLs relativas
    base = real_url.rsplit('/', 1)[0] + '/'

    salida = []
    for linea in text.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith('#'):
            # Sub-playlist → proxy
            abs_url = linea if linea.startswith('http') else base + linea
            linea   = f"{BASE_URL}/dai-segment?url={requests.utils.quote(abs_url, safe='')}"
        salida.append(linea)

    contenido = '\n'.join(salida)
    return Response(contenido, mimetype='application/x-mpegurl',
                    headers={'Access-Control-Allow-Origin': '*'})


@app.route('/dai-segment')
def dai_segment():
    """
    Proxy para sub-playlists y segmentos .ts de canales DAI.
    Renueva automáticamente las URLs cuando expiran.
    """
    url = request.args.get('url', '')
    if not url:
        return "Falta url", 400

    try:
        r = requests.get(url, headers=PROXY_HEADERS, stream=True, timeout=20)
        r.raise_for_status()
    except Exception as e:
        return f"Error segmento DAI: {e}", 502

    content_type = r.headers.get('Content-Type', 'application/octet-stream')

    # Si es m3u8 → reescribir URLs internas también
    if 'mpegurl' in content_type or url.split('?')[0].endswith('.m3u8'):
        text = r.text
        base = url.rsplit('/', 1)[0] + '/'
        salida = []
        for linea in text.splitlines():
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                abs_url = linea if linea.startswith('http') else base + linea
                linea   = f"{BASE_URL}/dai-segment?url={requests.utils.quote(abs_url, safe='')}"
            salida.append(linea)
        return Response('\n'.join(salida), mimetype='application/x-mpegurl',
                        headers={'Access-Control-Allow-Origin': '*'})

    # Si es .ts → streaming directo
    def generar():
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                yield chunk

    return Response(generar(), content_type=content_type,
                    headers={'Access-Control-Allow-Origin': '*'})


@app.route('/ytlive/<youtube_id>')
def ytlive(youtube_id):
    """Extrae URL del live de YouTube con yt-dlp y redirige. Cacheado 2 horas."""
    youtube_id = youtube_id.rstrip('#').strip()
    url = get_yt_stream(youtube_id)
    if not url:
        return f"No se pudo extraer stream para {youtube_id}", 502
    return redirect(url)


@app.route('/lista')
def lista():
    canales = cargar_canales()
    filas = ""
    for c in canales:
        nombre = c.get('nombre', '')
        pais   = c.get('pais', '')
        grupo  = c.get('grupo', '')
        stream = c.get('stream', '')
        if c.get('youtube_id'):
            tipo = 'YouTube (yt-dlp)'
        elif 'dai.google.com' in stream:
            tipo = 'DAI Google (proxy)'
        else:
            tipo = 'Directo'
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
