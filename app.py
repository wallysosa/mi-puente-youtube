import os
import re
from flask import Flask, Response

app = Flask(__name__)

# Este es el diccionario de radios que extraje del HTML que pasaste
RADIOS_DATA = [
    ("Azul FM (Montevideo)", "azul"),
    ("Océano FM", "oceano-fm"),
    ("El Espectador", "radio-el-espectador"),
    ("Metrópolis", "metropolis-fm"),
    ("Radiocero (Montevideo)", "radio-cero"),
    ("Sport 890", "sport-890"),
    ("Radio Aire", "aire"),
    ("Del Plata (Montevideo)", "del-plata-fm"),
    ("Radio Universal (Montevideo)", "universal-montevideo"),
    ("Del Sol (Montevideo)", "del-sol-montevideo"),
    ("Radio Futura (Montevideo)", "futura"),
    ("Alfa (Montevideo)", "alfa-montevideo"),
    ("Radio Monte Carlo", "monte-carlo"),
    ("Carve (Montevideo)", "radio-carve"),
    ("Carve Deportiva 1010 AM", "carve-deportiva-1010"),
    ("Radio Rural (Montevideo)", "rural-montevideo"),
    ("Sarandi", "sarandi"),
    ("FM HIT 90.3", "fm-hit-90-3"),
    ("Radio Disney (Montevideo)", "disney"),
    ("M24 (Montevideo)", "m24-montevideo"),
    ("La Voz de Melo", "voz-de-melo"),
    ("Aspen (Punta del Este)", "aspen-punta-del-este"),
    ("Radio Oriental", "oriental"),
    ("Radio Colonia (Montevideo)", "colonia"),
    ("Radio Centenario (Montevideo)", "centenario-montevideo"),
    ("La Voz de Artigas", "voz-de-artigas"), # Ejemplo de cómo seguir sumando
]

@app.route('/')
def home():
    return "<h1>Servidor de Radios UY v3.0</h1><p>Lista M3U generada: <b>/radios.m3u</b></p>", 200

@app.route('/radios.m3u')
def generar_lista():
    m3u = "#EXTM3U\r\n"
    
    for nombre, slug in RADIOS_DATA:
        # Lógica de selección de Stream
        if slug == "oceano-fm":
            url = "https://oceano-2.nty.uy/stream"
        elif slug in ["radio-cero", "monte-carlo"]:
            stream_name = slug.replace("-", "")
            url = f"https://icecast2.innovanexo.com:9000/{stream_name}.mp3"
        elif slug == "azul":
            url = "https://vencat-azul.fing.edu.uy/hls/azul.m3u8"
        else:
            # Para el resto, intentamos el formato MP3 directo que suele ser más compatible
            url = f"https://vencat.fing.edu.uy:8000/{slug.replace('radio-', '')}.mp3"

        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n{url}\r\n'
    
    return Response(m3u, mimetype='application/x-mpegurl')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
