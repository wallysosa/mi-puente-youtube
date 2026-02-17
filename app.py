from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

# CONFIGURACIÓN
WEB_HOME = "https://2000peliculassigloxx.com"
STREAM_BASE = "https://streaming.2000peliculassigloxx.com/yandex/yadisk.html?v="

@app.route('/')
def home():
    return "<h1>SERVIDOR ACTIVO</h1><p>Usa este link en PotPlayer: /lista.m3u</p>", 200

@app.route('/lista.m3u')
def generar_lista():
    host = request.host_url.rstrip('/')
    m3u = "#EXTM3U\r\n"
    
    # Cabeceras para parecer un navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Descargamos la web principal
        r = requests.get(WEB_HOME, headers=headers, timeout=15)
        
        # Buscamos películas (bloques 'article')
        patron = re.findall(r'href="https://2000peliculassigloxx\.com/([^"/]+)/".*?title="(.*?)".*?>', r.text, re.DOTALL)
        
        encontrados = set()
        
        # Añadimos manualmente la de prueba que sabemos que funciona
        if "una-noche-en-casablanca" not in encontrados:
            m3u += f'#EXTINF:-1 group-title="Cine Siglo XX", Una noche en Casablanca (Prueba)\r\n'
            # Usamos el ID directo que encontraste: nFSeFHQcutFp3g
            m3u += f'{host}/video/nFSeFHQcutFp3g\r\n'
            encontrados.add("una-noche-en-casablanca")

        # Añadimos el resto de la web automáticamente
        for slug, titulo_sucio in patron:
            if slug in encontrados or slug in ['contacto', 'politica-de-privacidad']:
                continue
            
            titulo = titulo_sucio.replace("Ver online", "").replace("descargar", "").strip()
            # Imagen
            img = f"https://2000peliculassigloxx.com/wp-content/uploads/{slug}.jpg"
            
            m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="Cine Siglo XX", {titulo}\r\n'
            # Aquí usamos el slug para buscar el video después
            m3u += f'{host}/buscar/{slug}\r\n'
            encontrados.add(slug)

    except Exception as e:
        m3u += f"# Error generando lista: {str(e)}\n"

    return Response(m3u, mimetype='application/x-mpegurl')

# RUTA 1: Cuando ya tenemos el ID del video (El caso de Casablanca)
@app.route('/video/<id_video>')
def video_directo(id_video):
    target = f"{STREAM_BASE}{id_video}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://videos.2000peliculassigloxx.com/'
    }
    try:
        r = requests.get(target, headers=headers, timeout=10)
        # Buscamos el MP4 dentro de Yandex
        mp4 = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', r.text)
        if mp4:
            return redirect(mp4.group(1), code=302)
        
        # Si falla, enviamos a PotPlayer a la web del video (Plan B)
        return redirect(target, code=302)
    except:
        return redirect(target, code=302)

# RUTA 2: Cuando solo tenemos el nombre (slug) y hay que buscar el ID
@app.route('/buscar/<slug>')
def buscar_video(slug):
    try:
        # Entramos a buscar el ID
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(f"https://videos.2000peliculassigloxx.com/{slug}/embed/", headers=headers, timeout=10)
        
        match = re.search(r'yadisk\.html\?v=([a-zA-Z0-9_-]+)', r.text)
        if match:
            # Si encontramos el ID, lo mandamos a la ruta de video
            return video_directo(match.group(1))
        else:
            return "Video no encontrado", 404
    except:
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
