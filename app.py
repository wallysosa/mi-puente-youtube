import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

# 1. Corregido: La URL debe ir entre comillas
BASE_URL = "https://cine-unificado-m3u.onrender.com"

# 2. Lista de Slugs (Solo el nombre identificador, el código arma el resto)
SLUGS = [
    "alfa-montevideo", "aspen-punta-del-este", "azul", "radio-carve",
    "carve-deportiva-1010", "conquistador-treinta-y-tres", "del-plata-fm",
    "del-sol-montevideo", "radio-el-espectador", "sur", "fm-hit-90-3",
    "inolvidable-montevideo", "la-30-montevideo", "voz-de-melo",
    "m24-montevideo", "metropolis-fm", "oceano-fm", "aire", "arapey",
    "babel", "centenario-montevideo", "city", "clarin", "clasica",
    "colonia", "disney", "durazno-montevideo", "futura", "radio-maria-uruguay",
    "monte-carlo", "oriental", "rural-montevideo", "1280-am-tacuarembo",
    "universal-montevideo", "zorrilla-de-san-martin", "radio-cero",
    "reflejos", "sarandi", "sport-890", "sur-fm", "exito-paysandu"
]

@app.route('/')
def home():
    return "SERVIDOR ACTIVO - LISTA EN: /antel.m3u", 200

# 3. Unificamos la ruta para que responda en /antel.m3u
@app.route('/antel.m3u')
def generar_lista():
    m3u = "#EXTM3U Astra\r\n"
    
    for slug in SLUGS:
        # Embellecer el nombre (ej: radio-cero -> Radio Cero)
        nombre = slug.replace("-", " ").title()
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        
        # El link apunta a tu servidor, que luego hará la redirección
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        m3u += f'{BASE_URL}/radio/{slug}\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/radio/<slug>')
def redireccionar_a_streaming(slug):
    # El servidor va a la API a buscar el link real cada vez que das Play
    api_url = f"https://api.instant.audio/data/streams/30/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            
            # Buscamos el link de audio real
            url_audio = None
            for s in streams:
                if s.get("mediaType") in ["MP3", "AAC", "MPEG"] and "http" in s.get("url"):
                    url_audio = s.get("url")
                    break
            
            if url_audio:
                # Esto manda a PotPlayer directamente al flujo de música
                return redirect(url_audio, code=302)
    except:
        pass
    
    return "Error: No se pudo encontrar el flujo de audio", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
