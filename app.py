import os
import requests
from flask import Flask, Response

app = Flask(__name__)

BASE_URL = "https://cine-unificado-m3u.onrender.com"

# Tu lista de IDs
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
    return "SERVIDOR ACTIVO", 200

@app.route('/antel.m3u')
def generar_lista():
    m3u = "#EXTM3U Astra\r\n"
    for slug, radio_id in RADIOS_DATA:
        nombre = slug.replace("-", " ").title()
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        # Esta ruta ahora devolverá el contenido del stream, no una redirección
        m3u += f'{BASE_URL}/reproducir/{radio_id}/playlist.m3u8\r\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/reproducir/<radio_id>/playlist.m3u8')
def reproducir(radio_id):
    # 1. Obtener la URL real desde la API
    api_url = f"https://api.instant.audio/data/streams/30/{radio_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r_api = requests.get(api_url, headers=headers, timeout=5)
        if r_api.status_code == 200:
            data = r_api.json()
            streams = data.get("result", {}).get("streams", [])
            
            # Buscamos la URL del stream MP3 o AAC
            url_audio_real = None
            for s in streams:
                if s.get("mediaType") in ["MP3", "AAC", "MPEG"] and "http" in s.get("url"):
                    url_audio_real = s.get("url")
                    break
            
            if url_audio_real:
                # 2. EN LUGAR DE REDIRECT: Descargamos el contenido del stream y lo devolvemos
                # Esto es lo que hace que salga el texto que tú quieres
                r_stream = requests.get(url_audio_real, headers=headers, stream=True, timeout=5)
                
                # Creamos una respuesta que "emula" ser el archivo original
                def generate():
                    for chunk in r_stream.iter_content(chunk_size=1024):
                        yield chunk
                
                return Response(generate(), mimetype=r_stream.headers.get('Content-Type'))

    except Exception as e:
        return f"# Error: {str(e)}", 500
    
    return "Error: No se pudo conectar", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
