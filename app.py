import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response

app = Flask(__name__)

def extraer_datos_completos():
    url_sitio = "https://radios.com.uy/"
    api_base = "https://api.instant.audio/data/streams/30/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://radios.com.uy/"
    }

    # Cabecera obligatoria de cualquier archivo M3U
    resultado_m3u = "#EXTM3U\r\n"
    
    try:
        # 1. Obtenemos el HTML de la página principal
        print("Obteniendo lista de radios...")
        res = requests.get(url_sitio, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Filtramos los enlaces que contienen los slugs de las radios
        items = soup.select('#radios li a')
        
        # Usamos una sesión para reutilizar la conexión y ganar velocidad
        session = requests.Session()

        for item in items:
            nombre = item.get('title')
            href = item.get('href', '')
            
            # Extraemos el slug (ej: azul, radio-cero)
            slug = href.replace('https://radios.com.uy/', '').replace('#', '')
            
            if not slug or "radio.png" in str(item):
                continue

            # 2. Consultamos la API interna para obtener el stream real (MP3/AAC)
            try:
                api_res = session.get(f"{api_base}{slug}", headers=headers, timeout=5)
                if api_res.status_code == 200:
                    data = api_res.json()
                    streams = data.get("result", {}).get("streams", [])
                    
                    # Buscamos la URL que sea un flujo de audio directo
                    url_audio = None
                    for s in streams:
                        if s.get('mediaType') in ["MP3", "AAC", "MPEG"] and "http" in s.get("url"):
                            url_audio = s.get("url")
                            break
                    
                    if url_audio:
                        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
                        # Añadimos la entrada al formato M3U
                        resultado_m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n'
                        resultado_m3u += f'{url_audio}\r\n'
                        print(f"OK: {nombre}")
            except Exception:
                continue # Si falla una, seguimos con la otra
        
        return resultado_m3u

    except Exception as e:
        return f"# Error general: {str(e)}"

@app.route('/')
def home():
    # El navegador se quedará cargando mientras procesa
    print("Iniciando proceso de extracción para el usuario...")
    m3u_final = extraer_datos_completos()
    
    # Retornamos como texto plano para facilitar el Copiar/Pegar
    return Response(m3u_final, mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
