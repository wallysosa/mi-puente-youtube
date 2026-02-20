import os
import requests
from flask import Flask, Response

app = Flask(__name__)

def obtener_streaming_real(slug):
    """ Consulta la API de instant.audio para obtener el streaming real """
    try:
        # Paso 1: Obtener el ID de la estación y los streams
        # Usamos el dominio 30 que corresponde a Uruguay en su sistema
        api_url = f"https://api.instant.audio/data/streams/30/{slug}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(api_url, headers=headers, timeout=5)
        data = response.json()
        
        if data.get("success") and data.get("result"):
            streams = data["result"].get("streams", [])
            # Buscamos el stream que sea MP3 o AAC (no el HTML)
            for s in streams:
                if s.get("mediaType") in ["MP3", "AAC", "MPEG"]:
                    return s.get("url")
    except:
        pass
    return None

@app.route('/')
def home():
    return "<h1>Radio Scanner UY Pro</h1><p>Lista M3U real en: <b>/radios.m3u</b></p>", 200

@app.route('/radios.m3u')
def generar_lista():
    # Slugs populares sacados de la web que me pasaste
    slugs = [
        ("Azul FM", "azul"),
        ("Océano FM", "oceano-fm"),
        ("Radio Cero", "radio-cero"),
        ("Sport 890", "sport-890"),
        ("Del Sol", "del-sol-montevideo"),
        ("Metrópolis", "metropolis-fm"),
        ("Radio Universal", "universal-montevideo"),
        ("Radio Monte Carlo", "monte-carlo"),
        ("Radio Carve", "radio-carve")
    ]

    m3u = "#EXTM3U\r\n"
    
    for nombre, slug in slugs:
        url_real = obtener_streaming_real(slug)
        if url_real:
            logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
            m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n{url_real}\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
