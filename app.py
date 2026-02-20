import os
import requests
from flask import Flask, Response, redirect

app = Flask(__name__)

BASE_URL = "https://cine-unificado-m3u.onrender.com"

# He corregido los IDs basados en tu JSON (Reflejos es 1457, Zorrilla es 11759)
RADIOS_DATA = [
    ("Reflejos FM 90.7", "1457", "reflejos"),
    ("Radio Zorrilla de San Martín", "11759", "zorrilla-de-san-martin"),
    ("Carve Deportiva 1010", "7282", "carve-deportiva-1010"),
    ("Alfa (Montevideo)", "11579", "alfa-montevideo"),
    ("Aspen (Punta del Este)", "7273", "aspen-punta-del-este"),
    ("Azul FM", "7275", "azul"),
    ("Radio Carve 850", "7281", "radio-carve"),
    ("Del Sol", "7287", "del-sol-montevideo"),
    ("Sport 890", "7319", "sport-890"),
    ("Radio Monte Carlo", "7299", "monte-carlo")
    # ... puedes seguir agregando aquí con el mismo formato
]

@app.route('/')
def home():
    return "SERVIDOR RADIOS PRO ACTIVO", 200

@app.route('/antel.m3u')
def generar_m3u():
    m3u = "#EXTM3U Astra\r\n"
    for nombre, rid, slug in RADIOS_DATA:
        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
        m3u += f'{BASE_URL}/reproducir/{rid}/stream.mp3\r\n'
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/reproducir/<radio_id>/stream.mp3')
def resolver_stream(radio_id):
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
            
            # --- LÓGICA DE PROGRAMADOR SENIOR ---
            url_final = None
            
            # Prioridad 1: Buscar los que NO son contenedores (isContainer: false)
            # y que sean MP3 o AAC.
            for s in streams:
                if s.get("isContainer") is False and s.get("mediaType") in ["MP3", "AAC", "MPEG"]:
                    url_final = s.get("url")
                    break
            
            # Prioridad 2: Si no hay, buscar cualquier cosa que NO sea un contenedor HTML
            if not url_final:
                for s in streams:
                    if s.get("isContainer") is False and s.get("mediaType") != "HTML":
                        url_final = s.get("url")
                        break
            
            # Prioridad 3: Si todo es contenedor, buscar el que tenga "stream" en la URL
            if not url_final:
                for s in streams:
                    if "stream" in s.get("url", "").lower():
                        url_final = s.get("url")
                        break

            if url_final:
                # Si la URL es HTTP y estamos en una app moderna, a veces falla.
                # Pero aquí redirigimos directo al flujo.
                return redirect(url_final, code=302)
                
    except Exception as e:
        print(f"Error en ID {radio_id}: {e}")

    return "No se encontró un flujo de audio válido", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
