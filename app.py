import os
import requests
from flask import Flask, Response

app = Flask(__name__)

# Esta es nuestra lista de "motores" (los slugs que sacamos del HTML)
RADIOS_URUGUAY = [
    ("Alfa (Montevideo)", "alfa-montevideo"),
    ("Azul FM", "azul"),
    ("Océano FM", "oceano-fm"),
    ("Sport 890", "sport-890"),
    ("Del Sol", "del-sol-montevideo"),
    ("Radio Monte Carlo", "monte-carlo"),
    ("Radiocero", "radio-cero"),
    ("Radio Clarín", "clarin"),
    ("Universal", "universal-montevideo")
    # Puedes seguir agregando los de la lista anterior aquí...
]

def buscar_stream_real(slug):
    """
    Esta función entra al JSON que me pasaste y busca la mejor URL de audio.
    """
    api_url = f"https://api.instant.audio/data/streams/30/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            streams = data.get("result", {}).get("streams", [])
            
            # Buscamos la URL que sea MP3 y que NO sea un HTML
            for s in streams:
                url = s.get("url")
                # Priorizamos HTTPS y MP3 directo
                if url and "http" in url and s.get("mediaType") == "MP3":
                    return url
    except Exception:
        pass
    return None

@app.route('/')
def generar_m3u():
    """
    Ruta principal que genera el archivo para el Bloc de Notas o PotPlayer.
    """
    m3u = "#EXTM3U\r\n"
    
    for nombre, slug in RADIOS_URUGUAY:
        print(f"Procesando: {nombre}...") # Esto se ve en los logs de Render
        stream_directo = buscar_stream_real(slug)
        
        if stream_directo:
            logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
            m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
            m3u += f'{stream_directo}\r\n'
    
    return Response(m3u, mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
