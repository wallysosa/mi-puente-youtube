import os
import requests
from flask import Flask, Response

app = Flask(__name__)

# Lista completa extraída de tu HTML
RADIOS_URUGUAY = [
    ("Alfa (Montevideo)", "alfa-montevideo"), ("Aspen (Punta del Este)", "aspen-punta-del-este"),
    ("Azul FM", "azul"), ("Carve (Montevideo)", "radio-carve"),
    ("Carve Deportiva 1010", "carve-deportiva-1010"), ("Conquistador (Treinta y Tres)", "conquistador-treinta-y-tres"),
    ("Del Plata FM", "del-plata-fm"), ("Del Sol", "del-sol-montevideo"),
    ("Dias de Gloria", "dias-de-gloria"), ("El Espectador", "radio-el-espectador"),
    ("Emisora del Sur", "sur"), ("FM HIT 90.3", "fm-hit-90-3"),
    ("FM Inolvidable", "inolvidable-montevideo"), ("La 30 Radio Nacional", "la-30-montevideo"),
    ("La Voz de Melo", "voz-de-melo"), ("LaCosta FM", "lacosta-fm"),
    ("M24 (Montevideo)", "m24-montevideo"), ("Metrópolis", "metropolis-fm"),
    ("Océano FM", "oceano-fm"), ("Radio Aire", "aire"),
    ("Radio Arapey", "arapey"), ("Radio Babel", "babel"),
    ("Radio Centenario", "centenario-montevideo"), ("Radio City (Durazno)", "city"),
    ("Radio Clarín AM", "clarin"), ("Radio Clásica", "clasica"),
    ("Radio Colonia", "colonia"), ("Radio Disney", "disney"),
    ("Radio Durazno", "durazno-montevideo"), ("Radio Futura", "futura"),
    ("Radio María (Florida)", "radio-maria-uruguay"), ("Radio Monte Carlo", "monte-carlo"),
    ("Radio Oriental", "oriental"), ("Radio Rural", "rural-montevideo"),
    ("Radio Tacuarembó", "1280-am-tacuarembo"), ("Radio Universal", "universal-montevideo"),
    ("Radio Zorrilla de San Martín", "zorrilla-de-san-martin"), ("Radiocero", "radio-cero"),
    ("Reflejos FM", "reflejos"), ("Sarandi", "sarandi"),
    ("Sport 890", "sport-890"), ("Sur FM (Trinidad)", "sur-fm"),
    ("Éxito FM (Paysandú)", "exito-paysandu")
]

def obtener_streaming(slug):
    api_url = f"https://api.instant.audio/data/streams/30/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            # Priorizamos MP3/AAC
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
    # Usamos Session para que las peticiones a la API sean más rápidas
    session = requests.Session()
    
    for nombre, slug in RADIOS_URUGUAY:
        url_audio = obtener_streaming(slug)
        if url_audio:
            logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
            m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n{url_audio}\r\n'
    
    return Response(m3u, mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
