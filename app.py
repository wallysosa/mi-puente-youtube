import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response

app = Flask(__name__)

def extraer_logica():
    url_sitio = "https://radios.com.uy/"
    api_base = "https://api.instant.audio/data/streams/30/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://radios.com.uy/"
    }

    m3u = "#EXTM3U\r\n"
    try:
        res = requests.get(url_sitio, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('#radios li a')
        
        session = requests.Session()
        for item in items:
            nombre = item.get('title')
            href = item.get('href', '')
            slug = href.replace('https://radios.com.uy/', '').replace('#', '')
            
            if not slug or "radio.png" in str(item):
                continue

            try:
                # Bajamos el timeout para que no sea tan lento
                api_res = session.get(f"{api_base}{slug}", headers=headers, timeout=3)
                if api_res.status_code == 200:
                    data = api_res.json()
                    streams = data.get("result", {}).get("streams", [])
                    url_audio = next((s['url'] for s in streams if s.get('mediaType') in ["MP3", "AAC", "MPEG"] and "http" in s.get("url")), None)
                    
                    if url_audio:
                        logo = f"https://cdn.instant.audio/images/logos/radios-com-uy/{slug}.png"
                        m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="URUGUAY", {nombre}\r\n{url_audio}\r\n'
            except:
                continue
        return m3u
    except Exception as e:
        return f"# Error: {str(e)}"

@app.route('/')
def home():
    # Página simple para que Render vea que la app funciona al instante
    return "<h1>Extractor de Radios UY</h1><p>Haz clic para generar la lista (tardará unos 30 seg):</p><a href='/generar'>GENERAR M3U</a>", 200

@app.route('/generar')
def generar():
    contenido = extraer_logica()
    return Response(contenido, mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
