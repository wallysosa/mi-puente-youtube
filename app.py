import os, json, uuid, requests, re
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)
BASE_URL = os.environ.get('MY_APP_URL', "").rstrip('/')
VOD_FILE = 'vod.json'

PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://pluto.tv/",
    "Origin": "https://pluto.tv"
}

def obtener_jwt():
    dev_id, sid = str(uuid.uuid4()), str(uuid.uuid4())
    url = f"https://boot.pluto.tv/v4/start?appName=web&appVersion=5.9.2&clientID={dev_id}&deviceMake=Chrome&deviceModel=web&deviceType=web&countryCode=US"
    try:
        r = requests.get(url, headers=PROXY_HEADERS, timeout=10)
        return r.json().get("sessionToken", ""), dev_id, sid
    except: return "", dev_id, sid

@app.route('/proxy/segment')
def proxy_segment():
    url = request.args.get('url')
    jwt = request.args.get('jwt')
    if not url: return "No URL", 400
    
    hdrs = {**PROXY_HEADERS}
    if jwt: hdrs["Authorization"] = f"Bearer {jwt}"

    # OPTIMIZACIÓN CRÍTICA: Stream binario directo para segmentos de video
    if ".ts" in url:
        r = requests.get(url, headers=hdrs, stream=True, timeout=20)
        return Response(stream_with_context(r.iter_content(chunk_size=128*1024)), content_type="video/MP2T")

    # Para listas M3U8 (texto)
    r = requests.get(url, headers=hdrs, timeout=15)
    return Response(r.text, content_type="application/vnd.apple.mpegurl")

@app.route('/cine-vlc.m3u')
def lista_vlc():
    if not os.path.exists(VOD_FILE): return "Archivo VOD no encontrado", 404
    with open(VOD_FILE, 'r', encoding='utf-8') as f:
        vod = json.load(f)[:300] # LIMITADO A 300 PARA EVITAR PESO EXCESIVO

    m3u = "#EXTM3U\n"
    for v in vod:
        nombre = v.get('nombre', 'Sin Titulo')
        id_ep = v.get('id', '').strip().rstrip('#')
        m3u += f'#EXTINF:-1 tvg-logo="{v.get("poster","")}" group-title="{v.get("genero","")}", {nombre}\n'
        m3u += f'#EXTVLCOPT:http-user-agent={PROXY_HEADERS["User-Agent"]}\n'
        m3u += f'{BASE_URL}/play/{id_ep}#.m3u8\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/play/<id_ep>')
def play(id_ep):
    jwt, dev_id, sid = obtener_jwt()
    master_url = f"https://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/v2/stitch/hls/episode/{id_ep}/master.m3u8?appName=web&deviceType=web&deviceId={dev_id}&sid={sid}&jwt={jwt}"
    
    r = requests.get(master_url, headers=PROXY_HEADERS)
    # Aquí podrías elegir la mejor calidad. Por ahora redirigimos al proxy:
    return Response(r.text.replace("https://", f"{BASE_URL}/proxy/segment?url=https://"), mimetype='application/x-mpegurl')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
