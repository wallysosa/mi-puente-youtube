import os, json, uuid, requests, gzip, re
from io import BytesIO
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# ✅ CONFIGURACIÓN CRÍTICA
BASE_URL = os.environ.get('MY_APP_URL', "https://mi-puente-youtube.onrender.com").rstrip('/')
VOD_FILE = 'vod.json'

# Headers ultra-reales para evitar bloqueos
PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://pluto.tv/",
    "Origin": "https://pluto.tv",
    "Accept-Language": "en-US,en;q=0.9",
}

def obtener_jwt(region="us"):
    """Genera una sesión nueva cada vez que se solicita un video"""
    device_id = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    url = f"https://boot.pluto.tv/v4/start?appName=web&appVersion=5.9.2&deviceMake=Chrome&deviceModel=web&deviceType=web&countryCode={region.upper()}&deviceId={device_id}"
    try:
        r = requests.get(url, headers=PROXY_HEADERS, timeout=10)
        data = r.json()
        jwt = data.get("sessionToken") or data.get("stitcherParams", {}).get("sessionToken", "")
        return jwt, device_id, sid
    except:
        return "", device_id, sid

def cargar_vod():
    if os.path.exists(VOD_FILE):
        with open(VOD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/')
def home():
    return f"PUENTE PLUTO TV ACTIVO - VOD: {len(cargar_vod())} pelis. Lista: /cine-vlc.m3u", 200

# ── PROXY DE CLAVE DRM (Indispensable para VLC) ──
@app.route('/proxy/key')
def proxy_key():
    url = request.args.get('url')
    jwt = request.args.get('jwt')
    hdrs = {**PROXY_HEADERS}
    if jwt: hdrs["Authorization"] = f"Bearer {jwt}"
    r = requests.get(url, headers=hdrs, timeout=10)
    return Response(r.content, content_type="application/octet-stream")

# ── PROXY DE SEGMENTOS Y SUB-PLAYLISTS ──
@app.route('/proxy/segment')
def proxy_segment():
    url = request.args.get('url')
    jwt = request.args.get('jwt')
    hdrs = {**PROXY_HEADERS}
    if jwt: hdrs["Authorization"] = f"Bearer {jwt}"

    r = requests.get(url, headers=hdrs, stream=True, timeout=20)
    
    # Si es una lista de segmentos, reescribimos las rutas internas
    if "mpegurl" in r.headers.get("Content-Type", "") or ".m3u8" in url:
        texto = r.text
        base_url = url.rsplit("/", 1)[0] + "/"
        lineas = []
        for l in texto.splitlines():
            if l.startswith("#EXT-X-KEY"):
                # Capturamos la clave DRM y la pasamos por nuestro proxy
                uri = re.search(r'URI="([^"]+)"', l).group(1)
                uri_abs = uri if uri.startswith("http") else base_url + uri
                l = l.replace(uri, f"{BASE_URL}/proxy/key?jwt={jwt}&url={uri_abs}")
            elif l and not l.startswith("#"):
                uri_abs = l if l.startswith("http") else base_url + l
                l = f"{BASE_URL}/proxy/segment?jwt={jwt}&url={uri_abs}"
            lineas.append(l)
        return Response("\n".join(lineas), content_type="application/vnd.apple.mpegurl")

    # Si es un pedazo de video (.ts), lo mandamos directo
    return Response(stream_with_context(r.iter_content(chunk_size=128*1024)), content_type=r.headers.get("Content-Type"))

# ── ENDPOINT PARA VLC (El que pones en la lista) ──
@app.route('/play/<episode_id>')
def play_vlc(episode_id):
    jwt, dev_id, sid = obtener_jwt("us")
    master_url = f"https://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/v2/stitch/hls/episode/{episode_id}/master.m3u8?appName=web&deviceType=web&deviceId={dev_id}&sid={sid}&jwt={jwt}"
    
    r = requests.get(master_url, headers=PROXY_HEADERS, timeout=15)
    if r.status_code != 200: return "Error Pluto", 502

    # Buscamos la mejor calidad
    lineas = r.text.splitlines()
    mejor_url = ""
    for i in range(len(lineas)):
        if "#EXT-X-STREAM-INF" in lineas[i]:
            mejor_url = lineas[i+1] # La línea siguiente tiene la URL
    
    if not mejor_url.startswith("http"):
        base = master_url.rsplit("/", 1)[0] + "/"
        mejor_url = base + mejor_url

    # Mandamos al proxy de segmentos con el JWT fresco
    return Response(f"#EXTM3U\n{BASE_URL}/proxy/segment?jwt={jwt}&url={mejor_url}", content_type="application/vnd.apple.mpegurl")

# ── GENERADOR DE LISTA M3U ──
@app.route('/cine-vlc.m3u')
def generar_lista():
    vod = cargar_vod()[:300]
    m3u = "#EXTM3U\n"
    for item in vod:
        eid = item.get('id', '').strip()
        m3u += f'#EXTINF:-1 tvg-logo="{item.get("poster")}" group-title="{item.get("genero")}", {item.get("nombre")}\n'
        m3u += f'{BASE_URL}/play/{eid}\n'
    return Response(m3u, content_type="text/plain")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
