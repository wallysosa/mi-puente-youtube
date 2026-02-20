import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

# URL de tu servidor en Render
BASE_URL = "https://cine-unificado-m3u.onrender.com"

# LISTA MAESTRA VERIFICADA (43 RADIOS)
# (Nombre, ID de API, Slug para logo/búsqueda)
RADIOS_DATA = [
    ("Alfa (Montevideo)", "11579", "alfa-montevideo"),
    ("Aspen (Punta del Este)", "7273", "aspen-punta-del-este"),
    ("Azul FM", "7275", "azul"),
    ("Radio Carve 850", "7281", "radio-carve"),
    ("Carve Deportiva 1010", "7282", "carve-deportiva-1010"),
    ("Conquistador (Treinta y Tres)", "11586", "conquistador-treinta-y-tres"),
    ("Del Plata FM", "7286", "del-plata-fm"),
    ("Del Sol", "7287", "del-sol-montevideo"),
    ("Dias de Gloria", "11587", "dias-de-gloria"),
    ("El Espectador", "7291", "radio-el-espectador"),
    ("Emisora del Sur", "7317", "sur"),
    ("FM HIT 90.3", "7292", "fm-hit-90-3"),
    ("FM Inolvidable", "7294", "inolvidable-montevideo"),
    ("La 30 Radio Nacional", "7295", "la-30-montevideo"),
    ("La Voz de Melo", "7296", "voz-de-melo"),
    ("LaCosta FM", "7321", "lacosta-fm"),
    ("M24 (Montevideo)", "7297", "m24-montevideo"),
    ("Metrópolis", "7298", "metropolis-fm"),
    ("Océano FM", "7303", "oceano-fm"),
    ("Radio Aire", "11588", "aire"),
    ("Radio Arapey", "7272", "arapey"),
    ("Radio Babel", "7318", "babel"),
    ("Radio Centenario", "7284", "centenario-montevideo"),
    ("Radio City (Durazno)", "11578", "city"),
    ("Radio Clarín AM", "7283", "clarin"),
    ("Radio Clásica", "7302", "clasica"),
    ("Radio Colonia", "7285", "colonia"),
    ("Radio Disney", "7288", "disney"),
    ("Radio Durazno", "7289", "durazno-montevideo"),
    ("Radio Futura", "7293", "futura"),
    ("Radio María (Florida)", "11580", "radio-maria-uruguay"),
    ("Radio Monte Carlo", "7299", "monte-carlo"),
    ("Radio Oriental", "7304", "oriental"),
    ("Radio Rural", "7313", "rural-montevideo"),
    ("Radio Tacuarembó", "12560", "1280-am-tacuarembo"),
    ("Radio Universal", "7320", "universal-montevideo"),
    ("Radio Zorrilla de San Martín", "11759", "zorrilla-de-san-martin"),
    ("Radiocero", "7315", "radio-cero"),
    ("Reflejos FM", "1457", "reflejos"),
    ("Sarandi", "7316", "sarandi"),
    ("Sport 890", "7319", "sport-890"),
    ("Sur FM (Trinidad)", "11584", "sur-fm"),
    ("Éxito FM (Paysandú)", "11583", "exito-paysandu")
]

@app.route('/')
def home():
    return "SISTEMA DE RADIOS URUGUAY - OK", 200

@app.route('/antel.m3u')
def generar_m3u():
    m3u = "#EXTM3U Astra\r\n"
    for nombre, rid, slug in RADIOS_DATA:
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        # Usamos el slug en la URL para mayor claridad
        m3u += f'{BASE_URL}/reproducir/{slug}/stream.mp3\r\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/reproducir/<slug>/stream.mp3')
def resolver_stream(slug):
    # Buscamos el ID correspondiente al slug en nuestra lista
    radio_id = next((rid for nom, rid, slg in RADIOS_DATA if slg == slug), slug)
    
    api_url = f"https://api.instant.audio/data/streams/30/{radio_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://radios.com.uy/"
    }
    
    try:
        r = requests.get(api_url, headers=headers, timeout=6)
        # Si el ID falla, intentamos con el slug directamente en la API
        if r.status_code != 200:
            r = requests.get(f"https://api.instant.audio/data/streams/30/{slug}", headers=headers, timeout=6)
            
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            
            best_url = None
            max_score = -1
            
            for s in streams:
                score = 0
                m_type = str(s.get("mediaType", "")).upper()
                is_container = s.get("isContainer", True)
                url = s.get("url", "")

                if "http" not in url or m_type == "HTML": continue
                
                # Algoritmo de decisión:
                if not is_container: score += 100
                if m_type in ["MP3", "AAC"]: score += 50
                if "stream" in url.lower(): score += 20
                if url.startswith("https"): score += 10
                
                if score > max_score:
                    max_score = score
                    best_url = url
            
            if best_url:
                return redirect(best_url, code=302)
    except:
        pass

    return "Error: No se pudo obtener el audio", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
