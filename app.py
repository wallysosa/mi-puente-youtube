from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

# URL base del streaming que confirmaste que funciona
STREAM_BASE = "https://streaming.2000peliculassigloxx.com/yandex/yadisk.html?v="
WEB_HOME = "https://2000peliculassigloxx.com"

@app.route('/')
def home():
    return "<h1>SERVIDOR LISTO</h1><p>Carga esto en PotPlayer (Ctrl+U): <b>/lista.m3u</b></p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    # --- 1. PELÍCULA FIJA (CASABLANCA) ---
    # Esta es la que sabemos que el ID es nFSeFHQcutFp3g
    img_casa = "https://2000peliculassigloxx.com/wp-content/uploads/una-noche-en-casablanca.jpg"
    m3u += f'#EXTINF:-1 tvg-logo="{img_casa}" group-title="Clásicos", Una noche en Casablanca\r\n'
    # Redirigimos al ID manual que conseguiste
    m3u += f'{host}/video/nFSeFHQcutFp3g\r\n'

    # --- 2. ESCÁNER AUTOMÁTICO (LIMPIO) ---
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(WEB_HOME, headers=headers, timeout=10)
        # Buscamos solo bloques que parezcan artículos de películas
        patron = re.findall(r'href="https://2000peliculassigloxx\.com/([^"/]+)/".*?title="(.*?)".*?>', r.text, re.DOTALL)
        
        encontrados = set()
        palabras_prohibidas = ['wp-json', 'decadas', 'biografias', 'aplicacion', 'contacto', 'politica', 'sagas', 'feed', 'comments']

        for slug, titulo_sucio in patron:
            # FILTRO DE BASURA: Si el slug tiene palabras prohibidas, lo saltamos
            if any(x in slug for x in palabras_prohibidas) or slug in encontrados:
                continue
            
            titulo = titulo_sucio.replace("Ver online", "").replace("descargar", "").strip()
            
            # Solo añadimos si el título parece real (más de 2 letras)
            if len(titulo) > 2:
                img = f"https://2000peliculassigloxx.com/wp-content/uploads/{slug}.jpg"
                m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="Novedades", {titulo}\r\n'
                # Para las automáticas, usamos la ruta de búsqueda
                m3u += f'{host}/buscar/{slug}\r\n'
                encontrados.add(slug)

    except:
        pass # Si falla el escaneo, al menos saldrá Casablanca

    return Response(m3u, mimetype='application/x-mpegurl')

# RUTA 1: Para cuando YA TENEMOS el ID (Caso Casablanca)
@app.route('/video/<id_video>')
def directo(id_video):
    # REDIRECCIÓN PURA: No procesamos nada, enviamos a PotPlayer al link que funciona
    return redirect(f"{STREAM_BASE}{id_video}", code=302)

# RUTA 2: Para buscar el ID de las otras películas
@app.route('/buscar/<slug>')
def buscar(slug):
    try:
        # Aquí sí tenemos que entrar a buscar el ID
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(f"https://videos.2000peliculassigloxx.com/{slug}/embed/", headers=headers, timeout=5)
        match = re.search(r'yadisk\.html\?v=([a-zA-Z0-9_-]+)', r.text)
        if match:
            # Si encontramos el ID, lo mandamos a la ruta directa
            return redirect(f"{STREAM_BASE}{match.group(1)}", code=302)
        else:
            return "ID no encontrado", 404
    except:
        return "Error buscando ID", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
