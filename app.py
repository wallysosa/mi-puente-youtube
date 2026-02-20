import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

BASE_URL = "https://cine-unificado-m3u.onrender.com"

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

@app.route('/antel.m3u')
def generar_lista():
    m3u = "#EXTM3U\r\n"
    for slug in SLUGS:
        nombre = slug.replace("-", " ").title()
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        # Importante: PotPlayer prefiere ver una extensión al final aunque sea falsa
        m3u += f'{BASE_URL}/radio/{slug}/stream.mp3\r\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/radio/<slug>/stream.mp3')
@app.route('/radio/<slug>')
def redireccionar_a_streaming(slug):
    api_url = f"https://api.instant.audio/data/streams/30/{slug}"
    # Headers para engañar a la API y que crea que somos un navegador
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            
            # 1. Intentamos buscar MP3 directo
            url_audio = next((s['url'] for s in streams if s.get('mediaType') == "MP3" and "http" in s.get("url")), None)
            
            # 2. Si no hay MP3, buscamos AAC o cualquier flujo de audio
            if not url_audio:
                url_audio = next((s['url'] for s in streams if s.get('mediaType') in ["AAC", "MPEG"] and "http" in s.get("url")), None)

            if url_audio:
                # Algunas radios requieren que la URL no termine en redirect simple
                # Redirigimos con un código 301 (Permanente) o 302
                return redirect(url_audio, code=302)
                
    except Exception as e:
        print(f"Error en {slug}: {e}")
    
    return f"Error: No se pudo encontrar el flujo para {slug}", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
