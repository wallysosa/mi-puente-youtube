from flask import Flask, redirect, Response, request
import requests
import re
import os

app = Flask(__name__)

# Configuración de URLs
BASE_URL = "https://2000peliculassigloxx.com"
VIDEO_SERVER = "https://videos.2000peliculassigloxx.com"
STREAM_SERVER = "https://streaming.2000peliculassigloxx.com/yandex/yadisk.html?v="

@app.route('/')
def index():
    return "Servidor Siglo XX Funcionando. Lista en /lista.m3u", 200

@app.route('/lista.m3u')
def m3u_gen():
    host = request.host_url.rstrip('/')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    m3u = "#EXTM3U\n"
    
    try:
        # 1. Obtenemos la web principal
        r = requests.get(BASE_URL, headers=headers, timeout=10)
        # 2. Buscamos solo los bloques de artículos para evitar el código JS
        # Buscamos: href="URL" ... title="TITULO"
        movies = re.findall(r'<article.*?\s+href="https://2000peliculassigloxx\.com/([^"/]+)/".*?title="(.*?)".*?>', r.text, re.DOTALL)
        
        added = set()
        for slug, title in movies:
            if slug in added or "PolÃ­tica" in title or "Contacto" in title:
                continue
            
            # Limpiamos el título de caracteres extraños
            clean_title = title.replace("Ver online", "").replace("descargar", "").strip()
            # Imagen por defecto (puedes ajustarla)
            img = f"{BASE_URL}/wp-content/uploads/{slug}.jpg"
            
            m3u += f'#EXTINF:-1 tvg-logo="{img}" group-title="Cine Siglo XX", {clean_title}\n'
            m3u += f'{host}/video/{slug}\n'
            added.add(slug)
            
    except Exception as e:
        m3u += f"# Error: {str(e)}\n"
        
    return Response(m3u, mimetype='application/x-mpegurl')

@app.route('/video/<slug>')
def get_stream(slug):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': f"{VIDEO_SERVER}/{slug}/"
    }
    
    try:
        # Entramos a la página de video para buscar el ID de Yandex
        r = requests.get(f"{VIDEO_SERVER}/{slug}/embed/", headers=headers, timeout=10)
        
        # Buscamos el ID que está después de yadisk.html?v=
        id_match = re.search(r'yadisk\.html\?v=([a-zA-Z0-9_-]+)', r.text)
        
        if id_match:
            video_id = id_match.group(1)
            # Redirigimos al link directo que descubrimos que funciona
            return redirect(f"{STREAM_SERVER}{video_id}", code=302)
        
        # Si no hay Yandex, intentamos buscar cualquier MP4 directo
        mp4_match = re.search(r'source src="(.*?\.mp4)"', r.text)
        if mp4_match:
            return redirect(mp4_match.group(1), code=302)
            
    except:
        pass
        
    return "Video no disponible", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
