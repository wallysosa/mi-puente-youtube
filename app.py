import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

# URL de tu servidor en Render
BASE_URL = "https://cine-unificado-m3u.onrender.com"

# Formato: (Nombre para mostrar, ID numérico de la API, Slug para el logo)
RADIOS_DATA = [
    ("Carve Deportiva 1010", "7282", "carve-deportiva-1010"),
    ("Alfa FM", "11579", "alfa-montevideo"),
    ("Azul FM", "7275", "azul"),
    ("Radio Cero", "7315", "radio-cero"),
    ("Océano FM", "7303", "oceano-fm"),
    ("Sport 890", "7319", "sport-890"),
    ("Universal 970", "7320", "universal-montevideo"),
    ("Del Sol FM", "7287", "del-sol-montevideo"),
    ("Monte Carlo", "7299", "monte-carlo"),
    ("Radio Carve 850", "7281", "radio-carve"),
    ("Radio Sarandí", "7316", "sarandi"),
    ("Metrópolis FM", "7298", "metropolis-fm"),
    ("El Espectador", "7291", "radio-el-espectador"),
    ("Aspen FM", "7273", "aspen-punta-del-este"),
    ("Del Plata FM", "7286", "del-plata-fm"),
    ("Radio Disney", "7288", "disney"),
    ("Radio Futura", "7293", "futura"),
    ("M24", "7297", "m24-montevideo"),
    ("Radio Oriental", "7304", "oriental"),
    ("Radio Rural", "7313", "rural-montevideo"),
    ("Radio Clarín", "7283", "clarin"),
    ("Emisora del Sur", "7317", "sur"),
    ("Babel FM", "7318", "babel"),
    ("Radio Clásica", "7302", "clasica")
]

@app.route('/')
def home():
    return "SERVIDOR RADIOS UY - LISTA EN /antel.m3u", 200

@app.route('/antel.m3u')
def generar_lista():
    m3u = "#EXTM3U Astra\r\n"
    for nombre, radio_id, slug in RADIOS_DATA:
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        # El link apunta a tu servidor usando el ID
        m3u += f'{BASE_URL}/reproducir/{radio_id}/playlist.m3u8\r\n'
        
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/reproducir/<radio_id>/playlist.m3u8')
def reproducir(radio_id):
    # Consultamos la API directamente por el ID
    api_url = f"https://api.instant.audio/data/streams/30/{radio_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://radios.com.uy/"
    }
    
    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            
            # Buscamos el stream que sea audio real (isContainer=False)
            url_audio = None
            for s in streams:
                if s.get("mediaType") in ["MP3", "AAC", "MPEG"] and s.get("isContainer") is False:
                    url_audio = s.get("url")
                    break
            
            if url_audio:
                # Redirigimos al flujo real
                return redirect(url_audio, code=302)
    except:
        pass
    
    return "Error: No se pudo conectar con el ID " + radio_id, 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
