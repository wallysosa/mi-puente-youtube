import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

BASE_URL = "https://cine-unificado-m3u.onrender.com"

# Usamos tu formato: (Slug para el logo, ID para la API)
RADIOS_DATA = [
    ("carve-deportiva-1010", "7282"),
    ("alfa-montevideo", "11579"),
    ("azul", "7275"),
    ("radio-cero", "7315"),
    ("oceano-fm", "7303"),
    ("sport-890", "7319"),
    ("universal-montevideo", "7320"),
    ("del-sol-montevideo", "7287"),
    ("monte-carlo", "7299")
]

@app.route('/')
def home():
    return "SERVIDOR ACTIVO - LISTA EN: /antel.m3u", 200

@app.route('/antel.m3u')
def generar_lista():
    m3u = "#EXTM3U Astra\r\n"
    for slug, radio_id in RADIOS_DATA:
        # Ponemos el nombre bonito (Carve Deportiva 1010)
        nombre = slug.replace("-", " ").title()
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        # Enviamos el ID a la ruta de reproducción
        m3u += f'{BASE_URL}/reproducir/{radio_id}\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/reproducir/<radio_id>')
def reproducir(radio_id):
    # La API de instant.audio también permite buscar por ID directamente
    # URL: https://api.instant.audio/data/streams/30/[ID]
    api_url = f"https://api.instant.audio/data/streams/30/{radio_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            
            # Buscamos el stream MP3 real (que no sea HTML)
            url_final = None
            for s in streams:
                if s.get("mediaType") == "MP3" and "http" in s.get("url"):
                    url_final = s.get("url")
                    break
            
            if url_final:
                return redirect(url_final, code=302)
    except:
        pass
    
    return "Error: No se pudo obtener el audio", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
