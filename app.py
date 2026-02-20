import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

# URL base de tu despliegue
BASE_URL = "https://cine-unificado-m3u.onrender.com"

# LISTA MAESTRA EXPANDIDA (43 RADIOS)
# Estructura: (Nombre, ID, Slug_Logo)
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
    ("Metrópolis FM", "7298", "metropolis-fm"),
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
    ("Radio Zorrilla de San Martín", "11582", "zorrilla-de-san-martin"),
    ("Radiocero", "7315", "radio-cero"),
    ("Reflejos FM", "11585", "reflejos"),
    ("Sarandi", "7316", "sarandi"),
    ("Sport 890", "7319", "sport-890"),
    ("Sur FM (Trinidad)", "11584", "sur-fm"),
    ("Éxito FM (Paysandú)", "11583", "exito-paysandu")
]

@app.route('/')
def home():
    return f"SISTEMA DE REDIRECCIÓN PRO - <a href='/antel.m3u'>DESCARGAR LISTA</a>", 200

@app.route('/antel.m3u')
def generar_m3u():
    m3u = "#EXTM3U Astra\r\n"
    for nombre, rid, slug in RADIOS_DATA:
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        # Añadimos un parámetro de caché para que el reproductor no use links viejos
        m3u += f'{BASE_URL}/reproducir/{rid}/playlist.m3u8\r\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/reproducir/<radio_id>/playlist.m3u8')
def resolver_y_redirigir(radio_id):
    # Headers de nivel "Best Programmer": Imita un navegador real al 100%
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://radios.com.uy/"
    }
    
    # 1. Caso especial: Carve 850 (7281) suele fallar en la API, forzamos link manual si es necesario
    if radio_id == "7281":
        return redirect("https://icecast3.innovanexo.com:9000/radiocarve850.mp3", code=302)

    api_url = f"https://api.instant.audio/data/streams/30/{radio_id}"
    
    try:
        r = requests.get(api_url, headers=headers, timeout=7)
        if r.status_code == 200:
            data = r.json()
            streams = data.get("result", {}).get("streams", [])
            
            # FILTRADO INTELIGENTE: Prioriza flujos directos sobre contenedores
            url_audio = None
            
            # Paso 1: Buscar MP3/AAC puro
            for s in streams:
                if s.get("mediaType") in ["MP3", "AAC"] and not s.get("isContainer"):
                    url_audio = s.get("url")
                    break
            
            # Paso 2: Si no hay, buscar cualquier URL que contenga un puerto (típico de radios)
            if not url_audio:
                for s in streams:
                    if "http" in s.get("url") and ":" in s.get("url", "")[7:]:
                        url_audio = s.get("url")
                        break

            if url_audio:
                # 302 Redirect: El estándar de oro para streaming
                return redirect(url_audio, code=302)
                
    except Exception as e:
        print(f"Error crítico en ID {radio_id}: {e}")

    return f"Error: No se pudo conectar con la fuente de audio {radio_id}", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
