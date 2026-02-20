import os
import requests
from flask import Flask, Response

app = Flask(__name__)

# Aquí pegás directamente los links de la API que quieras procesar
LINKS_API = [
    "https://api.instant.audio/data/streams/30/alfa-montevideo",
    "https://api.instant.audio/data/streams/30/azul",
    "https://api.instant.audio/data/streams/30/oceano-fm",
    "https://api.instant.audio/data/streams/30/radio-cero",
    "https://api.instant.audio/data/streams/30/sport-890",
    "https://api.instant.audio/data/streams/30/universal-montevideo"
]

def procesar_radio(api_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            station = data.get("result", {}).get("station", {})
            streams = data.get("result", {}).get("streams", [])
            
            # Sacamos los datos automáticamente del JSON
            nombre = station.get("title", "Radio Sin Nombre")
            slug = station.get("name", "")
            
            # Buscamos la URL de audio (MP3 preferentemente)
            url_audio = None
            for s in streams:
                if s.get("mediaType") == "MP3" and "http" in s.get("url"):
                    url_audio = s.get("url")
                    break
            
            if url_audio and slug:
                logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
                return f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\n{url_audio}\n'
    except:
        pass
    return ""

@app.route('/')
def home():
    m3u = "#EXTM3U\n"
    for link in LINKS_API:
        m3u += procesar_radio(link)
    
    return Response(m3u, mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
