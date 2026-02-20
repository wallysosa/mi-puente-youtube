import os
import requests
from flask import Flask, Response

app = Flask(__name__)

# Lista de slugs que sacamos de tu HTML
SLUGS_URUGUAY = [
    ("Azul FM 101.9", "azul"), ("Océano FM 93.9", "oceano-fm"), 
    ("El Espectador 810", "radio-el-espectador"), ("Metrópolis FM", "metropolis-fm"),
    ("Radiocero 104.3", "radio-cero"), ("Sport 890 AM", "sport-890"),
    ("Radio Universal 970", "universal-montevideo"), ("Del Sol 99.5", "del-sol-montevideo"),
    ("Radio Futura", "futura"), ("Radio Monte Carlo", "monte-carlo"),
    ("Radio Carve 850", "radio-carve"), ("Radio Sarandí 690", "sarandi"),
    ("FM HIT 90.3", "fm-hit-90-3"), ("M24 97.9 FM", "m24-montevideo"),
    ("Radio Clarín AM", "clarin"), ("Emisora del Sur", "sur"),
    ("Radio Babel", "babel"), ("La Voz de Melo", "voz-de-melo"),
    ("Radio Tacuarembó", "1280-am-tacuarembo"), ("Radio María", "radio-maria-uruguay")
]

def obtener_stream_api(slug):
    api_url = f"https://api.instant.audio/data/streams/30/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            streams = data.get("result", {}).get("streams", [])
            # Buscamos el primer stream que sea MP3 o similar y tenga una URL HTTP
            for s in streams:
                url = s.get("url")
                if url and "http" in url and s.get("mediaType") != "HTML":
                    return url
    except:
        pass
    return None

@app.route('/')
@app.route('/generar')
@app.route('/radios.m3u')
def home():
    m3u = "#EXTM3U\r\n"
    session = requests.Session()
    
    for nombre, slug in SLUGS_URUGUAY:
        stream_url = obtener_stream_api(slug)
        if stream_url:
            logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
            m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n{stream_url}\r\n'
    
    return Response(m3u, mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
